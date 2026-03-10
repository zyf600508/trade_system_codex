from __future__ import annotations

from contextlib import contextmanager
import sqlite3
from typing import Iterator


class Database:
    def __init__(self, path: str) -> None:
        self.path = path

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_schema(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS stocks (
                    symbol TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    board TEXT NOT NULL,
                    listing_date TEXT NOT NULL,
                    market_cap REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS daily_bars (
                    symbol TEXT NOT NULL,
                    trade_date TEXT NOT NULL,
                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,
                    volume REAL NOT NULL,
                    amount REAL NOT NULL,
                    turnover REAL NOT NULL,
                    PRIMARY KEY(symbol, trade_date)
                );

                CREATE TABLE IF NOT EXISTS money_flow (
                    symbol TEXT NOT NULL,
                    trade_date TEXT NOT NULL,
                    main_net_inflow REAL NOT NULL,
                    small_net_inflow REAL NOT NULL,
                    large_net_inflow REAL NOT NULL,
                    xlarge_net_inflow REAL NOT NULL,
                    PRIMARY KEY(symbol, trade_date)
                );

                CREATE TABLE IF NOT EXISTS chip_metrics (
                    symbol TEXT NOT NULL,
                    trade_date TEXT NOT NULL,
                    concentration REAL NOT NULL,
                    avg_cost REAL NOT NULL,
                    low_zone_ratio REAL NOT NULL,
                    high_zone_ratio REAL NOT NULL,
                    PRIMARY KEY(symbol, trade_date)
                );

                CREATE TABLE IF NOT EXISTS recommendations (
                    symbol TEXT NOT NULL,
                    trade_date TEXT NOT NULL,
                    score REAL NOT NULL,
                    action TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    PRIMARY KEY(symbol, trade_date)
                );

                CREATE TABLE IF NOT EXISTS positions (
                    symbol TEXT PRIMARY KEY,
                    quantity INTEGER NOT NULL,
                    avg_price REAL NOT NULL,
                    last_price REAL NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS run_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL
                );
                """
            )
