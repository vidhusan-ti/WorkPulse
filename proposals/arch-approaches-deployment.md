# WorkPulse — Deployment Approaches

Architecture research for the runtime/deployment layer of WorkPulse.
Generated: 2026-06-29

---

## Overview

WorkPulse monitors Cursor transcript JSONL files, detects new conversation windows, and grades them through a 4-stage pipeline (SND→IOAS→CTA→EJAD) via Anthropic Claude API calls, surfacing results in real time. The core tension is: **file access lives on the user's machine**, while **LLM calls go to the cloud**. Every deployment approach is a different answer to that tension.

---

### Approach 1: Pure Local Python Daemon

**How it works:** A Python script (with `watchdog`) runs as a background process on the user's machine, watches the Cursor transcript folder directly, and makes Anthropic API calls from the local process. Results are surfaced via a local web UI (Flask/FastAPI + browser) or CLI output.

**Pros:**
- Zero latency for file detection — direct filesystem events
- No data ever leaves the machine except to Anthropic API
- Works offline except for grading calls
- Simple mental model: one process, one machine
- Easy to inspect, kill, restart

**Cons:**
- User must have Python installed and manage a background process
- No cross-machine sync (if user switches machines, monitoring stops)
- Process can die silently; needs a supervisor (launchd, systemd, etc.)
- UI is a separate concern (browser tab, terminal, or TUI)

**Complexity:** Low
**Setup friction:** Medium — `pip install workpulse && workpulse start` is achievable, but Python env management, API key config, and autostart are friction points for non-developers.

---

### Approach 2: pip Package with Autostart (launchd / systemd)

**How it works:** A pip-installable package that, on first run, registers itself as a system service (macOS `launchd` plist, Linux `systemd` unit, Windows Task Scheduler) so it survives reboots and runs without manual invocation.

**Pros:**
- One-time setup: `pip install workpulse && workpulse install`
- Behaves like a proper system daemon after install
- Cross-platform with service manager abstraction (e.g., `pystemd`, `launchd` via subprocess)
- Upgradeable via `pip install --upgrade workpulse`

**Cons:**
- Writing launchd/systemd files programmatically is fiddly across OS versions
- Users may distrust a pip package that modifies system services
- Python version conflicts; virtualenv isolation recommended but adds steps
- Uninstall path needs care to avoid orphaned service entries

**Complexity:** Medium
**Setup friction:** Low for the happy path (`pip install` + `workpulse install`), but recovery from errors (wrong Python, permissions, existing service) can be gnarly.

---

### Approach 3: VS Code / Cursor Extension (Extension Host Process)

**How it works:** A Cursor/VS Code extension activates when the editor opens, uses the Node.js `fs.watch` / `chokidar` API inside the extension host process to monitor the transcript folder, and streams grading results into a custom Webview panel within the editor.

**Pros:**
- Zero additional install for Cursor users — native to their workflow
- Results appear directly in the editor (side panel, status bar, notifications)
- Extension Marketplace distribution handles updates automatically
- Access to VS Code APIs (workspace, progress, decorations) for rich UX
- No separate process to manage

**Cons:**
- Extension host process is single-threaded; heavy I/O or slow API calls can lag the editor
- Extensions run sandboxed — some filesystem paths may need explicit permission
- Cursor's extension API is VS Code-compatible but may lag VS Code releases
- Publishing to marketplace requires review + developer account
- Node.js only (no Python-native grading logic without subprocess calls)

**Complexity:** Medium
**Setup friction:** Very low — install from Cursor Extensions panel, configure API key in settings. One of the smoothest possible UX paths.

---

### Approach 4: Electron Desktop App

**How it works:** A standalone cross-platform desktop app (Electron + React/Vue) that bundles the file watcher, grading pipeline client, and UI into a single .dmg/.exe/.AppImage. Runs as a tray icon app, surfaces grading results in a native window.

**Pros:**
- Full desktop integration: tray icon, native notifications, OS-level autostart
- Bundles everything — no Python/Node version concerns for the user
- Rich UI possible with full web tech stack
- Direct filesystem access without sandboxing restrictions
- Distributable as a signed, notarized app (macOS) for trust

**Cons:**
- Large binary size (~150MB+ for Electron baseline)
- Electron has a reputation for memory/CPU overhead
- Build complexity: separate targets for macOS (arm64/x86), Windows, Linux
- Code signing and notarization (especially macOS) requires paid accounts and CI pipeline
- Slower iteration cycle than a script

**Complexity:** High
**Setup friction:** Very low for end users (download, drag to Applications, run), but high build/distribution complexity for developers.

---

### Approach 5: Native macOS App (Swift / SwiftUI)

**How it works:** A SwiftUI menu-bar app uses FSEvents (macOS native file system events API) to monitor the transcript folder with minimal overhead, and makes Anthropic API calls via URLSession. Results appear in a native popover from the menu bar.

**Pros:**
- Extremely lightweight — no runtime overhead, native performance
- FSEvents is the gold standard for macOS file monitoring (used by Spotlight, Time Machine)
- Native SwiftUI UI feels premium and fits macOS aesthetics
- Can be distributed via Mac App Store or direct download
- Proper macOS sandbox and security model

**Cons:**
- macOS only — Linux/Windows users are excluded entirely
- Swift development requires Xcode on macOS; not accessible to Python/JS devs
- App Store sandboxing complicates arbitrary folder access (needs entitlements + user consent)
- Longer release cycle; harder to iterate rapidly

**Complexity:** High
**Setup friction:** Very low for macOS users (download .dmg, run). Development friction is high.

---

### Approach 6: Local + Cloud Hybrid (Local Watcher, Cloud Grader)

**How it works:** A lightweight local agent (minimal Python or Node.js script) watches the transcript folder and forwards new windows via HTTP/WebSocket to a cloud-hosted grading service (e.g., FastAPI on Fly.io, Railway, or Render). The cloud service runs the 4-stage LLM pipeline and pushes results back to the local agent for display.

**Pros:**
- Local agent is tiny and simple — no heavy dependencies
- Grading logic lives in the cloud: easily updated, scaled, monitored without touching the user's machine
- Multiple users can share the same grading service
- Cloud service can log/aggregate grading results for analytics
- Grading rubric updates deploy instantly without user action

**Cons:**
- Requires a running cloud service — adds infrastructure cost
- Network round-trip adds latency to each grading event
- User data (Cursor transcripts) leaves the machine — privacy concern
- Local agent still needs to be installed and run reliably
- Cloud service is a single point of failure

**Complexity:** Medium
**Setup friction:** Medium — local agent install is simple, but cloud service requires deployment and the user must point the agent at the right endpoint.

---

### Approach 7: Full Cloud (Cursor Folder Synced via Cloud Storage)

**How it works:** The user's Cursor transcript folder is synced to cloud storage (iCloud, Dropbox, S3 via rclone, etc.). A cloud worker (Lambda, Cloud Run) triggers on new/modified files, runs the grading pipeline, and pushes results to a web dashboard the user has open in their browser.

**Pros:**
- Zero local install — the user's existing cloud sync does the heavy lifting
- Grading and UI are entirely cloud-side; easy to update
- Results accessible from any device/browser
- Natural audit trail in cloud storage

**Cons:**
- Requires syncing the Cursor folder to a cloud provider — non-trivial setup and significant privacy trade-off
- Cloud sync introduces latency (Dropbox/iCloud can take 5-30s)
- Complex event-driven architecture: storage trigger function push browser
- Cursor transcript files may contain sensitive code and conversations
- Cost scales with file change frequency

**Complexity:** High
**Setup friction:** High — requires cloud sync setup, IAM config, webhook plumbing. Not suitable for quick onboarding.

---

### Approach 8: Docker Container (Local)

**How it works:** A Docker container mounts the user's Cursor transcript folder as a volume and runs the file watcher + grading pipeline inside the container. A web UI served from the container is accessible at localhost:PORT.

**Pros:**
- Perfectly isolated — no Python/Node version conflicts on host
- Single `docker run` command to start
- Easy to update: `docker pull workpulse/workpulse:latest`
- Works on any OS with Docker installed (macOS, Linux, Windows/WSL)
- Reproducible, auditable environment

**Cons:**
- Docker required — not a given for all developers, and definitely not for non-developers
- Volume mounts on macOS have performance overhead (improved with VirtioFS, but not zero)
- Container runs without autostart by default; needs --restart unless-stopped or Docker Desktop settings
- Awkward for tray/notification-style UX — better for headless + browser UI pattern

**Complexity:** Low (to run), Medium (to build and maintain image)
**Setup friction:** Medium — `docker run` is one command, but Docker install + volume path setup is a barrier for less technical users.

---

### Approach 9: npm Package (Node.js CLI / Background Process)

**How it works:** An npm-published package (`npx workpulse` or global `npm install -g workpulse`) runs a Node.js process that uses `chokidar` for cross-platform file watching and makes Anthropic API calls. Results are served via a local Express server + browser UI, or printed to the terminal.

**Pros:**
- Node.js/npm is ubiquitous among developers (very likely already installed for Cursor/VS Code users)
- `npx workpulse` requires zero global install — try it immediately
- Fast iteration on the package; `npm update` for upgrades
- `chokidar` provides robust, battle-tested cross-platform file watching
- Natural stepping stone toward a full Cursor extension

**Cons:**
- Node.js ecosystem: node_modules bloat, security audit noise
- Process management (autostart, crash recovery) needs external tools or a bundled solution
- Less ergonomic than Python-native if grading logic is being developed in Python
- `npx` cold-start downloads the package each time unless globally installed

**Complexity:** Low
**Setup friction:** Low — `npm install -g workpulse && workpulse start` or `npx workpulse`. One of the lowest-friction CLI approaches.

---

### Approach 10: Serverless Functions on File Change Events

**How it works:** The user sets up a cloud sync (S3, R2, etc.) that triggers a serverless function (AWS Lambda, Cloudflare Workers with Durable Objects) on each new/modified JSONL file. The function runs the grading pipeline and stores results in a database, which a web dashboard polls or subscribes to via WebSocket.

**Pros:**
- Scales to zero cost when not in use
- No servers to manage; fully managed compute
- Each grading pipeline run is isolated and automatically retriable
- Natural fit for event-driven, stateless grading jobs

**Cons:**
- Cold start latency for serverless functions (100ms-2s depending on provider/runtime)
- Still requires a local file-sync mechanism to get files into the cloud trigger chain
- Most complex architecture to set up and debug from scratch
- Cloudflare Workers have a 10ms CPU time limit by default — insufficient for multi-step LLM orchestration without Durable Objects
- Distributed event chains are hard to observe and debug

**Complexity:** High
**Setup friction:** High — requires cloud account, S3/R2 bucket, Lambda/Worker config, trigger wiring, and dashboard deployment.

---

### Approach 11: GitHub Actions / CI Pipeline

**How it works:** The user commits (or auto-syncs) their Cursor transcript folder to a private GitHub repo. A GitHub Actions workflow triggers on push, runs the grading pipeline in a CI job, and posts results as a commit comment, PR comment, or publishes to a GitHub Pages dashboard.

**Pros:**
- Zero infrastructure to manage — GitHub handles compute
- Results are versioned alongside transcripts (git history = audit trail)
- Free tier is generous (2,000 minutes/month on free plan)
- Familiar tooling for developers; .github/workflows/ is well-understood

**Cons:**
- Not real-time — requires a git commit/push cycle (minutes of latency minimum)
- Committing Cursor transcripts to GitHub means potentially sensitive conversations are in a remote repo
- Actions not designed for continuous monitoring — per-push triggers create workflow spam if Cursor writes frequently
- Poor UX for real-time feedback; fundamentally async

**Complexity:** Low (to prototype), Medium (to make robust)
**Setup friction:** Medium — requires GitHub repo setup, secrets config, and willingness to commit transcript files. Not suitable for real-time use cases.

---

### Approach 12: Browser-Based PWA (File System Access API)

**How it works:** A Progressive Web App hosted at a URL uses the browser's File System Access API to request permission to watch the Cursor transcript folder directly from the browser. The grading pipeline calls Anthropic's API directly from the browser (client-side). Results display in the PWA UI with zero install.

**Pros:**
- No install at all — open a URL, grant folder access, done
- Cross-platform: works on any OS with Chrome or Edge
- Instant updates: refresh the page to get the latest version
- Can be installed as a PWA for quasi-tray behavior
- No backend infrastructure required (API calls go browser to Anthropic directly)

**Cons:**
- File System Access API is Chrome/Edge only — Firefox and Safari not supported
- Browser background processing is throttled/suspended when tab is hidden
- No true daemon behavior — user must keep the tab open and visible
- Sensitive transcript data and API key are exposed in the browser context
- Must poll for file changes (no inotify-style push events in browser FS API)

**Complexity:** Medium
**Setup friction:** Very low — zero install. Open URL, click "Allow folder access." Reliability as a persistent monitor is limited.

---

### Approach 13: OpenClaw Agent (Already Running)

**How it works:** WorkPulse runs as a capability of the already-deployed OpenClaw agent. The agent uses its existing shell access and exec tool to tail the Cursor transcript folder via inotifywait or a polling loop, pipes new windows into the 4-stage grading pipeline (Anthropic API calls via the agent's existing credential context), and reports results back through the OpenClaw session channel (webchat, Discord, etc.).

**Pros:**
- Zero additional infrastructure — OpenClaw is already running on this machine
- Agent already has filesystem access, shell execution, and API credentials
- Results delivered through any channel OpenClaw serves (webchat, Discord, notifications)
- Leverages existing memory/context: agent can correlate grading results with project history
- Grading logic expressible as a Skill (SKILL.md) — versioned, auditable, shareable
- Agent can self-update grading rubrics by editing its own skill files
- Subagent pattern enables isolated monitoring sessions that don't pollute main context

**Cons:**
- Ties WorkPulse to the OpenClaw deployment — if OpenClaw goes down, monitoring stops
- Continuous monitoring in the main session grows context size (token cost)
- Better suited to periodic/triggered grading than very high-frequency continuous monitoring
- Not portable: users without OpenClaw cannot use this approach

**Complexity:** Low (given OpenClaw is already deployed)
**Setup friction:** Near-zero for existing OpenClaw users — add a SKILL.md, configure transcript path, done. High friction for anyone not already running OpenClaw.

---

## Summary Table

| # | Approach | Complexity | Setup Friction | Real-time? | Cross-platform? | Data stays local? |
|---|----------|------------|----------------|------------|-----------------|-------------------|
| 1 | Pure Local Python Daemon | Low | Medium | Yes | Yes | Yes* |
| 2 | pip Package + Autostart | Medium | Low | Yes | Yes | Yes* |
| 3 | VS Code / Cursor Extension | Medium | Very Low | Yes | Yes | Yes* |
| 4 | Electron Desktop App | High | Very Low (user) | Yes | Yes | Yes* |
| 5 | Native macOS App (SwiftUI) | High | Very Low (user) | Yes | macOS only | Yes* |
| 6 | Local + Cloud Hybrid | Medium | Medium | Yes | Yes | No |
| 7 | Full Cloud (Cloud Sync) | High | High | Delayed | Yes | No |
| 8 | Docker Container (Local) | Low/Medium | Medium | Yes | Yes | Yes* |
| 9 | npm Package / npx | Low | Low | Yes | Yes | Yes* |
| 10 | Serverless on File Events | High | High | Delayed | Yes | No |
| 11 | GitHub Actions / CI | Low/Medium | Medium | No | Yes | No |
| 12 | Browser PWA (FS Access API) | Medium | Very Low | Polling | Chrome/Edge only | Yes* |
| 13 | OpenClaw Agent | Low | Near-zero** | Periodic | Yes** | Yes* |

*Except for Anthropic API calls  
**For existing OpenClaw deployments only

---

## Recommended Starting Points

**For fastest MVP:** Approach 1 (Pure Local Python Daemon) or Approach 9 (npm/npx) — lowest complexity, works immediately.

**For best developer UX:** Approach 3 (Cursor Extension) — results appear in the editor with zero context switching.

**For best end-user UX:** Approach 4 (Electron) or Approach 2 (pip + autostart) — set it and forget it.

**For OpenClaw-native prototyping:** Approach 13 — leverage existing infrastructure, iterate fast, no new deployment needed.
