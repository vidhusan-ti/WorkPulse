# WorkPulse — UI/Presentation Approaches

How to show grading results (SND→IOAS→CTA→EJAD pipeline) to the user in real time.

---

### Approach 1: Native OS Notifications

**How it works:** After each window is graded, fire a native desktop notification (macOS `NSUserNotification` / `osascript`, Windows Toast via `win10toast` or PowerShell, Linux `libnotify`/`notify-send`) with a one-line summary of the grade and the stage that triggered.

**Pros:**
- Zero UI to build — OS does all the rendering
- Works while Cursor is focused or minimized
- Requires no window management or overlay code
- Familiar UX; users already trained on notification banners

**Cons:**
- Very limited real estate — one short title + body line
- No history; dismissed notifications are gone
- macOS notification permissions required (can be blocked)
- Notification fatigue if grading fires frequently (every turn)
- No rich detail — can't show rubric breakdown inline

**Complexity:** Low

**User experience:** A banner slides in from the top-right (macOS) or bottom-right (Windows/Linux) showing e.g. "WorkPulse Turn 14 — EJAD: 8/10 | SND: pass". User can click to open a log file or web dashboard. Disappears after ~5 seconds.

---

### Approach 2: Floating Overlay Window (Always-on-Top)

**How it works:** A small always-on-top frameless window (Electron, Tauri, or PyWebView) floats in a corner of the screen, updating live as each turn is graded. The user can resize/reposition it; it never steals focus.

**Pros:**
- Persistent, glanceable — always visible while coding
- Rich layout: color-coded scores, stage badges, sparkline history
- Cross-platform (Electron/Tauri work on macOS, Windows, Linux)
- Can be toggled on/off via hotkey

**Cons:**
- Electron adds ~100MB binary footprint
- Tauri is leaner but requires Rust toolchain to build
- Screen real estate consumed permanently
- Always-on-top windows can conflict with full-screen apps
- More complex window lifecycle management

**Complexity:** Medium-High

**User experience:** A semi-transparent panel (e.g. 300x200px) lives in the top-right corner. Each new grade animates in: stage pills (SND pass IOAS pass CTA warn EJAD 7/10) with color coding. Clicking a row expands detail. A collapse arrow hides it to a thin strip.

---

### Approach 3: VS Code / Cursor Sidebar Extension Panel

**How it works:** A VS Code extension (works in Cursor which is VS Code-based) registers a custom TreeView or WebviewPanel in the sidebar. The WorkPulse daemon writes grades to a local socket or file; the extension reads them and renders the panel.

**Pros:**
- Lives exactly where the user is working — no context switch
- Full VS Code API available: colors, icons, CodeLens, hover tooltips
- Can annotate open files with inline decorations (see Approach 4)
- Single install via .vsix or marketplace
- Persistent panel with full history scrollback

**Cons:**
- Extension development is VS Code API-specific (TypeScript)
- Requires publishing or sideloading a .vsix
- Communication between daemon and extension needs a local IPC channel (file watcher, Unix socket, or localhost HTTP)
- Cursor may lag behind VS Code API versions

**Complexity:** High

**User experience:** A "WorkPulse" sidebar panel shows a list of graded turns in reverse-chronological order. Each row shows timestamp, turn snippet, and a compact score badge. Clicking expands the full rubric breakdown. A status bar item in the bottom shows the last grade score at a glance.

---

### Approach 4: Cursor Extension — Inline Decorations & Diagnostics

**How it works:** Extends Approach 3 by using VS Code's TextEditorDecorationType and DiagnosticCollection APIs to annotate the currently-open transcript JSONL file (or a scratch pad) with inline grade markers — colored gutters, end-of-line score badges, and hover cards.

**Pros:**
- Grades appear exactly next to the content being evaluated
- Diagnostics integrate with the Problems panel automatically
- Hover cards can show full rubric detail without leaving the editor
- Very developer-native feel

**Cons:**
- Only useful if the user has the transcript file open
- JSONL format may not be human-readable enough to make inline annotations meaningful
- Diagnostic noise could pollute the Problems panel
- Most complex extension approach

**Complexity:** High

**User experience:** The user opens a Cursor transcript file. Each turn block gets a colored left-gutter marker (green/yellow/red). End-of-line shows "EJAD: 8/10". Hovering shows a rich card: all four stage results, highlighted failing criteria, and suggestions. Failing turns appear in the Problems panel.

---

### Approach 5: System Tray / Menubar App

**How it works:** A minimal menubar app (macOS: rumps or SwiftUI MenuBarExtra; Windows: pystray; Linux: AppIndicator) sits in the system tray. Its icon updates to reflect the latest grade (green/yellow/red). Clicking opens a dropdown with recent grades and a "View Dashboard" link.

**Pros:**
- Extremely low visual footprint — just an icon
- Always accessible without cluttering the screen
- Icon color change gives ambient awareness of grade quality
- Cross-platform libraries exist (pystray works on all three OSes)

**Cons:**
- Menu dropdowns are limited (no charts, no scrollable history)
- macOS tray icon permissions can be fidgety
- Discovery is poor — users may not realize the icon is active
- pystray on Linux requires a running display server / tray support

**Complexity:** Medium

**User experience:** A small colored dot icon lives in the menubar. On new grade, the icon pulses briefly and updates color. Clicking shows a dropdown: last 5 turns with their EJAD scores. A "Full History" item opens the web dashboard (Approach 6) in a browser tab.

---

### Approach 6: Web Dashboard (localhost)

**How it works:** WorkPulse daemon starts a lightweight local HTTP server (FastAPI, Flask, or Express). The dashboard is a single-page app (or server-side rendered HTML) that streams live grade updates via WebSocket or SSE. User opens http://localhost:7474 in any browser.

**Pros:**
- Unlimited UI richness: charts, tables, filters, drill-down
- No installation friction beyond running the daemon
- Works on any OS; browser is already open
- Can show historical trends, aggregations, and rubric analytics
- Easy to share/screenshot for team use

**Cons:**
- Requires the user to keep a browser tab open
- Browser tab competes with other tabs for attention
- No ambient awareness — user must actively switch to it
- Port conflicts possible on shared machines

**Complexity:** Medium

**User experience:** A browser tab at localhost:7474 shows a live feed of graded turns. Left panel: timeline of turns with color-coded scores. Right panel: selected turn detail — all four stage results, highlighted failing criteria, raw turn snippet. Top bar shows running session stats (average EJAD, % turns passing CTA). Auto-scrolls to newest turn.

---

### Approach 7: Terminal TUI (Rich / Textual)

**How it works:** A terminal UI built with Python's rich or textual library. Run as `workpulse tui` in a dedicated terminal pane (or tmux split). Updates in place using terminal control codes — no browser required.

**Pros:**
- Zero dependencies beyond Python — no GUI framework
- Works over SSH, in headless environments, in any terminal emulator
- textual supports mouse clicks, scrollable panes, tabs
- Feels natural to developers who live in the terminal
- Can split-pane next to Cursor's integrated terminal

**Cons:**
- Terminal must remain visible alongside Cursor — requires screen space / split
- No persistent background ambient view — user must have terminal focused
- textual TUI can be slow to render on Windows Terminal
- Not accessible outside the terminal (no mobile, no sharing)

**Complexity:** Medium

**User experience:** A textual app with three panes: (1) live feed of graded turns with score sparklines, (2) detail panel for the selected turn showing all stage results, (3) session stats bar at bottom. Keyboard shortcuts: j/k to navigate turns, Enter to expand, q to quit. Updates arrive in real time as new turns are graded.

---

### Approach 8: Slack / Discord / Telegram Bot

**How it works:** WorkPulse posts grade summaries to a dedicated Slack channel, Discord server, or Telegram chat via bot API. Each graded turn becomes a formatted message with emoji stage indicators and score badges.

**Pros:**
- Persistent, searchable history in a platform the user already has open
- Works on mobile automatically — same messages appear on phone
- Team-friendly: colleagues can see AI usage quality in shared channels
- Rich formatting: Slack blocks, Discord embeds, Telegram HTML
- Can @mention user for failing grades above a severity threshold

**Cons:**
- Requires bot setup and API token management
- Network dependency — won't work offline
- Notification fatigue in active channels
- Potential privacy concern: Cursor transcripts leave the local machine
- Dedicated channel required to avoid spamming existing spaces

**Complexity:** Medium

**User experience:** A #workpulse Slack/Discord channel receives a message per graded turn: "Turn 14 | SND pass | IOAS pass | CTA warn | EJAD 6/10 — Weak action framing". Threads expand to show full rubric. The user checks the channel passively, or sets up notifications for pings on EJAD < 5.

---

### Approach 9: Mobile Push Notifications

**How it works:** WorkPulse sends push notifications to the user's phone via a service like Pushover, Pushbullet, ntfy.sh (self-hosted), or Firebase Cloud Messaging. Only notable events (failing turns, session summaries) are pushed to avoid noise.

**Pros:**
- Truly ambient — phone is always with the user
- Great for end-of-session summaries or critical alerts
- ntfy.sh can be self-hosted for full privacy
- Low cost / free tiers available on Pushover/ntfy

**Cons:**
- Overkill for real-time per-turn feedback (too noisy)
- Best suited for digests and threshold alerts, not continuous monitoring
- Requires smartphone app install (Pushover, ntfy client)
- Network required; no offline operation
- Another service account to manage

**Complexity:** Low-Medium

**User experience:** During a coding session, the phone stays silent. At session end (or when EJAD score drops below threshold), a push notification arrives: "WorkPulse: Session summary — 42 turns, avg EJAD 7.2, 3 turns flagged". Tapping opens a simple mobile-friendly HTML summary page (if ntfy is used with a body attachment).

---

### Approach 10: Email Digest

**How it works:** At the end of each coding session (or on a schedule: hourly, daily), WorkPulse emails a structured HTML digest of graded turns to the user. Uses SMTP, SendGrid, or Resend for delivery.

**Pros:**
- Zero UI to build — HTML email templates are well-understood
- Provides a durable, searchable archive of session history
- Great for daily reflection / retrospective use
- Can include charts (inline base64 images) and full rubric tables

**Cons:**
- Not real-time — fundamentally a batch/digest channel
- Email clients vary wildly in HTML rendering
- Requires SMTP credentials or API key setup
- Inbox pollution if sent too frequently
- No interactivity — read-only artifact

**Complexity:** Low

**User experience:** At session end, the user receives an email: "WorkPulse Digest — Mon Jun 29 | 38 turns | Avg EJAD: 7.4 | 2 CTA flags". The email body contains a table of turns with scores, a bar chart of EJAD scores over the session, and highlighted failing turns with rubric excerpts. Actionable but passive.

---

### Approach 11: Desktop Widget (macOS Notification Center / Windows Widget Board)

**How it works:** On macOS, a Notification Center widget (built with WidgetKit via a Swift helper app) shows live stats. On Windows 11, a PWA or WebView2-based widget appears on the Widget Board. Displays session stats and last grade.

**Pros:**
- Glanceable without switching apps — natural part of OS workflow
- macOS WidgetKit widgets auto-refresh and look native
- Low distraction — only visible when widget board is opened

**Cons:**
- macOS WidgetKit requires Swift development (separate build target)
- Windows Widget Board is Windows 11-only and poorly adopted
- No Linux equivalent (closest is a conky/eww widget — niche)
- Refresh rate limited by OS (WidgetKit timelines are not truly real-time)
- High per-platform effort for medium payoff

**Complexity:** High (per platform)

**User experience:** macOS: The user swipes to Notification Center and sees a WorkPulse widget showing "Last turn: EJAD 8/10 | Session avg: 7.1 | 14 turns graded". Updates every 1-2 minutes. Windows: Widget board panel shows similar info as a card. Best for ambient session awareness, not real-time per-turn feedback.

---

### Approach 12: Browser Extension Popup

**How it works:** A Chrome/Firefox/Edge extension that WorkPulse communicates with via a native messaging host (a local daemon registered as a native app). The extension popup shows recent grades; a badge on the extension icon shows the latest EJAD score.

**Pros:**
- Badge counter on the extension icon gives constant ambient awareness
- Popup provides a rich mini-dashboard without opening a full tab
- Works in any Chromium-based browser (including Cursor's built-in browser, if used)
- Native messaging is well-documented and secure (local only)

**Cons:**
- Requires browser extension install + native messaging host setup (two components)
- Native messaging manifest registration differs per OS (registry on Windows, plist on macOS)
- Extension needs to be sideloaded (unsigned) or published to store
- Only useful if user has browser open and notices the badge

**Complexity:** High

**User experience:** The WorkPulse extension icon in the browser toolbar shows a score badge (e.g. "8"). Clicking the icon opens a 400x500px popup: live feed of last 10 graded turns with scores, a mini bar chart of session trend, and a link to open the full localhost dashboard. The badge turns red when EJAD drops below a threshold.

---

### Approach 13: CLI Output with Watch Mode

**How it works:** `workpulse watch` runs in a terminal, tailing the transcript folder and printing each graded turn to stdout as it arrives. Uses ANSI colors and box-drawing characters for a structured but purely text-based output. No TUI framework needed.

**Pros:**
- Simplest possible implementation — just print() with colors
- Works everywhere: any terminal, SSH, CI, headless server
- Scriptable: output can be piped, grepped, logged to file
- No dependencies beyond the core grading engine
- Easy to debug — the output is the state

**Cons:**
- Scroll-away problem: old grades scroll off screen; no persistent panel
- No interactivity — can't click/navigate turns
- Less polished than a TUI; harder to scan visually
- Requires a dedicated terminal window to stay useful
- No ambient awareness when terminal is not in view

**Complexity:** Low

**User experience:** The user runs `workpulse watch` in a split terminal pane next to Cursor. Each new graded turn prints a formatted block:

    ─────────────────────────────────────
    Turn 14  •  11:47:23
    SND pass  IOAS pass  CTA warn  EJAD 6/10
    -> CTA: Weak action framing in response
    ─────────────────────────────────────

Colors: green for pass, yellow for warn, red for fail. `workpulse watch --json` outputs raw JSON for piping into other tools.

---

## Summary Matrix

| # | Approach | Complexity | Real-time | Persistent | Cross-platform | Privacy |
|---|----------|-----------|-----------|------------|---------------|---------|
| 1 | OS Notifications | Low | Yes | No | Yes | Local |
| 2 | Floating Overlay | Med-High | Yes | Yes | Yes | Local |
| 3 | VS Code Sidebar | High | Yes | Yes | Yes | Local |
| 4 | Inline Decorations | High | Yes | Yes | Yes | Local |
| 5 | System Tray | Medium | Yes | Yes | Yes | Local |
| 6 | Web Dashboard | Medium | Yes | Yes | Yes | Local |
| 7 | Terminal TUI | Medium | Yes | Yes | Yes | Local |
| 8 | Chat Bot | Medium | Yes | Yes | Yes | Cloud (privacy risk) |
| 9 | Mobile Push | Low-Med | Threshold only | Yes | Yes | Cloud (privacy risk) |
| 10 | Email Digest | Low | No | Yes | Yes | Cloud (privacy risk) |
| 11 | Desktop Widget | High | Near-realtime | Yes | No | Local |
| 12 | Browser Extension | High | Yes | Yes | Yes | Local |
| 13 | CLI Watch Mode | Low | Yes | No | Yes | Local |

**Recommended starting point:** Approach 13 (CLI Watch) for MVP validation + Approach 6 (Web Dashboard) as the primary UX, with Approach 1 (OS Notifications) for ambient alerts. This trio covers all bases with incremental complexity.
