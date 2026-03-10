from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json


@dataclass(slots=True)
class MarketConfig:
    allowed_boards: list[str]
    min_listing_days: int
    max_market_cap: float
    exclude_st: bool


@dataclass(slots=True)
class DataConfig:
    bootstrap_days: int
    daily_increment_days: int


@dataclass(slots=True)
class ScoreThresholds:
    strong_buy: float
    buy: float
    watch: float
    sell: float


@dataclass(slots=True)
class ScoreConfig:
    fund_flow_weight: float
    chip_weight: float
    volume_price_weight: float
    position_weight: float
    thresholds: ScoreThresholds


@dataclass(slots=True)
class RiskConfig:
    take_profit: float
    stop_loss: float
    max_positions: int
    max_single_position_ratio: float


@dataclass(slots=True)
class AccountConfig:
    initial_cash: float


@dataclass(slots=True)
class SystemConfig:
    sqlite_path: str
    log_file: str


@dataclass(slots=True)
class AppConfig:
    market: MarketConfig
    data: DataConfig
    score: ScoreConfig
    risk: RiskConfig
    account: AccountConfig
    system: SystemConfig


def load_config(config_path: str | Path = "config.json") -> AppConfig:
    data = json.loads(Path(config_path).read_text(encoding="utf-8"))
    return AppConfig(
        market=MarketConfig(**data["market"]),
        data=DataConfig(**data["data"]),
        score=ScoreConfig(
            fund_flow_weight=data["score"]["fund_flow_weight"],
            chip_weight=data["score"]["chip_weight"],
            volume_price_weight=data["score"]["volume_price_weight"],
            position_weight=data["score"]["position_weight"],
            thresholds=ScoreThresholds(**data["score"]["thresholds"]),
        ),
        risk=RiskConfig(**data["risk"]),
        account=AccountConfig(**data["account"]),
        system=SystemConfig(**data["system"]),
    )
