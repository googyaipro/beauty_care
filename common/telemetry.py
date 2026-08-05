"""Telemetry module stub."""

from contextlib import contextmanager

@contextmanager
def trace_step(trace_id: str, step_name: str, metadata=None):
    yield {}

def get_trace(trace_id: str):
    return []

def clear_trace(trace_id: str):
    pass

_ACTIVE_TRACES = {}
