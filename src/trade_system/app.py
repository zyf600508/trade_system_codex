from __future__ import annotations

from datetime import date, timedelta
import sqlite3
from typing import Any

from .config import load_config
from .data_provider import MockDataProvider
from .database import Database
from .logger import init_logger
from .portfolio import apply_risk_controls
from .repository import insert_market_row, log_to_db, upsert_stock
from .scoring import calc_score, map_action


class TradingMonitorApp:
    def __init__(self, config_path: str = "config.json") -> None:
        self.cfg = load_config(config_path)
        self.db = Database(self.cfg.system.sqlite_path)
        self.provider = MockDataProvider(seed=42)
        self.logger = init_logger(self.cfg.system.log_file)

    def bootstrap(self) -> None:
        self.db.init_schema()
        stock_list = self.provider.list_stocks()
        today = date.today()
        start = today - timedelta(days=self.cfg.data.bootstrap_days * 2)

        with self.db.connect() as conn:
            for stock in stock_list:
                if not self._stock_allowed(stock, today):
                    continue
                upsert_stock(
                    conn,
                    {
                        "symbol": stock.symbol,
                        "name": stock.name,
                        "board": stock.board,
                        "listing_date": stock.listing_date.isoformat(),
                        "market_cap": stock.market_cap,
                    },
                )

                series = self.provider.generate_daily_series(
                    stock.symbol,
                    start=start,
                    days=self.cfg.data.bootstrap_days * 2,
                )
                for row in series[-self.cfg.data.bootstrap_days :]:
                    insert_market_row(conn, row)

            msg = "首次数据初始化完成"
            self.logger.info(msg)
            log_to_db(conn, "INFO", msg)

    def run_daily(self) -> list[dict[str, Any]]:
        with self.db.connect() as conn:
            symbols = [r["symbol"] for r in conn.execute("SELECT symbol FROM stocks").fetchall()]
            self._append_daily_data(conn, symbols)

            recommendations: list[dict[str, Any]] = []
            for symbol in symbols:
                rows = self._fetch_recent_rows(conn, symbol, days=130)
                score, reason = calc_score(
                    rows,
                    {
                        "fund_flow_weight": self.cfg.score.fund_flow_weight,
                        "chip_weight": self.cfg.score.chip_weight,
                        "volume_price_weight": self.cfg.score.volume_price_weight,
                        "position_weight": self.cfg.score.position_weight,
                    },
                )
                action = map_action(
                    score,
                    {
                        "strong_buy": self.cfg.score.thresholds.strong_buy,
                        "buy": self.cfg.score.thresholds.buy,
                        "watch": self.cfg.score.thresholds.watch,
                        "sell": self.cfg.score.thresholds.sell,
                    },
                )
                price = rows[-1]["close"] if rows else 0
                trade_date = rows[-1]["trade_date"] if rows else date.today().isoformat()

                conn.execute(
                    """
                    INSERT OR REPLACE INTO recommendations(symbol, trade_date, score, action, reason)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (symbol, trade_date, score, action, reason),
                )
                recommendations.append(
                    {
                        "symbol": symbol,
                        "score": score,
                        "action": action,
                        "reason": reason,
                        "price": price,
                    }
                )

            recommendations.sort(key=lambda x: x["score"], reverse=True)
            risk_msgs = apply_risk_controls(
                conn,
                recommendations,
                take_profit=self.cfg.risk.take_profit,
                stop_loss=self.cfg.risk.stop_loss,
            )

            log_to_db(conn, "INFO", f"当日评分完成，股票数={len(recommendations)}")
            for m in risk_msgs:
                log_to_db(conn, "INFO", m)
                self.logger.info(m)

            topn = recommendations[:10]
            self.logger.info("当日Top10建议：")
            for idx, rec in enumerate(topn, start=1):
                self.logger.info(
                    "%s. %s 分数=%s 建议=%s",
                    idx,
                    rec["symbol"],
                    rec["score"],
                    rec["action"],
                )
            return topn

    def _append_daily_data(self, conn: sqlite3.Connection, symbols: list[str]) -> None:
        for symbol in symbols:
            latest = conn.execute(
                "SELECT MAX(trade_date) AS d FROM daily_bars WHERE symbol=?", (symbol,)
            ).fetchone()["d"]
            if latest is None:
                continue
            next_day = date.fromisoformat(latest) + timedelta(days=1)
            series = self.provider.generate_daily_series(
                symbol=symbol,
                start=next_day,
                days=self.cfg.data.daily_increment_days + 2,
            )
            if not series:
                continue
            insert_market_row(conn, series[-1])

    def _fetch_recent_rows(self, conn: sqlite3.Connection, symbol: str, days: int) -> list[dict]:
        rows = conn.execute(
            """
            SELECT b.trade_date, b.close, b.volume, m.main_net_inflow, c.concentration, c.low_zone_ratio
            FROM daily_bars b
            JOIN money_flow m ON b.symbol=m.symbol AND b.trade_date=m.trade_date
            JOIN chip_metrics c ON b.symbol=c.symbol AND b.trade_date=c.trade_date
            WHERE b.symbol=?
            ORDER BY b.trade_date DESC
            LIMIT ?
            """,
            (symbol, days),
        ).fetchall()
        return [dict(r) for r in reversed(rows)]

    def _stock_allowed(self, stock: Any, today: date) -> bool:
        if stock.board not in self.cfg.market.allowed_boards:
            return False
        if self.cfg.market.exclude_st and ("ST" in stock.name.upper()):
            return False
        if (today - stock.listing_date).days < self.cfg.market.min_listing_days:
            return False
        if stock.market_cap > self.cfg.market.max_market_cap:
            return False
        return True
