"""Setup for WorkPulse — installs workpulse-monitor CLI entry point."""

from setuptools import setup, find_packages

setup(
    name="workpulse",
    version="0.1.0",
    description="WorkPulse — AI Prompt Coach for Cursor. Real-time transcript monitoring and grading.",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "watchdog>=3.0.0",
        "anthropic>=0.20.0",
        "flask>=3.0.0",
        "flask-cors>=4.0.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "notifications": ["plyer>=2.1.0"],
        "fast-snd": ["sentence-transformers>=2.0.0"],
        "openai": ["openai>=1.0.0"],
    },
    entry_points={
        "console_scripts": [
            "workpulse-monitor=src.cli_monitor:main",
        ],
    },
)
