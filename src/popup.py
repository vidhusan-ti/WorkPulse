"""
popup.py — Cross-platform floating overlay popups using tkinter.
Handles: above-bar approval popup, near-bar coaching popup, 10-min inactivity nudge.
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Callable, Dict, Any, Optional
import threading


def _make_overlay(root: tk.Tk, title: str, width: int = 500, height: int = 350) -> tk.Tk:
    """Configure a floating always-on-top overlay window."""
    root.title(title)
    root.geometry(f"{width}x{height}+50+50")
    root.attributes("-topmost", True)
    root.resizable(False, False)
    root.configure(bg="#1e1e2e")
    return root


def show_above_bar_popup(
    grade: Dict[str, Any],
    window_text: str,
    on_approve: Callable,
    on_reject: Callable,
) -> None:
    """
    Show approval popup for above-bar window.
    Calls on_approve() or on_reject() based on user choice.
    """
    def _run():
        root = tk.Tk()
        _make_overlay(root, "🔱 WorkPulse — Portfolio Candidate", 520, 420)

        # Title
        tk.Label(
            root, text="⭐ Above Bar — Portfolio Candidate",
            bg="#1e1e2e", fg="#cba6f7", font=("Helvetica", 13, "bold")
        ).pack(pady=(14, 4))

        # Score
        tk.Label(
            root, text=f"Score: {grade.get('score', '?')}/10  |  {grade.get('label', '').replace('_', ' ').title()}",
            bg="#1e1e2e", fg="#a6e3a1", font=("Helvetica", 10)
        ).pack(pady=(0, 6))

        # Reason
        reason_box = scrolledtext.ScrolledText(root, height=6, width=58, bg="#313244", fg="#cdd6f4",
                                               font=("Helvetica", 9), wrap=tk.WORD, bd=0)
        reason_box.insert(tk.END, grade.get("reason", ""))
        reason_box.configure(state="disabled")
        reason_box.pack(padx=14, pady=4)

        # Buttons
        btn_frame = tk.Frame(root, bg="#1e1e2e")
        btn_frame.pack(pady=12)

        def approve():
            on_approve()
            root.destroy()

        def reject():
            on_reject()
            root.destroy()

        tk.Button(
            btn_frame, text="✅ Add to Portfolio", command=approve,
            bg="#a6e3a1", fg="#1e1e2e", font=("Helvetica", 10, "bold"),
            padx=14, pady=6, relief="flat", cursor="hand2"
        ).pack(side=tk.LEFT, padx=8)

        tk.Button(
            btn_frame, text="❌ Skip", command=reject,
            bg="#f38ba8", fg="#1e1e2e", font=("Helvetica", 10, "bold"),
            padx=14, pady=6, relief="flat", cursor="hand2"
        ).pack(side=tk.LEFT, padx=8)

        root.mainloop()

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    t.join(timeout=120)  # Auto-close after 2 minutes if no response


def show_near_bar_popup(grade: Dict[str, Any]) -> None:
    """Show coaching popup for near-bar window."""
    def _run():
        root = tk.Tk()
        _make_overlay(root, "🔱 WorkPulse — Coaching", 520, 380)

        tk.Label(
            root, text="💡 Near Bar — Here's how to improve",
            bg="#1e1e2e", fg="#fab387", font=("Helvetica", 13, "bold")
        ).pack(pady=(14, 4))

        tk.Label(
            root, text=f"Score: {grade.get('score', '?')}/10  |  {grade.get('label', '').replace('_', ' ').title()}",
            bg="#1e1e2e", fg="#89b4fa", font=("Helvetica", 10)
        ).pack(pady=(0, 6))

        # Coaching note
        tk.Label(root, text="What was missing:", bg="#1e1e2e", fg="#a6adc8",
                 font=("Helvetica", 9, "bold")).pack(anchor="w", padx=14)
        coaching_box = scrolledtext.ScrolledText(root, height=4, width=58, bg="#313244", fg="#cdd6f4",
                                                  font=("Helvetica", 9), wrap=tk.WORD, bd=0)
        coaching_box.insert(tk.END, grade.get("coaching", ""))
        coaching_box.configure(state="disabled")
        coaching_box.pack(padx=14, pady=(2, 8))

        # Better prompt
        if grade.get("better_prompt"):
            tk.Label(root, text="Stronger version:", bg="#1e1e2e", fg="#a6adc8",
                     font=("Helvetica", 9, "bold")).pack(anchor="w", padx=14)
            bp_box = scrolledtext.ScrolledText(root, height=4, width=58, bg="#313244", fg="#cdd6f4",
                                               font=("Helvetica", 9), wrap=tk.WORD, bd=0)
            bp_box.insert(tk.END, grade.get("better_prompt", ""))
            bp_box.configure(state="disabled")
            bp_box.pack(padx=14, pady=(2, 8))

        tk.Button(
            root, text="Got it", command=root.destroy,
            bg="#89b4fa", fg="#1e1e2e", font=("Helvetica", 10, "bold"),
            padx=14, pady=6, relief="flat", cursor="hand2"
        ).pack(pady=6)

        root.mainloop()

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    t.join(timeout=60)


def show_inactivity_nudge() -> None:
    """Show 10-minute inactivity nudge popup."""
    def _run():
        root = tk.Tk()
        _make_overlay(root, "🔱 WorkPulse — Nudge", 420, 200)

        tk.Label(
            root, text="⏰ 10 Minutes of Low Signal",
            bg="#1e1e2e", fg="#f9e2af", font=("Helvetica", 13, "bold")
        ).pack(pady=(20, 8))

        tk.Label(
            root,
            text="You haven't had an above-bar or near-bar\nprompt in the last 10 minutes.\n\nTry bringing more insight to your next prompt.",
            bg="#1e1e2e", fg="#cdd6f4", font=("Helvetica", 10),
            justify="center"
        ).pack(pady=6)

        tk.Button(
            root, text="Got it", command=root.destroy,
            bg="#f9e2af", fg="#1e1e2e", font=("Helvetica", 10, "bold"),
            padx=14, pady=6, relief="flat", cursor="hand2"
        ).pack(pady=10)

        root.mainloop()

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    t.join(timeout=30)
