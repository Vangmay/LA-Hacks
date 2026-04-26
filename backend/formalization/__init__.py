"""Formalize & Verify mode.

This package is intentionally isolated from the review pipeline. It reads
completed review jobs, runs an AXLE-backed Lean formalization loop, and exposes
its own store, event bus, and API surface.
"""
