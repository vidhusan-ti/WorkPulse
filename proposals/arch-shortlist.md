# WorkPulse Architecture — 50 Approaches Ranked → Top 20 → Top 10

## Scoring criteria
Each approach is scored 1-5 on:
- **Realtime** — how fast does the user see a result?
- **Friction** — how hard is setup for a new user?
- **Reliability** — will it keep working across Cursor updates?
- **UX** — how good is the user experience?
- **Feasibility** — can a small team build and maintain this?

Higher = better. Max score = 25.

---

## All 52 Approaches (Transport × UI × Deployment × Pipeline combined)

### Transport Layer (how data gets from Cursor to grader)
| # | Approach | Realtime | Friction | Reliability | UX | Feasibility | Total |
|---|---|---|---|---|---|---|---|
| T1 | Polling file watcher | 2 | 5 | 4 | 3 | 5 | **19** |
| T2 | inotify/FSEvents/watchdog | 5 | 4 | 4 | 4 | 5 | **22** |
| T3 | tail -F log tailing | 4 | 5 | 4 | 3 | 5 | **21** |
| T4 | SQLite WAL reader | 3 | 3 | 2 | 3 | 3 | **14** |
| T5 | VS Code Extension API | 5 | 2 | 3 | 5 | 3 | **18** |
| T6 | Named pipe / Unix socket | 5 | 3 | 3 | 3 | 3 | **17** |
| T7 | Local WebSocket + Extension | 5 | 2 | 3 | 4 | 3 | **17** |
| T8 | CDP network interception | 5 | 1 | 1 | 3 | 2 | **12** |
| T9 | LD_PRELOAD I/O hook | 5 | 1 | 1 | 2 | 1 | **10** |
| T10 | eBPF vfs_write trace | 5 | 1 | 1 | 2 | 1 | **10** |
| T11 | mitmproxy TLS intercept | 4 | 1 | 1 | 2 | 2 | **10** |
| T12 | Shared memory mmap | 5 | 1 | 1 | 2 | 1 | **10** |
| T13 | inotify + incremental JSONL ⭐ | 5 | 5 | 5 | 4 | 5 | **24** |

### UI Layer (how results reach the user)
| # | Approach | Realtime | Friction | Reliability | UX | Feasibility | Total |
|---|---|---|---|---|---|---|---|
| U1 | Native OS notifications | 5 | 5 | 5 | 3 | 5 | **23** |
| U2 | Floating overlay (Electron/Tauri) | 5 | 3 | 4 | 5 | 3 | **20** |
| U3 | Cursor sidebar panel | 5 | 2 | 3 | 5 | 2 | **17** |
| U4 | Cursor inline decorations | 5 | 2 | 2 | 5 | 2 | **16** |
| U5 | System tray / menubar | 4 | 4 | 4 | 3 | 4 | **19** |
| U6 | Web dashboard (localhost) | 4 | 4 | 5 | 5 | 4 | **22** |
| U7 | Terminal TUI | 4 | 4 | 5 | 3 | 5 | **21** |
| U8 | Slack/Discord/Telegram bot | 3 | 3 | 4 | 3 | 4 | **17** |
| U9 | Mobile push (ntfy/Pushover) | 3 | 3 | 4 | 3 | 4 | **17** |
| U10 | Email digest | 1 | 5 | 5 | 2 | 5 | **18** |
| U11 | Desktop widget | 3 | 2 | 3 | 4 | 2 | **14** |
| U12 | Browser extension popup | 3 | 2 | 3 | 3 | 2 | **13** |
| U13 | CLI watch mode ⭐ | 5 | 5 | 5 | 3 | 5 | **23** |

### Deployment Layer (where the system runs)
| # | Approach | Realtime | Friction | Reliability | UX | Feasibility | Total |
|---|---|---|---|---|---|---|---|
| D1 | Pure local Python daemon | 5 | 3 | 4 | 3 | 5 | **20** |
| D2 | pip package + autostart | 5 | 4 | 4 | 4 | 5 | **22** |
| D3 | Cursor extension | 5 | 5 | 3 | 5 | 3 | **21** |
| D4 | Electron desktop app | 5 | 5 | 4 | 5 | 3 | **22** |
| D5 | Native macOS app | 5 | 5 | 5 | 5 | 2 | **22** |
| D6 | Local + cloud hybrid | 4 | 3 | 4 | 4 | 3 | **18** |
| D7 | Full cloud | 2 | 2 | 3 | 3 | 2 | **12** |
| D8 | Docker container | 4 | 3 | 4 | 3 | 4 | **18** |
| D9 | npm / npx package | 5 | 4 | 4 | 4 | 5 | **22** |
| D10 | Serverless on file change | 2 | 2 | 2 | 2 | 2 | **10** |
| D11 | GitHub Actions / CI | 1 | 3 | 4 | 1 | 4 | **13** |
| D12 | Browser PWA | 3 | 4 | 3 | 3 | 3 | **16** |
| D13 | OpenClaw agent ⭐ | 4 | 5 | 4 | 4 | 5 | **22** |

### Pipeline Layer (how grading executes)
| # | Approach | Realtime | Friction | Reliability | UX | Feasibility | Total |
|---|---|---|---|---|---|---|---|
| P1 | Synchronous blocking | 2 | 5 | 5 | 2 | 5 | **19** |
| P2 | Async background + notify | 4 | 5 | 5 | 4 | 5 | **23** |
| P3 | Streaming stage-by-stage ⭐ | 5 | 4 | 5 | 5 | 4 | **23** |
| P4 | FIFO queue | 3 | 5 | 5 | 3 | 5 | **21** |
| P5 | Priority queue (newest first) | 5 | 4 | 5 | 5 | 4 | **23** |
| P6 | Batched periodic flush | 2 | 5 | 5 | 2 | 5 | **19** |
| P7 | SND fast-path pre-filter ⭐ | 5 | 5 | 5 | 5 | 5 | **25** |
| P8 | Semantic caching | 4 | 4 | 4 | 4 | 4 | **20** |
| P9 | Local model escalation | 4 | 2 | 3 | 4 | 2 | **15** |
| P10 | End-of-session batch | 1 | 5 | 5 | 2 | 5 | **18** |
| P11 | Differential grading | 4 | 5 | 5 | 4 | 5 | **23** |
| P12 | Concurrent parallel stages | 5 | 4 | 4 | 5 | 3 | **21** |
| P13 | Human-in-the-loop gate | 3 | 4 | 5 | 4 | 4 | **20** |

---

## Top 20 (scores ≥ 21, one from each category plus cross-cutting combinations)

| Rank | Code | Approach | Score | Why it matters |
|---|---|---|---|---|
| 1 | P7 | SND fast-path pre-filter | 25 | Cheapest win — kills obvious below-bar before LLM call |
| 2 | T13 | inotify + incremental JSONL | 24 | Best transport — no Cursor cooperation, cross-platform |
| 3 | P2 | Async background + notify | 23 | Non-blocking grading baseline |
| 4 | P3 | Streaming stage-by-stage | 23 | First result in ~1-2s, feels instant |
| 5 | P5 | Priority queue (newest first) | 23 | Always grades most recent prompt first |
| 6 | P11 | Differential grading | 23 | Skip re-grading, only process new turns |
| 7 | U1 | Native OS notifications | 23 | Zero-UI, instant, works with any deployment |
| 8 | U13 | CLI watch mode | 23 | Simplest MVP, scriptable |
| 9 | T2 | inotify/FSEvents/watchdog | 22 | Core of T13 — solid standalone option |
| 10 | D2 | pip package + autostart | 22 | Lowest-friction Python deployment |
| 11 | D4 | Electron desktop app | 22 | Best cross-platform packaged UX |
| 12 | D5 | Native macOS app | 22 | Best macOS UX, FSEvents native |
| 13 | D9 | npm/npx package | 22 | Zero-install for JS teams |
| 14 | D13 | OpenClaw agent | 22 | Already running — near-zero extra setup |
| 15 | U6 | Web dashboard (localhost) | 22 | Richest UI, full history, SSE live feed |
| 16 | D3 | Cursor extension | 21 | Best UX — lives inside the editor |
| 17 | T3 | tail -F log tailing | 21 | Unix-native, dead simple |
| 18 | P4 | FIFO queue | 21 | Orderly processing, prevents race conditions |
| 19 | P12 | Concurrent parallel stages | 21 | 2-4s via parallelism instead of 3-8s sequential |
| 20 | U7 | Terminal TUI | 21 | SSH-friendly, keyboard-navigable |

---

## Top 10 — Final Shortlist

| Rank | Approach | Dimension | Why it's top 10 |
|---|---|---|---|
| **1** | **inotify + incremental JSONL (T13)** | Transport | Best foundation — no Cursor cooperation, 50-150ms, cross-platform, already partially built in the codebase |
| **2** | **SND fast-path pre-filter (P7)** | Pipeline | Add to any approach — kills obvious below-bar in <100ms before spending LLM tokens |
| **3** | **Async background + streaming stages (P2+P3)** | Pipeline | Non-blocking + first result in ~1-2s = feels real-time without blocking Cursor |
| **4** | **Priority queue newest-first (P5)** | Pipeline | User just typed → that window grades first, older backlog waits |
| **5** | **Native OS notifications (U1)** | UI | Zero-friction alert when above-bar prompt found — works on macOS/Windows/Linux |
| **6** | **Web dashboard localhost (U6)** | UI | Full history, filters, live SSE feed — open in browser, stays out of editor |
| **7** | **pip package + systemd/launchd autostart (D2)** | Deployment | `pip install workpulse` → runs on login, grades in background, zero ongoing maintenance |
| **8** | **Cursor extension with sidebar (D3+U3)** | Deployment+UI | Best UX — results appear inside the editor, no context switch — harder to build but best end state |
| **9** | **Differential grading (P11)** | Pipeline | Only process new turns since last check — avoids re-grading the same windows repeatedly |
| **10** | **OpenClaw agent deployment (D13)** | Deployment | Already running, can poll transcript folders on a heartbeat — zero new infrastructure for a working prototype |

---

## Recommended build sequence

### Phase 1 — Working prototype (1-2 days)
**T13 + P7 + P2 + U1 + D13**
- OpenClaw agent polls Cursor transcript folder every 60s
- inotify/watchdog detects new JSONL files
- SND pre-filter kills below-bar instantly
- Remaining windows grade async through pipeline
- OS notification fires when above-bar found
- **Result:** End-to-end working, zero new UI to build

### Phase 2 — Real-time feel (3-5 days)
**+ P3 + P5 + U6**
- Streaming stage-by-stage so user sees "grading..." progress
- Priority queue so newest prompt always grades first
- Localhost web dashboard showing live feed + history
- **Result:** Feels genuinely real-time, has a UI

### Phase 3 — Production (1-2 weeks)
**+ D2 + D3/U3**
- pip package with autostart
- Optional: Cursor extension with sidebar panel
- **Result:** Installable product, in-editor UX

