"""
live_poller.py
Background thread that polls API-Football every N seconds
and pushes updates into the GUI via a thread-safe queue.
"""

import threading
import queue
import time
from typing import Optional
from live_data import fetch_live_matches, fetch_matches_by_date, today_str

POLL_INTERVAL_LIVE = 15  # seconds between live match refreshes
POLL_INTERVAL_TODAY = 60  # seconds between today's fixture refreshes


class LivePoller:
    """
    Runs two background threads:
    - one polling live matches every 15s
    - one polling today's fixtures every 60s
    Results are pushed into self.queue as (event_type, data) tuples.
    """

    def __init__(self):
        self.queue: queue.Queue = queue.Queue()
        self._stop_event = threading.Event()
        self._live_thread: Optional[threading.Thread] = None
        self._today_thread: Optional[threading.Thread] = None
        self.running = False

    def start(self):
        if self.running:
            return
        self._stop_event.clear()
        self.running = True

        self._live_thread = threading.Thread(
            target=self._poll_live,
            daemon=True,
            name="LiveMatchPoller"
        )
        self._today_thread = threading.Thread(
            target=self._poll_today,
            daemon=True,
            name="TodayFixturePoller"
        )

        self._live_thread.start()
        self._today_thread.start()
        print("[poller] Started live + today threads")

    def stop(self):
        self._stop_event.set()
        self.running = False
        print("[poller] Stopped")

    def _poll_live(self):
        while not self._stop_event.is_set():
            try:
                matches = fetch_live_matches()
                self.queue.put(("live_matches", matches))
            except Exception as e:
                self.queue.put(("error", f"live: {e}"))
            self._stop_event.wait(POLL_INTERVAL_LIVE)

    def _poll_today(self):
        while not self._stop_event.is_set():
            try:
                matches = fetch_matches_by_date(today_str())
                self.queue.put(("today_matches", matches))
            except Exception as e:
                self.queue.put(("error", f"today: {e}"))
            self._stop_event.wait(POLL_INTERVAL_TODAY)