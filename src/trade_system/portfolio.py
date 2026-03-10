from __future__ import annotations

import sqlite3
from datetime import datetime


def load_positions(conn: sqlite3.Connection) -> dict[str, dict]:
    rows = conn.execute("SELECT * FROM positions").fetchall()
    return {r["symbol"]: dict(r) for r in rows}


def update_last_price(conn: sqlite3.Connection, symbol: str, last_price: float) -> None:
    conn.execute("UPDATE positions SET last_price=?, updated_at=? WHERE symbol=?", (last_price, datetime.now().isoformat(timespec="seconds"), symbol))


def apply_risk_controls(
    conn: sqlite3.Connection,
    recommendations: list[dict],
    take_profit: float,
    stop_loss: float,
) -> list[str]:
    actions: list[str] = []
    positions = load_positions(conn)
    rec_map = {r["symbol"]: r for r in recommendations}

    for symbol, pos in positions.items():
        if symbol not in rec_map:
            continue
        rec = rec_map[symbol]
        pnl = (rec["price"] - pos["avg_price"]) / pos["avg_price"]
        update_last_price(conn, symbol, rec["price"])

        if pnl >= take_profit:
            actions.append(f"{symbol} 触发止盈，建议卖出")
        elif pnl <= stop_loss:
            actions.append(f"{symbol} 触发止损，建议卖出")
        elif rec["action"] in {"建议卖出", "强烈建议卖出"}:
            actions.append(f"{symbol} 评分走弱，建议减仓或卖出")
    return actions
