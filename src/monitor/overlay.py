"""
overlay.py — WorkPulse overlay widget.

Provides OverlayState (shared thread-safe state) and OverlayWidget.

OverlayWidget implementation strategy (in priority order):
  1. Tkinter  — always-on-top floating window (preferred, zero deps)
  2. Flask    — minimal /overlay HTML page with pause/resume buttons
               (fallback when tkinter is unavailable)

The overlay should never crash the monitor; all errors are logged and
the monitor continues without the overlay.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Attempt Tkinter import — used by OverlayWidget below
# ---------------------------------------------------------------------------
try:
    import tkinter as tk
    from tkinter import font as tkfont
    _TKINTER_AVAILABLE = True
except ImportError:
    _TKINTER_AVAILABLE = False
    logger.warning(
        "tkinter is not available — overlay will run as a Flask web page "
        "at http://localhost:7701/overlay  (pause/resume work via that page)"
    )


# ---------------------------------------------------------------------------
# OverlayState — thread-safe shared state
# ---------------------------------------------------------------------------

@dataclass
class OverlayState:
    """
    Thread-safe shared state between the monitor threads and the overlay widget.

    Background threads call ``increment_above_bar()`` and ``set_last_graded()``
    directly; the overlay reads the plain attributes for display.
    """

    running: bool = True
    start_time: float = field(default_factory=time.time)
    last_graded: Optional[float] = None
    above_bar_today: int = 0
    paused: bool = False

    # Internal lock — not part of the dataclass repr
    _lock: threading.Lock = field(
        default_factory=threading.Lock, init=False, repr=False, compare=False
    )

    def increment_above_bar(self) -> None:
        """Thread-safe increment of above_bar_today counter."""
        with self._lock:
            self.above_bar_today += 1

    def set_last_graded(self, ts: Optional[float] = None) -> None:
        """Thread-safe update of last_graded timestamp. Defaults to now."""
        with self._lock:
            self.last_graded = ts if ts is not None else time.time()

    def toggle_pause(self) -> bool:
        """Toggle paused state. Returns new paused value."""
        with self._lock:
            self.paused = not self.paused
            self.running = not self.paused
            return self.paused

    # ------------------------------------------------------------------
    # Display helpers (reads; atomicity not critical for display)
    # ------------------------------------------------------------------

    def uptime_str(self) -> str:
        """Human-readable uptime since start_time."""
        elapsed = int(time.time() - self.start_time)
        if elapsed < 60:
            return f"{elapsed} secs"
        if elapsed < 3600:
            return f"{elapsed // 60} mins"
        h = elapsed // 3600
        m = (elapsed % 3600) // 60
        return f"{h}h {m}m"

    def last_graded_str(self) -> str:
        """Human-readable time since last grade."""
        lg = self.last_graded
        if lg is None:
            return "not yet"
        ago = int(time.time() - lg)
        if ago < 60:
            return "just now"
        if ago < 3600:
            return f"{ago // 60} mins ago"
        return f"{ago // 3600}h ago"


# ---------------------------------------------------------------------------
# OverlayWidget — Tkinter implementation
# ---------------------------------------------------------------------------

class _TkOverlayWidget:
    """
    Always-on-top floating Tkinter window.

    Must be created and ``run()`` called from the **main thread**.
    """

    BG = "#1e1e2e"
    FG = "#cdd6f4"
    BTN_BG = "#313244"
    BTN_FG = "#cdd6f4"
    BTN_ACTIVE_BG = "#45475a"
    GREEN = "#a6e3a1"
    YELLOW = "#f9e2af"
    RED = "#f38ba8"

    WIDTH = 260
    HEIGHT = 130

    def __init__(
        self,
        state: OverlayState,
        on_close: Optional[Callable[[], None]] = None,
    ) -> None:
        self._state = state
        self._on_close = on_close

        self._root = tk.Tk()
        self._root.title("WorkPulse")

        # Always-on-top, no taskbar entry
        self._root.wm_attributes("-topmost", True)
        self._root.wm_overrideredirect(True)

        # Size & position (bottom-right corner)
        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        x = sw - self.WIDTH - 20
        y = sh - self.HEIGHT - 60
        self._root.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")
        self._root.configure(bg=self.BG)
        self._root.resizable(False, False)

        # Drag support
        self._drag_x = 0
        self._drag_y = 0

        self._build_ui()
        self._root.bind("<ButtonPress-1>", self._on_drag_start)
        self._root.bind("<B1-Motion>", self._on_drag_motion)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        # Title row
        title_frame = tk.Frame(self._root, bg=self.BG)
        title_frame.pack(fill="x", padx=10, pady=(8, 2))
        tk.Label(
            title_frame, text="\U0001f531 WorkPulse",
            bg=self.BG, fg=self.FG,
            font=("Helvetica", 11, "bold"),
            anchor="w",
        ).pack(side="left")

        # Status row
        self._status_var = tk.StringVar()
        self._status_label = tk.Label(
            self._root,
            textvariable=self._status_var,
            bg=self.BG, fg=self.GREEN,
            font=("Helvetica", 10),
            anchor="w",
        )
        self._status_label.pack(fill="x", padx=10, pady=0)

        # Last graded row
        self._graded_var = tk.StringVar()
        tk.Label(
            self._root,
            textvariable=self._graded_var,
            bg=self.BG, fg=self.FG,
            font=("Helvetica", 9),
            anchor="w",
        ).pack(fill="x", padx=10, pady=0)

        # Above bar row
        self._above_var = tk.StringVar()
        tk.Label(
            self._root,
            textvariable=self._above_var,
            bg=self.BG, fg=self.FG,
            font=("Helvetica", 9),
            anchor="w",
        ).pack(fill="x", padx=10, pady=0)

        # Button row
        btn_frame = tk.Frame(self._root, bg=self.BG)
        btn_frame.pack(fill="x", padx=10, pady=(6, 8))

        self._pause_btn = tk.Button(
            btn_frame,
            text="\u23f8  Pause",
            bg=self.BTN_BG, fg=self.BTN_FG,
            activebackground=self.BTN_ACTIVE_BG,
            activeforeground=self.BTN_FG,
            relief="flat",
            cursor="hand2",
            font=("Helvetica", 9),
            command=self._toggle_pause,
        )
        self._pause_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))

        tk.Button(
            btn_frame,
            text="\u2715",
            bg=self.BTN_BG, fg=self.RED,
            activebackground=self.BTN_ACTIVE_BG,
            activeforeground=self.RED,
            relief="flat",
            cursor="hand2",
            font=("Helvetica", 9),
            width=3,
            command=self._close,
        ).pack(side="right")

        # Initial refresh
        self._refresh()

    # ------------------------------------------------------------------
    # Periodic refresh
    # ------------------------------------------------------------------

    def _refresh(self) -> None:
        s = self._state
        uptime = s.uptime_str()

        if s.paused:
            self._status_var.set(f"\u23f8  Paused   \u2022  {uptime}")
            self._status_label.configure(fg=self.YELLOW)
            self._pause_btn.configure(text="\u25b6  Resume")
        else:
            self._status_var.set(f"\u25cf  Running  \u2022  {uptime}")
            self._status_label.configure(fg=self.GREEN)
            self._pause_btn.configure(text="\u23f8  Pause")

        self._graded_var.set(f"Last graded: {s.last_graded_str()}")
        self._above_var.set(f"Above bar today: {s.above_bar_today}")

        # Schedule next refresh in 5 seconds
        self._root.after(5000, self._refresh)

    # ------------------------------------------------------------------
    # Drag support
    # ------------------------------------------------------------------

    def _on_drag_start(self, event) -> None:
        self._drag_x = event.x
        self._drag_y = event.y

    def _on_drag_motion(self, event) -> None:
        x = self._root.winfo_x() + (event.x - self._drag_x)
        y = self._root.winfo_y() + (event.y - self._drag_y)
        self._root.geometry(f"+{x}+{y}")

    # ------------------------------------------------------------------
    # Controls
    # ------------------------------------------------------------------

    def _toggle_pause(self) -> None:
        self._state.toggle_pause()
        self._refresh()

    def _close(self) -> None:
        if self._on_close:
            try:
                self._on_close()
            except Exception as exc:
                logger.error("on_close callback failed: %s", exc)
        self._root.destroy()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Enter Tkinter main loop (blocks until window is closed)."""
        self._root.mainloop()


# ---------------------------------------------------------------------------
# HTML template for Flask fallback
# ---------------------------------------------------------------------------

_OVERLAY_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>WorkPulse Overlay</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: #1e1e2e;
      color: #cdd6f4;
      font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
    }}
    .widget {{
      background: #181825;
      border: 1px solid #313244;
      border-radius: 12px;
      padding: 16px 20px;
      width: 280px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    }}
    .title {{
      font-size: 14px;
      font-weight: 700;
      margin-bottom: 10px;
      color: #cdd6f4;
    }}
    .status {{
      font-size: 13px;
      font-weight: 600;
      margin-bottom: 4px;
    }}
    .status.running {{ color: #a6e3a1; }}
    .status.paused  {{ color: #f9e2af; }}
    .meta {{
      font-size: 12px;
      color: #a6adc8;
      margin-bottom: 3px;
    }}
    .buttons {{
      display: flex;
      gap: 8px;
      margin-top: 12px;
    }}
    .btn {{
      flex: 1;
      padding: 6px 0;
      border: none;
      border-radius: 6px;
      background: #313244;
      color: #cdd6f4;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.15s;
    }}
    .btn:hover {{ background: #45475a; }}
    .btn-close {{ flex: 0 0 40px; color: #f38ba8; }}
    .dot {{ display: inline-block; width: 8px; height: 8px;
            border-radius: 50%; margin-right: 6px; vertical-align: middle; }}
    .dot.green {{ background: #a6e3a1; }}
    .dot.yellow {{ background: #f9e2af; }}
  </style>
  <meta http-equiv="refresh" content="5">
</head>
<body>
  <div class="widget">
    <div class="title">&#x1F531; WorkPulse</div>
    <div class="status {status_class}">
      <span class="dot {dot_class}"></span>{status_text}&nbsp;&nbsp;&bull;&nbsp;&nbsp;{uptime}
    </div>
    <div class="meta">Last graded: {last_graded}</div>
    <div class="meta">Above bar today: {above_bar}</div>
    <div class="buttons">
      <form method="post" action="/overlay/pause" style="flex:1;display:flex;">
        <button class="btn" type="submit">{pause_label}</button>
      </form>
      <form method="post" action="/overlay/close" style="display:flex;">
        <button class="btn btn-close" type="submit">&#x2715;</button>
      </form>
    </div>
  </div>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# OverlayWidget — Flask fallback implementation
# ---------------------------------------------------------------------------

class _FlaskOverlayWidget:
    """
    Flask-based overlay widget (fallback when Tkinter is unavailable).

    Starts a minimal Flask server on port 7701.
    Visit http://localhost:7701/overlay to see the status widget.
    Pause/resume are handled via POST to /overlay/pause.
    """

    PORT = 7701

    def __init__(
        self,
        state: OverlayState,
        on_close: Optional[Callable[[], None]] = None,
    ) -> None:
        self._state = state
        self._on_close = on_close
        self._server_thread: Optional[threading.Thread] = None

    def _build_app(self):
        try:
            from flask import Flask, redirect, Response
        except ImportError as exc:
            raise RuntimeError("Flask is required for the overlay fallback") from exc

        import logging as _logging
        _logging.getLogger("werkzeug").setLevel(_logging.WARNING)

        app = Flask(__name__)
        state = self._state
        on_close = self._on_close

        @app.route("/overlay")
        def overlay_page():
            paused = state.paused
            html = _OVERLAY_HTML.format(
                status_class="paused" if paused else "running",
                dot_class="yellow" if paused else "green",
                status_text="Paused" if paused else "Running",
                uptime=state.uptime_str(),
                last_graded=state.last_graded_str(),
                above_bar=state.above_bar_today,
                pause_label="&#x25B6;&#xFE0F;  Resume" if paused else "&#x23F8;&#xFE0F;  Pause",
            )
            return Response(html, mimetype="text/html")

        @app.route("/overlay/pause", methods=["POST"])
        def overlay_pause():
            state.toggle_pause()
            return redirect("/overlay")

        @app.route("/overlay/close", methods=["POST"])
        def overlay_close():
            if on_close:
                threading.Thread(target=on_close, daemon=True).start()
            return Response(
                "<html><body style='background:#1e1e2e;color:#cdd6f4;"
                "font-family:sans-serif;text-align:center;padding-top:40px'>"
                "<p>WorkPulse monitor is shutting down\u2026</p></body></html>",
                mimetype="text/html",
            )

        # JSON API endpoints for programmatic / dashboard integration
        @app.route("/overlay/api/state")
        def overlay_api_state():
            from flask import jsonify
            return jsonify({
                "paused": state.paused,
                "running": state.running,
                "uptime": state.uptime_str(),
                "last_graded": state.last_graded_str(),
                "above_bar_today": state.above_bar_today,
            })

        @app.route("/overlay/api/pause", methods=["GET", "POST"])
        def overlay_api_pause():
            from flask import jsonify
            state.toggle_pause()
            return jsonify({"paused": state.paused})

        return app

    def run(self) -> None:
        """
        Start Flask overlay server in a background daemon thread.

        Returns immediately — the monitor's watcher.run_blocking() blocks
        the main thread as usual.
        """
        app = self._build_app()
        logger.info(
            "WorkPulse overlay widget running at http://localhost:%d/overlay  "
            "(Tkinter unavailable \u2014 using Flask fallback)",
            self.PORT,
        )

        def _serve():
            app.run(
                host="127.0.0.1",
                port=self.PORT,
                threaded=True,
                use_reloader=False,
                debug=False,
            )

        self._server_thread = threading.Thread(
            target=_serve,
            daemon=True,
            name="workpulse-overlay",
        )
        self._server_thread.start()


# ---------------------------------------------------------------------------
# Public OverlayWidget — selects the right backend automatically
# ---------------------------------------------------------------------------

class OverlayWidget:
    """
    Public overlay widget facade.

    Automatically selects the best available backend:
    - **Tkinter** (preferred): creates a floating always-on-top window;
      ``run()`` blocks the main thread until the window is closed.
    - **Flask** (fallback): serves a status page at
      http://localhost:7701/overlay; ``run()`` returns immediately
      (starts a background daemon thread).

    Usage::

        state = OverlayState(start_time=time.time())
        widget = OverlayWidget(state, on_close=shutdown_fn)

        if widget.uses_tkinter:
            # Start background threads BEFORE run() — it will block
            worker.start(); watcher_thread.start()
            widget.run()          # blocks; watcher runs in background
        else:
            widget.run()          # non-blocking Flask start
            watcher.run_blocking()  # blocks main thread
    """

    def __init__(
        self,
        state: OverlayState,
        on_close: Optional[Callable[[], None]] = None,
    ) -> None:
        self._state = state
        self._on_close = on_close
        self._backend: Optional[object] = None
        self._uses_tkinter = False

        try:
            if _TKINTER_AVAILABLE:
                self._backend = _TkOverlayWidget(state, on_close)
                self._uses_tkinter = True
            else:
                self._backend = _FlaskOverlayWidget(state, on_close)
        except Exception as exc:
            logger.warning("OverlayWidget init failed (%s) \u2014 overlay disabled.", exc)

    @property
    def uses_tkinter(self) -> bool:
        """True if the Tkinter backend is active (run() will block)."""
        return self._uses_tkinter

    def run(self) -> None:
        """
        Start the overlay.

        - **Tkinter backend**: blocks until the window is closed.
        - **Flask backend**: starts background thread and returns immediately.
        - **No backend**: logs a warning and returns immediately.
        """
        if self._backend is None:
            logger.warning("OverlayWidget has no backend \u2014 skipping overlay.")
            return
        try:
            self._backend.run()
        except Exception as exc:
            logger.warning("OverlayWidget.run() failed: %s", exc)
