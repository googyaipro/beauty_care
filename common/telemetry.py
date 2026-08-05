import time
from contextlib import contextmanager

_ACTIVE_TRACES = {}

@contextmanager
def trace_step(trace_id: str, step_name: str, metadata=None):
    start_time = time.time()
    span = {
        "step_name": step_name,
        "status": "OK",
        "metadata": metadata or {},
    }
    try:
        yield span
    except Exception as e:
        span["status"] = "ERROR"
        span["error"] = str(e)
        raise
    finally:
        end_time = time.time()
        span["duration_ms"] = int((end_time - start_time) * 1000)
        if trace_id not in _ACTIVE_TRACES:
            _ACTIVE_TRACES[trace_id] = []
        _ACTIVE_TRACES[trace_id].append(span)

def get_trace(trace_id: str):
    return _ACTIVE_TRACES.get(trace_id, [])

def clear_trace(trace_id: str):
    _ACTIVE_TRACES[trace_id] = []

