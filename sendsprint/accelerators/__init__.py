"""Optional Rust accelerator boundary with Python fallback.

Hot paths — file scanning, diff parsing, deduplication, receipt hashing —
have pure-Python implementations that are **always available**.  When a Rust
CLI binary (``sendsprint-accel``) is detected on ``$PATH``, the same
operations are transparently delegated to it via subprocess for better
throughput on large workloads.

Issue: #108
"""

from __future__ import annotations

from sendsprint.accelerators.resolver import resolve_accelerator

__all__ = ["resolve_accelerator"]
