from collections import deque
import threading

# Simple in-memory status store for scraper progress messages.
# This is process-local; for multiple replicas use Redis or DB-backed store.

_lock = threading.Lock()
_messages = deque(maxlen=200)
_running = False

def add_message(msg: str):
    with _lock:
        _messages.append({'ts': __import__('datetime').datetime.utcnow().isoformat() + 'Z', 'msg': msg})

def get_messages():
    with _lock:
        return list(_messages)

def set_running(value: bool):
    global _running
    with _lock:
        _running = bool(value)

def is_running() -> bool:
    with _lock:
        return bool(_running)
