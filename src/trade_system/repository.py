from __future__ import annotations

from datetime import datetime
import sqlite3


def upsert_stock(conn: sqlite3.Connection, row: dict) -> None:
    conn.execute(
        """
        INSERT INTO stocks(symbol, name, board, listing_date, market_cap)
        VALUES(:symbol, :name, :board, :listing_date, :market_cap)
        ON CONFLICT(symbol) DO UPDATE SET
            name=excluded.name,
            board=excluded.board,
            listing_date=excluded.listing_date,
            market_cap=excluded.market_cap
        """,
        row,
    )


def insert_market_row(conn: sqlite3.Connection, row: dict) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO daily_bars(
            symbol, trade_date, open, high, low, close, volume, amount, turnover
        ) VALUES (
            :symbol, :trade_date, :open, :high, :low, :close, :volume, :amount, :turnover
        )
        """,
        row,
    )
    conn.execute(
        """
        INSERT OR REPLACE INTO money_flow(
            symbol, trade_date, main_net_inflow, small_net_inflow, large_net_inflow, xlarge_net_inflow
        ) VALUES (
            :symbol, :trade_date, :main_net_inflow, :small_net_inflow, :large_net_inflow, :xlarge_net_inflow
        )
        """,
        row,
    )
    conn.execute(
        """
        INSERT OR REPLACE INTO chip_metrics(
            symbol, trade_date, concentration, avg_cost, low_zone_ratio, high_zone_ratio
        ) VALUES (
            :symbol, :trade_date, :concentration, :avg_cost, :low_zone_ratio, :high_zone_ratio
        )
        """,
        row,
    )


def log_to_db(conn: sqlite3.Connection, level: str, message: str) -> None:
    conn.execute(
        "INSERT INTO run_logs(created_at, level, message) VALUES(?, ?, ?)",
        (datetime.now().isoformat(timespec="seconds"), level, message),
    )
