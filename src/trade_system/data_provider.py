from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
import random


@dataclass(slots=True)
class StockMeta:
    symbol: str
    name: str
    board: str
    listing_date: date
    market_cap: float


class MockDataProvider:
    """V1 使用模拟数据，后续可替换为真实数据源适配器。"""

    def __init__(self, seed: int = 42) -> None:
        self.random = random.Random(seed)

    def list_stocks(self) -> list[StockMeta]:
        boards = ["SSE", "SZSE", "GEM", "STAR"]
        stocks: list[StockMeta] = []
        base_date = date.today() - timedelta(days=1000)
        for i in range(1, 41):
            board = boards[i % len(boards)]
            symbol = f"{600000 + i}" if board in {"SSE", "STAR"} else f"{1 + i:06d}"
            name = f"样本股{i}"
            if i % 13 == 0:
                name = f"*ST样本{i}"
            listing_date = base_date + timedelta(days=i * 10)
            market_cap = self.random.uniform(20e8, 8000e8)
            stocks.append(StockMeta(symbol, name, board, listing_date, market_cap))
        return stocks

    def generate_daily_series(self, symbol: str, start: date, days: int) -> list[dict]:
        price = self.random.uniform(8, 45)
        concentration = self.random.uniform(30, 70)
        rows: list[dict] = []
        for d in range(days):
            trade_date = start + timedelta(days=d)
            if trade_date.weekday() >= 5:
                continue

            drift = self.random.uniform(-0.03, 0.03)
            open_price = price
            close = max(1.0, price * (1 + drift))
            high = max(open_price, close) * (1 + self.random.uniform(0, 0.02))
            low = min(open_price, close) * (1 - self.random.uniform(0, 0.02))
            volume = self.random.uniform(2e6, 20e6)
            amount = volume * close
            turnover = self.random.uniform(0.01, 0.12)

            main_inflow = self.random.uniform(-2e7, 2e7)
            large_inflow = main_inflow * self.random.uniform(0.4, 0.9)
            xlarge_inflow = main_inflow * self.random.uniform(0.1, 0.5)
            small_inflow = -main_inflow * self.random.uniform(0.3, 0.8)

            concentration = min(95, max(5, concentration + self.random.uniform(-1.5, 1.5)))
            avg_cost = close * self.random.uniform(0.9, 1.1)
            low_zone_ratio = self.random.uniform(0.2, 0.8)
            high_zone_ratio = 1 - low_zone_ratio

            rows.append(
                {
                    "symbol": symbol,
                    "trade_date": trade_date.isoformat(),
                    "open": round(open_price, 2),
                    "high": round(high, 2),
                    "low": round(low, 2),
                    "close": round(close, 2),
                    "volume": round(volume, 2),
                    "amount": round(amount, 2),
                    "turnover": round(turnover, 4),
                    "main_net_inflow": round(main_inflow, 2),
                    "small_net_inflow": round(small_inflow, 2),
                    "large_net_inflow": round(large_inflow, 2),
                    "xlarge_net_inflow": round(xlarge_inflow, 2),
                    "concentration": round(concentration, 2),
                    "avg_cost": round(avg_cost, 2),
                    "low_zone_ratio": round(low_zone_ratio, 4),
                    "high_zone_ratio": round(high_zone_ratio, 4),
                }
            )
            price = close
        return rows
