"""
dashboard.py — Flask web dashboard with Server-Sent Events (SSE).

Runs on http://localhost:7700 by default.

Routes:
  GET /          → HTML dashboard page
  GET /stream    → SSE stream of new grading events
  GET /api/status → JSON: uptime, counts
  GET /api/results → JSON: recent results list

Results are read from ~/.workpulse/results.jsonl.
New results are pushed to connected SSE clients immediately via a thread-safe queue.
"""

from __future__ import annotations

import json
import logging
import os
import queue
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory result store + SSE broadcaster
# ---------------------------------------------------------------------------

class ResultStore:
    """Thread-safe result buffer with SSE broadcast."""

    def __init__(self, results_file: str):
        self._file = Path(results_file)
        self._lock = threading.Lock()
        self._results: List[Dict[str, Any]] = []
        self._subscribers: List[queue.Queue] = []
        self._load_existing()

    def add(self, record: Dict[str, Any]) -> None:
        """Add a new result and broadcast to SSE subscribers."""
        with self._lock:
            self._results.append(record)
            # Keep last 500 in memory
            if len(self._results) > 500:
                self._results = self._results[-500:]
            # Broadcast
            dead = []
            for q in self._subscribers:
                try:
                    q.put_nowait(record)
                except queue.Full:
                    dead.append(q)
            for q in dead:
                self._subscribers.remove(q)

    def subscribe(self) -> queue.Queue:
        """Return a queue that receives new results as they arrive."""
        q: queue.Queue = queue.Queue(maxsize=50)
        with self._lock:
            self._subscribers.append(q)
        return q

    def unsubscribe(self, q: queue.Queue) -> None:
        with self._lock:
            try:
                self._subscribers.remove(q)
            except ValueError:
                pass

    def get_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return most recent results (newest last)."""
        with self._lock:
            return list(self._results[-limit:])

    def _load_existing(self) -> None:
        """Load existing results from JSONL on startup."""
        if not self._file.is_file():
            return
        try:
            with open(self._file) as f:
                lines = f.readlines()
            # Load last 200
            for line in lines[-200:]:
                line = line.strip()
                if not line:
                    continue
                try:
                    self._results.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
            logger.debug("Loaded %d existing results from %s", len(self._results), self._file)
        except OSError as exc:
            logger.warning("Could not load existing results: %s", exc)


# ---------------------------------------------------------------------------
# Flask app factory
# ---------------------------------------------------------------------------

# Global result store singleton (set by create_app)
_result_store: Optional[ResultStore] = None
_start_time: float = time.time()


def get_result_store() -> Optional[ResultStore]:
    return _result_store


def create_app(results_file: str, port: int = 7700) -> Any:
    """Create and configure the Flask application.

    Returns the Flask app object. Does NOT call app.run() — caller does that.
    """
    global _result_store, _start_time
    _start_time = time.time()
    _result_store = ResultStore(results_file)

    try:
        from flask import Flask, Response, jsonify, request, stream_with_context
    except ImportError:
        raise ImportError(
            "Flask is required for the dashboard. "
            "Install it with: pip install flask flask-cors"
        )

    try:
        from flask_cors import CORS  # type: ignore
        _has_cors = True
    except ImportError:
        _has_cors = False

    app = Flask(__name__)
    if _has_cors:
        CORS(app)

    # Suppress Flask's default request logger for SSE noise
    logging.getLogger("werkzeug").setLevel(logging.WARNING)

    # ------------------------------------------------------------------
    # SSE generator
    # ------------------------------------------------------------------

    def _sse_format(data: Dict[str, Any]) -> str:
        """Format a dict as an SSE 'data:' event."""
        return f"data: {json.dumps(data)}\n\n"

    def _event_stream() -> Iterator[str]:
        """Generator that yields SSE events to a connected client."""
        store = get_result_store()
        if store is None:
            return
        q = store.subscribe()
        # Send a heartbeat first so browser knows connection is live
        yield "data: {\"type\": \"connected\"}\n\n"
        try:
            while True:
                try:
                    record = q.get(timeout=15.0)
                    yield _sse_format({"type": "result", "data": record})
                except queue.Empty:
                    # Heartbeat keepalive
                    yield ": keepalive\n\n"
        except GeneratorExit:
            store.unsubscribe(q)

    # ------------------------------------------------------------------
    # Routes
    # ------------------------------------------------------------------

    @app.route("/stream")
    def stream():
        return Response(
            stream_with_context(_event_stream()),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )

    @app.route("/api/status")
    def api_status():
        store = get_result_store()
        results = store.get_recent(500) if store else []
        uptime_secs = int(time.time() - _start_time)
        hours, rem = divmod(uptime_secs, 3600)
        mins, secs = divmod(rem, 60)
        tier_counts = {"above_bar": 0, "near_bar": 0, "below_bar": 0}
        for r in results:
            t = r.get("tier", "")
            if t in tier_counts:
                tier_counts[t] += 1
        return jsonify({
            "status": "running",
            "uptime": f"{hours:02d}:{mins:02d}:{secs:02d}",
            "uptime_seconds": uptime_secs,
            "total_graded": len(results),
            "tier_counts": tier_counts,
            "started_at": datetime.fromtimestamp(_start_time, tz=timezone.utc).isoformat(),
        })

    @app.route("/api/results")
    def api_results():
        store = get_result_store()
        if not store:
            return jsonify([])
        limit = min(int(request.args.get("limit", 50)), 200)
        results = store.get_recent(limit)
        return jsonify(results)

    @app.route("/")
    def index():
        return Response(_html_page(), mimetype="text/html")

    return app


def _html_page() -> str:
    """Return the full HTML dashboard page as a string."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>WorkPulse Monitor</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: #0f1117;
      color: #e2e8f0;
      min-height: 100vh;
    }
    header {
      background: #1a1d27;
      border-bottom: 1px solid #2d3148;
      padding: 16px 24px;
      display: flex;
      align-items: center;
      gap: 16px;
    }
    header h1 { margin: 0; font-size: 1.4rem; font-weight: 700; color: #a78bfa; }
    #status-bar {
      font-size: 0.85rem;
      color: #94a3b8;
      margin-left: auto;
      display: flex;
      gap: 20px;
      align-items: center;
    }
    .dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
    .dot.green { background: #22c55e; box-shadow: 0 0 6px #22c55e; }
    .dot.grey { background: #64748b; }
    main {
      max-width: 1100px;
      margin: 0 auto;
      padding: 24px;
    }
    .stats {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 12px;
      margin-bottom: 28px;
    }
    .stat-card {
      background: #1a1d27;
      border: 1px solid #2d3148;
      border-radius: 10px;
      padding: 16px;
      text-align: center;
    }
    .stat-card .val { font-size: 2rem; font-weight: 700; }
    .stat-card .lbl { font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: .05em; }
    .above { color: #22c55e; }
    .near  { color: #f59e0b; }
    .below { color: #ef4444; }
    h2 { font-size: 1rem; color: #94a3b8; margin: 0 0 14px; }
    #feed { display: flex; flex-direction: column; gap: 14px; }
    .card {
      background: #1a1d27;
      border: 1px solid #2d3148;
      border-radius: 10px;
      padding: 18px 20px;
      animation: slideIn .3s ease;
    }
    @keyframes slideIn {
      from { opacity: 0; transform: translateY(-8px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    .card-header { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
    .badge {
      font-size: 0.7rem;
      font-weight: 700;
      padding: 3px 10px;
      border-radius: 99px;
      text-transform: uppercase;
      letter-spacing: .06em;
    }
    .badge.above_bar { background: #14532d; color: #4ade80; }
    .badge.near_bar  { background: #451a03; color: #fbbf24; }
    .badge.below_bar { background: #450a0a; color: #f87171; }
    .card-ts { font-size: 0.75rem; color: #475569; margin-left: auto; }
    .prompt-text {
      font-size: 0.9rem;
      color: #cbd5e1;
      line-height: 1.6;
      margin-bottom: 8px;
      max-height: 120px;
      overflow: hidden;
      position: relative;
    }
    .reason {
      font-size: 0.8rem;
      color: #64748b;
      border-left: 3px solid #2d3148;
      padding-left: 10px;
      margin-top: 8px;
    }
    .coaching-block {
      margin-top: 10px;
      padding: 10px 12px;
      background: #0f172a;
      border-radius: 6px;
      font-size: 0.82rem;
      color: #93c5fd;
    }
    .coaching-block strong { display: block; margin-bottom: 4px; color: #60a5fa; }
    details summary { cursor: pointer; font-size: 0.8rem; color: #475569; margin-top: 8px; }
    .score-badge {
      font-size: 0.75rem;
      background: #1e2535;
      color: #a78bfa;
      padding: 2px 8px;
      border-radius: 99px;
    }
    #empty { color: #475569; text-align: center; padding: 40px; font-size: 0.9rem; }
  </style>
</head>
<body>
  <header>
    <h1>⚡ WorkPulse Monitor</h1>
    <div id="status-bar">
      <span><span id="conn-dot" class="dot grey"></span> <span id="conn-label">connecting…</span></span>
      <span>Uptime: <strong id="uptime">—</strong></span>
      <span>Graded: <strong id="total">—</strong></span>
    </div>
  </header>
  <main>
    <div class="stats">
      <div class="stat-card">
        <div class="val above" id="cnt-above">—</div>
        <div class="lbl">Above Bar</div>
      </div>
      <div class="stat-card">
        <div class="val near" id="cnt-near">—</div>
        <div class="lbl">Near Bar</div>
      </div>
      <div class="stat-card">
        <div class="val below" id="cnt-below">—</div>
        <div class="lbl">Below Bar</div>
      </div>
      <div class="stat-card">
        <div class="val" id="cnt-total" style="color:#a78bfa">—</div>
        <div class="lbl">Total</div>
      </div>
    </div>
    <h2>Live Feed — above_bar &amp; near_bar</h2>
    <div id="feed"><div id="empty">Waiting for results…</div></div>
  </main>
  <script>
    // ---- Utility ----
    function fmtTs(ts) {
      if (!ts) return '';
      try { return new Date(ts).toLocaleTimeString(); } catch(e) { return ts; }
    }
    function esc(s) {
      const d = document.createElement('div');
      d.textContent = s || '';
      return d.innerHTML;
    }

    // ---- Status polling ----
    async function fetchStatus() {
      try {
        const r = await fetch('/api/status');
        const d = await r.json();
        document.getElementById('uptime').textContent = d.uptime || '—';
        document.getElementById('total').textContent = d.total_graded ?? '—';
        const tc = d.tier_counts || {};
        document.getElementById('cnt-above').textContent = tc.above_bar ?? 0;
        document.getElementById('cnt-near').textContent  = tc.near_bar  ?? 0;
        document.getElementById('cnt-below').textContent = tc.below_bar ?? 0;
        document.getElementById('cnt-total').textContent = d.total_graded ?? 0;
      } catch(e) {}
    }
    setInterval(fetchStatus, 5000);
    fetchStatus();

    // ---- Load existing results ----
    async function loadExisting() {
      try {
        const r = await fetch('/api/results?limit=50');
        const items = await r.json();
        items.forEach(item => {
          if (item.tier === 'above_bar' || item.tier === 'near_bar') addCard(item, true);
        });
      } catch(e) {}
    }
    loadExisting();

    // ---- Card rendering ----
    function addCard(d, prepend) {
      const feed = document.getElementById('feed');
      const empty = document.getElementById('empty');
      if (empty) empty.remove();

      const prompt = d.prompt_preview || (d.window && d.window.turns && d.window.turns.find(t=>t.role==='user')?.text) || '';
      const coaching = d.coaching || '';
      const better = d.better_prompt || '';

      const card = document.createElement('div');
      card.className = 'card';
      card.innerHTML = `
        <div class="card-header">
          <span class="badge ${esc(d.tier)}">${esc(d.tier)}</span>
          <span class="score-badge">score ${esc(String(d.score ?? '?'))}</span>
          <span style="color:#94a3b8;font-size:.85rem">${esc(d.label || '')}</span>
          <span class="card-ts">${fmtTs(d.timestamp)}</span>
        </div>
        <div class="prompt-text">${esc(prompt.slice(0,300))}</div>
        <div class="reason">${esc(d.reason || '')}</div>
        ${coaching ? `<div class="coaching-block"><strong>💡 Coaching</strong>${esc(coaching)}</div>` : ''}
        ${better ? `<details><summary>Better prompt →</summary><div class="coaching-block">${esc(better)}</div></details>` : ''}
      `;

      if (prepend) {
        feed.insertBefore(card, feed.firstChild);
      } else {
        feed.appendChild(card);
      }

      // Keep feed trimmed to 100 cards
      while (feed.children.length > 100) feed.removeChild(feed.lastChild);
    }

    // ---- SSE connection ----
    function connectSSE() {
      const dot = document.getElementById('conn-dot');
      const lbl = document.getElementById('conn-label');
      const es = new EventSource('/stream');

      es.onopen = () => {
        dot.className = 'dot green';
        lbl.textContent = 'live';
      };
      es.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data);
          if (msg.type === 'result') {
            const d = msg.data;
            if (d.tier === 'above_bar' || d.tier === 'near_bar') {
              addCard(d, true);
            }
            fetchStatus();
          }
        } catch(err) {}
      };
      es.onerror = () => {
        dot.className = 'dot grey';
        lbl.textContent = 'reconnecting…';
        es.close();
        setTimeout(connectSSE, 3000);
      };
    }
    connectSSE();
  </script>
</body>
</html>"""


def run_dashboard(
    results_file: str,
    port: int = 7700,
    host: str = "127.0.0.1",
) -> None:
    """Create and run the Flask dashboard (blocking). Use in a background thread."""
    app = create_app(results_file=results_file, port=port)
    app.run(host=host, port=port, threaded=True, use_reloader=False)
