# WorkPulse — Transport Layer Architecture Approaches

> How to get data from Cursor to the grading system (SND→IOAS→CTA→EJAD pipeline).
> Generated: 2026-06-29

---

## Overview

Cursor stores conversation transcripts as JSONL files (and/or SQLite databases) on disk.
The challenge is detecting new turns *as they are written* and forwarding them to the grading pipeline with minimal latency and maximum reliability.

The 13 approaches below are ordered roughly from simplest to most sophisticated.

---

### Approach 1: Polling File Watcher

**How it works:** A background process (Python/Node) scans the Cursor transcript directory on a fixed interval (e.g., every 500ms), compares file sizes / mtime against a cached state, and ingests any new bytes appended to JSONL files since the last poll.

**Pros:**
- Dead-simple to implement; no native dependencies
- Works on all OSes (Linux, macOS, Windows) identically
- Easy to tune: lower interval = lower latency
- No Cursor cooperation needed

**Cons:**
- Busy-looping wastes CPU/IO when nothing is happening
- Minimum latency is bounded by poll interval (500ms–2s typical)
- Misses rapid in-place rewrites between polls (edge case)
- Scales poorly with large numbers of transcript files

**Complexity:** Low
**Latency:** 500ms–2s (equal to poll interval)

---

### Approach 2: `watchdog` / `inotify` / FSEvents Native File Watching

**How it works:** Use OS-native filesystem event APIs — `inotify` on Linux, `FSEvents` on macOS, `ReadDirectoryChangesW` on Windows — via the Python `watchdog` library or Node's `chokidar`. The OS pushes `IN_MODIFY` / `kFSEventStreamEventFlagItemModified` events the instant a file is written.

**Pros:**
- Near-instant notification (kernel pushes event, no polling)
- Low CPU overhead; process sleeps until event arrives
- Handles file creation, modification, and deletion cleanly
- `watchdog` / `chokidar` abstract the OS differences

**Cons:**
- On some Linux VMs / Docker environments, inotify events for bind mounts can be unreliable
- `FSEvents` coalesces rapid writes; a very fast LLM stream may merge multiple events
- Still need to parse incremental JSONL appends (byte-offset tracking)
- Large directory trees consume inotify watches (Linux has a system-wide limit)

**Complexity:** Low-Medium
**Latency:** <100ms (typically 10-50ms from write to event delivery)

---

### Approach 3: `tail -F` / Log Tailing

**How it works:** Spawn a `tail -F` (follow) process (or equivalent, e.g., Python's `tailf` or Node's `tail` package) on each JSONL transcript file. `tail -F` handles log rotation automatically and streams new lines to stdout, which WorkPulse reads from the subprocess pipe.

**Pros:**
- Battle-tested, extremely reliable for append-only logs
- Handles file rotation / truncation automatically (`-F` vs `-f`)
- Minimal implementation code -- delegate complexity to `tail`
- Works on all Unix/macOS without extra dependencies

**Cons:**
- Windows requires a shim (no native `tail`; use `Get-Content -Wait` or a library)
- One `tail` process per file -- N processes for N open sessions
- Doesn't detect *new* JSONL files being created (need separate dir watcher)
- Line-buffered: partial JSON lines during streaming responses need buffering

**Complexity:** Low
**Latency:** <200ms (tail wakes on kernel buffer flush, typically 50-150ms)

---

### Approach 4: SQLite WAL (Write-Ahead Log) Reader

**How it works:** Cursor stores conversation state in a SQLite database (e.g., `state.vscdb` in the Cursor user-data directory). When WAL mode is enabled, new writes appear in a `-wal` sidecar file before being checkpointed. A reader opens the DB in read-only mode and polls or watches the WAL file for changes, then queries new rows via SQL.

**Pros:**
- Structured data -- no JSONL parsing needed; query exactly what you need
- Can join across tables (messages, sessions, metadata)
- Atomic reads: SQLite's MVCC ensures consistent snapshots
- Survives crashes better than raw file appends

**Cons:**
- Requires reverse-engineering Cursor's schema (not publicly documented)
- Schema can change with Cursor updates, breaking the reader silently
- SQLite write-ahead log polling still needs a trigger (inotify or timer)
- Cursor may hold an exclusive lock during heavy writes, causing `SQLITE_BUSY`
- Opening the WAL directly (bypassing SQLite) is fragile and unsupported

**Complexity:** Medium-High
**Latency:** 200ms-1s (depends on WAL checkpoint interval + polling)

---

### Approach 5: VS Code Extension API (Cursor Extension)

**How it works:** Author a VS Code extension (works in Cursor, which is a VS Code fork) that subscribes to Cursor's internal extension APIs or VS Code's `workspace` / `window` events. The extension intercepts chat panel messages and pushes them to WorkPulse via a local HTTP/WebSocket endpoint.

**Pros:**
- First-class access to in-process data -- no file parsing at all
- Can hook into Cursor's proposed APIs (e.g., `vscode.lm` chat request events)
- Runs inside Cursor's Node.js process, same event loop
- Can inject UI (status bar, side panel) for real-time feedback within the editor

**Cons:**
- Cursor's chat internals are not part of the stable VS Code API; they may be private/undocumented
- Extension must be installed and trusted by the user
- Cursor updates can break internal hooks
- Sideloading unsigned extensions requires disabling extension signature verification
- Extension context has limited sandbox (no native OS access by default)

**Complexity:** High
**Latency:** <50ms (in-process, synchronous event handling)

---

### Approach 6: Named Pipe / Unix Domain Socket Bridge

**How it works:** WorkPulse creates a named pipe (FIFO) or Unix domain socket at a well-known path. A lightweight shim (shell script, small extension, or LD_PRELOAD hook) running in Cursor's context writes new transcript turns to the pipe. WorkPulse's ingestion service reads from the other end.

**Pros:**
- Zero network overhead; kernel-buffered IPC
- Lower latency than TCP localhost; no serialization overhead beyond JSON
- Clean separation: Cursor side just writes, WorkPulse side just reads
- Works without root; no firewall rules needed

**Cons:**
- Requires a writer shim on the Cursor side (still need to solve the injection problem)
- Named pipes block on write if the reader is slow -- need non-blocking I/O discipline
- Windows uses named pipes with different semantics; cross-platform abstraction needed
- Pipe lifecycle management (create on start, cleanup on crash) adds operational complexity

**Complexity:** Medium
**Latency:** <10ms (kernel IPC, near-zero once data is available)

---

### Approach 7: Local HTTP/WebSocket Server with Cursor Extension Push

**How it works:** WorkPulse runs a local WebSocket server (e.g., on `localhost:39810`). A Cursor VS Code extension connects as a WebSocket client and pushes each new prompt/response turn as a JSON message the moment it is committed to the transcript.

**Pros:**
- Standard, well-understood protocol; easy to debug with browser DevTools
- Bidirectional: WorkPulse can push grading results back to the extension for in-editor display
- Extension can reconnect automatically if WorkPulse restarts
- Clean separation of concerns: transport is just JSON-over-WebSocket

**Cons:**
- Still requires a working Cursor extension to be the push source
- Port conflicts possible on multi-project machines; needs port negotiation
- WebSocket adds a small framing overhead vs. raw sockets (negligible in practice)
- User must install and keep the extension enabled

**Complexity:** Medium
**Latency:** <50ms (extension captures event -> WebSocket send -> WorkPulse receives)

---

### Approach 8: Browser DevTools Protocol (CDP) Interception

**How it works:** Cursor's UI runs in Electron (Chromium). Launch Cursor with `--remote-debugging-port=9229` to enable the Chrome DevTools Protocol. WorkPulse connects as a CDP client, intercepts XHR/Fetch network requests to Cursor's LLM API endpoints, and extracts prompt/response payloads from the intercepted traffic.

**Pros:**
- No filesystem parsing; captures data at the network request layer
- Can intercept streaming SSE/chunked responses in real time
- Full access to request headers, payloads, timing
- No Cursor extension needed; CDP is a standard Electron feature

**Cons:**
- Requires launching Cursor with a non-default flag (user must configure this)
- `--remote-debugging-port` exposes an unauthenticated debug endpoint -- security risk on shared machines
- Cursor may connect to its backend via native code outside the Chromium network stack (not interceptable via CDP)
- CDP API surface is large and fragile across Chromium versions
- Streaming responses require reassembling chunked payloads

**Complexity:** High
**Latency:** Real-time (intercepts in-flight requests as they stream)

---

### Approach 9: LD_PRELOAD / DLL Injection File I/O Hooking

**How it works:** On Linux/macOS, inject a shared library via `LD_PRELOAD` (or `DYLD_INSERT_LIBRARIES`) that intercepts `write()` / `pwrite()` syscalls from Cursor's process. When a write targets a known transcript file path, the hook duplicates the data to a WorkPulse-controlled pipe or shared memory segment.

**Pros:**
- Captures writes at the lowest level -- no polling, no FS events needed
- Works even if Cursor bypasses normal FS notification mechanisms
- Zero latency from write to interception (synchronous hook)

**Cons:**
- Highly invasive; any bug in the hook can crash Cursor
- `LD_PRELOAD` injection is blocked by System Integrity Protection (SIP) on macOS, and by some Linux security modules
- Maintenance nightmare: Cursor updates may change write patterns
- No Windows equivalent (requires DLL injection, which AV tools flag)
- Violates the spirit of sandboxing; may trigger Cursor's own integrity checks

**Complexity:** Very High
**Latency:** <1ms (synchronous interception)

---

### Approach 10: OS-Level eBPF File Tracing (Linux)

**How it works:** Deploy a small eBPF program (via `bpftrace` or `libbpf`) that attaches to the `vfs_write` kernel probe, filters by Cursor's PID, and emits an event whenever Cursor writes to a transcript path. A userspace daemon receives these events via a perf ring buffer and forwards them to the grading pipeline.

**Pros:**
- Kernel-level observability with virtually zero overhead on the hot path
- No modification to Cursor whatsoever; purely observational
- Can filter by file path, PID, or file descriptor cheaply
- Production-grade: used by tools like Falco, Pixie, Tetragon

**Cons:**
- Linux-only (no macOS/Windows equivalent)
- Requires CAP_BPF / CAP_SYS_ADMIN privileges (root or specific capabilities)
- Non-trivial to set up; requires kernel headers or BTF
- eBPF programs have a steep learning curve
- Not suitable for end-user desktop deployments; overkill for a dev tool

**Complexity:** Very High
**Latency:** <5ms (ring-buffer delivery from kernel to userspace)

---

### Approach 11: mitmproxy / TLS Network Interception

**How it works:** Run `mitmproxy` (or a custom CA + proxy) as a system HTTP proxy. Configure the OS or Cursor to route traffic through it. WorkPulse reads the proxy's event stream to extract LLM API calls (prompts and responses) before they are written to disk.

**Pros:**
- Captures all LLM traffic, regardless of how Cursor stores it locally
- No filesystem access needed at all
- Works for any LLM provider Cursor uses
- mitmproxy has a Python addon API for easy filtering and forwarding

**Cons:**
- Requires installing a custom root CA certificate (user trust required)
- TLS pinning in Cursor could block interception
- Proxy must be running for all Cursor sessions; easy to forget
- Adds network latency to every Cursor LLM request (typically 1-5ms)
- Privacy concern: all LLM traffic passes through WorkPulse
- System proxy settings affect all apps, not just Cursor

**Complexity:** High
**Latency:** Real-time (streaming response interception as chunks arrive)

---

### Approach 12: Cursor Workspace Extension + Shared Memory (mmap)

**How it works:** A Cursor VS Code extension mmaps a shared memory segment (via Node.js `mmap-io` or a native addon). When a new turn is written, the extension writes to the shared region and signals WorkPulse via a semaphore or eventfd. WorkPulse reads from the same segment without any copy.

**Pros:**
- Lowest possible copy overhead: zero-copy data transfer between processes
- Signal latency is microseconds once data is in the shared region
- No serialization round-trips for large responses
- Clean producer/consumer model

**Cons:**
- Node.js does not natively support mmap; requires a native addon (`mmap-io`) which complicates packaging
- Shared memory lifecycle (creation, cleanup, crash recovery) is complex
- Harder to debug than sockets or files
- Still requires a Cursor extension as the writer
- Overkill: LLM response sizes rarely justify zero-copy optimization over WebSocket

**Complexity:** Very High
**Latency:** <1ms once extension writes (effectively instantaneous)

---

### Approach 13: inotify + Incremental JSONL Parser (Recommended Baseline)

**How it works:** Combine inotify/FSEvents (Approach 2) with a stateful byte-offset tracker and an incremental JSONL parser. WorkPulse watches the transcript directory for IN_CREATE (new session files) and IN_MODIFY (appended turns). On each event it reads only the new bytes since the last offset, parses complete JSON lines, detects `role: user` / `role: assistant` turn boundaries, and feeds complete windows to the grading pipeline.

**Pros:**
- Best balance of simplicity, reliability, and latency
- No Cursor cooperation, no extensions, no root -- pure userspace
- Handles multi-file sessions naturally (one JSONL per Cursor window)
- Incremental parsing handles partial writes from streaming LLM responses
- `watchdog` / `chokidar` already abstract OS differences
- Easily testable: replay JSONL files to simulate live sessions

**Cons:**
- Still depends on Cursor continuing to write JSONL transcript files (could change)
- Needs schema knowledge of Cursor's JSONL format (reverse-engineered)
- Streaming LLM responses produce partial lines; parser must buffer until newline
- Directory watch depth must be set correctly if sessions are nested in subdirectories

**Complexity:** Low-Medium
**Latency:** 50-150ms (inotify event delay + incremental read + JSON parse)

---

## Summary Comparison

| # | Approach | Complexity | Latency | Cursor Cooperation? | Cross-Platform? |
|---|---|---|---|---|---|
| 1 | Polling File Watcher | Low | 500ms-2s | No | Yes |
| 2 | inotify / FSEvents / watchdog | Low-Med | 10-100ms | No | Yes |
| 3 | `tail -F` Log Tailing | Low | 50-200ms | No | Unix/macOS |
| 4 | SQLite WAL Reader | Med-High | 200ms-1s | No | Yes |
| 5 | VS Code Extension API | High | <50ms | Yes (extension) | Yes |
| 6 | Named Pipe / Unix Socket | Medium | <10ms | Yes (shim) | Partial |
| 7 | Local WebSocket + Extension | Medium | <50ms | Yes (extension) | Yes |
| 8 | CDP Network Interception | High | Real-time | Partial (launch flag) | Yes |
| 9 | LD_PRELOAD I/O Hook | Very High | <1ms | No | Linux/macOS |
| 10 | eBPF vfs_write Trace | Very High | <5ms | No | Linux only |
| 11 | mitmproxy TLS Intercept | High | Real-time | Partial (CA install) | Yes |
| 12 | Shared Memory (mmap) | Very High | <1ms | Yes (extension) | Partial |
| 13 | inotify + Incremental JSONL | Low-Med | 50-150ms | No | Yes |

**Recommended starting point:** Approach 13 (inotify + incremental JSONL parser) -- it is the lowest-friction, most maintainable, and sufficiently fast baseline. If latency below 100ms becomes critical and Cursor API access is available, layer in Approach 7 (WebSocket extension) on top.
