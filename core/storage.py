import sqlite3
from datetime import datetime


class TelemetryDB:
    def __init__(self, db_name="thermal_grid.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self._init_db()

    def _init_db(self):
        """Creates the telemetry table if it doesn't exist."""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                cpu_usage REAL,
                cpu_temp REAL,
                ram_usage REAL,
                vram_clock_sim REAL
            )
        ''')
        self.conn.commit()

    def log_metrics(self, reading: dict):
        """Inserts one telemetry tick, as produced by HardwareSensors.sample()."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute('''
            INSERT INTO system_metrics (timestamp, cpu_usage, cpu_temp, ram_usage, vram_clock_sim)
            VALUES (?, ?, ?, ?, ?)
        ''', (timestamp, reading["cpu"], reading["temp"], reading["ram"], reading["vram"]))
        self.conn.commit()

    def close(self):
        """Flushes and releases the connection. Safe to call more than once."""
        if self.conn is not None:
            self.conn.commit()
            self.conn.close()
            self.conn = None
