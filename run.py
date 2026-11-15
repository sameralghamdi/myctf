"""Dev server entrypoint:  python run.py  (or  flask --app run run)."""
from __future__ import annotations

import os
import threading
import time

from app import create_app

app = create_app()


def _lab_sweeper(flask_app):
    """Background loop that expires overdue labs (dev stand-in for a worker)."""
    from app.labs import sweep_expired
    while True:
        time.sleep(60)
        try:
            with flask_app.app_context():
                sweep_expired()
        except Exception:
            pass


if __name__ == "__main__":
    if os.environ.get("MYCTF_SWEEPER", "1") == "1":
        threading.Thread(target=_lab_sweeper, args=(app,), daemon=True).start()
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="127.0.0.1", port=port, debug=bool(os.environ.get("MYCTF_DEBUG")))
