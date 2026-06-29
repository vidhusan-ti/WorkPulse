"""
notifier.py — OS-native desktop notifications for above_bar verdicts.

Strategy:
  1. Try plyer (cross-platform)
  2. Fall back to native OS commands:
     - macOS: osascript
     - Linux: notify-send
     - Windows: PowerShell toast
"""

from __future__ import annotations

import logging
import os
import platform
import subprocess
from typing import Any, Dict

logger = logging.getLogger(__name__)

APP_NAME = "WorkPulse"


def notify(
    title: str,
    message: str,
    urgency: str = "normal",
) -> None:
    """Send a desktop notification.

    Parameters
    ----------
    title:
        Notification title.
    message:
        Notification body text.
    urgency:
        Hint for plyer/notify-send (``"low"`` | ``"normal"`` | ``"critical"``).
    """
    # Try plyer first
    if _notify_plyer(title, message):
        return
    # Fall back to OS-native
    system = platform.system()
    if system == "Darwin":
        _notify_macos(title, message)
    elif system == "Linux":
        _notify_linux(title, message, urgency)
    elif system == "Windows":
        _notify_windows(title, message)
    else:
        logger.warning("No notification backend available on %s.", system)


def notify_result(result: Dict[str, Any], prompt_preview: str) -> None:
    """Fire a notification for a graded result if it's above_bar.

    Only above_bar triggers a notification. near_bar and below_bar are silent.
    """
    tier = result.get("tier", "")
    if tier != "above_bar":
        return

    label = result.get("label", "above_bar")
    score = result.get("score", "?")
    short_prompt = (prompt_preview[:100] + "…") if len(prompt_preview) > 100 else prompt_preview
    title = f"🎯 {APP_NAME}: {label} (score {score})"
    body = short_prompt or "(no prompt text)"
    notify(title, body)


# ---------------------------------------------------------------------------
# Backend implementations
# ---------------------------------------------------------------------------

def _notify_plyer(title: str, message: str) -> bool:
    """Try plyer notification. Returns True on success."""
    try:
        from plyer import notification  # type: ignore
        notification.notify(
            app_name=APP_NAME,
            title=title,
            message=message,
            timeout=8,
        )
        return True
    except ImportError:
        return False
    except Exception as exc:
        logger.debug("plyer notification failed: %s", exc)
        return False


def _notify_macos(title: str, message: str) -> None:
    """macOS notification via osascript."""
    # Escape for AppleScript string literal
    safe_title = title.replace('"', '\\"').replace("'", "\\'")
    safe_message = message.replace('"', '\\"').replace("'", "\\'")
    script = (
        f'display notification "{safe_message}" '
        f'with title "{safe_title}" '
        f'subtitle "{APP_NAME}"'
    )
    try:
        subprocess.run(
            ["osascript", "-e", script],
            check=False,
            capture_output=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        logger.debug("osascript notification failed: %s", exc)


def _notify_linux(title: str, message: str, urgency: str = "normal") -> None:
    """Linux notification via notify-send."""
    try:
        subprocess.run(
            [
                "notify-send",
                "--app-name", APP_NAME,
                "--urgency", urgency,
                title,
                message,
            ],
            check=False,
            capture_output=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        logger.debug("notify-send failed: %s", exc)


def _notify_windows(title: str, message: str) -> None:
    """Windows notification via PowerShell toast."""
    ps_script = f"""
Add-Type -AssemblyName System.Windows.Forms
$notify = New-Object System.Windows.Forms.NotifyIcon
$notify.Icon = [System.Drawing.SystemIcons]::Information
$notify.BalloonTipIcon = "Info"
$notify.BalloonTipTitle = "{title}"
$notify.BalloonTipText = "{message}"
$notify.Visible = $True
$notify.ShowBalloonTip(8000)
Start-Sleep -Seconds 2
$notify.Dispose()
"""
    try:
        subprocess.run(
            ["powershell", "-NonInteractive", "-Command", ps_script],
            check=False,
            capture_output=True,
            timeout=15,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        logger.debug("PowerShell toast notification failed: %s", exc)
