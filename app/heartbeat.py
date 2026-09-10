import os
import socket
import threading

from . import config, db


class Heartbeat:
    """Background thread that keeps the `workers` row alive."""

    def __init__(self, worker_type: str, wid: str):
        self.type = worker_type
        self.id = wid
        self._task = ""
        self._task_lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True, name=f"heartbeat-{worker_type}")

    def set_task(self, task: str):
        with self._task_lock:
            self._task = task

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()
        try:
            self._thread.join(timeout=5)
        except RuntimeError:
            pass
        db.execute(
            "UPDATE workers SET status = 'STOPPED', current_task = NULL, last_heartbeat = NOW() WHERE id = %s",
            (self.id,),
        )

    def _loop(self):
        while not self._stop.is_set():
            try:
                with self._task_lock:
                    task = self._task
                db.execute(
                    """
                    INSERT INTO workers (id, type, hostname, status, current_task, last_heartbeat)
                    VALUES (%s, %s, %s, 'HEALTHY', %s, NOW())
                    ON CONFLICT (id) DO UPDATE
                    SET type = EXCLUDED.type,
                        hostname = EXCLUDED.hostname,
                        status = 'HEALTHY',
                        current_task = EXCLUDED.current_task,
                        last_heartbeat = NOW()
                    """,
                    (self.id, self.type, socket.gethostname(), task or None),
                )
            except Exception as e:
                print(f"[heartbeat] error: {e}")
            self._stop.wait(config.HEARTBEAT_INTERVAL)
