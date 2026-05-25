import csv
import json
import os
import queue
import threading
from datetime import datetime


class DataLogger:
    DEFAULT_LOG_DIR = "logs"
    DEFAULT_LOG_INTERVAL_TICKS = 10

    COLUMNS = [
        "tick",
        "interval_ticks",
        "total_agents",
        "prey_cnt",
        "pred_cnt",
        "clover_cnt",
        "births_total",
        "births_prey",
        "births_pred",
        "births_clover",
        "deaths_total",
        "deaths_thirst",
        "deaths_age",
        "deaths_predation",
        "deaths_consumed",
        "deaths_other",
        "dropped_frames",
        "avg_prey_hunger",
        "avg_prey_thirst",
        "avg_prey_speed",
        "avg_prey_size",
        "avg_prey_sense",
        "avg_prey_age",
        "avg_pred_hunger",
        "avg_pred_thirst",
        "avg_pred_speed",
        "avg_pred_size",
        "avg_pred_sense",
        "avg_pred_age",
        "avg_clover_thirst",
        "avg_clover_age",
    ]

    def __init__(self, log_dir=None, run_config=None, log_interval_ticks=None):
        resolved_dir = log_dir or self.DEFAULT_LOG_DIR
        resolved_interval = log_interval_ticks or self.DEFAULT_LOG_INTERVAL_TICKS

        self.log_interval_ticks = max(1, int(resolved_interval))
        self.run_config = run_config or {}

        os.makedirs(resolved_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_id = f"run_{timestamp}"
        self.csv_path = os.path.join(resolved_dir, f"{self.run_id}.csv")
        self.meta_path = os.path.join(resolved_dir, f"{self.run_id}.json")

        self.start_time = datetime.now().isoformat(timespec="seconds")
        self.dropped_rows = 0

        self._queue = queue.Queue(maxsize=200)
        self._running = True
        self._thread = threading.Thread(target=self._writer_loop, daemon=True)
        self._thread.start()

    def _writer_loop(self):
        with open(self.csv_path, "w", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=self.COLUMNS)
            writer.writeheader()
            flush_counter = 0

            while self._running or not self._queue.empty():
                try:
                    row = self._queue.get(timeout=0.2)
                except queue.Empty:
                    continue

                if row is None:
                    break

                writer.writerow(row)
                flush_counter += 1

                if flush_counter >= 25:
                    csv_file.flush()
                    flush_counter = 0

            csv_file.flush()

    def enqueue_row(self, row):
        try:
            self._queue.put_nowait(row)
        except queue.Full:
            self.dropped_rows += 1

    def close(self, summary=None):
        self._running = False
        try:
            self._queue.put_nowait(None)
        except queue.Full:
            pass

        self._thread.join(timeout=2)
        self._write_summary(summary or {})

    def _write_summary(self, summary):
        payload = {
            "run_id": self.run_id,
            "start_time": self.start_time,
            "end_time": datetime.now().isoformat(timespec="seconds"),
            "log_interval_ticks": self.log_interval_ticks,
            "run_config": self.run_config,
            "dropped_rows": self.dropped_rows,
            "summary": summary,
        }

        with open(self.meta_path, "w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2, ensure_ascii=True)
