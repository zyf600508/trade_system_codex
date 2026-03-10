from __future__ import annotations

from statistics import mean


def _normalize(value: float, floor: float, ceil: float) -> float:
    if ceil <= floor:
        return 0.0
    return max(0.0, min(1.0, (value - floor) / (ceil - floor)))


def calc_score(rows: list[dict], weights: dict[str, float]) -> tuple[float, str]:
    if len(rows) < 20:
        return 0.0, "样本不足"

    closes = [r["close"] for r in rows]
    volumes = [r["volume"] for r in rows]
    main_inflow = [r["main_net_inflow"] for r in rows]
    concentration = [r["concentration"] for r in rows]

    hhv = max(closes[-120:]) if len(closes) >= 120 else max(closes)
    llv = min(closes[-120:]) if len(closes) >= 120 else min(closes)
    price_pos = (closes[-1] - llv) / (hhv - llv) if hhv > llv else 0.5
    position_score = 1 - price_pos

    inflow_positive_ratio = sum(1 for v in main_inflow[-10:] if v > 0) / 10
    inflow_strength = sum(main_inflow[-10:]) / 2e8
    fund_flow_score = _normalize(inflow_positive_ratio * 0.6 + inflow_strength * 0.4, 0, 1)

    chip_trend = concentration[-1] - concentration[-10]
    low_zone = mean([r["low_zone_ratio"] for r in rows[-5:]])
    chip_score = _normalize(chip_trend / 8 + low_zone, 0, 1)

    vol_ratio = mean(volumes[-5:]) / max(mean(volumes[-20:]), 1)
    price_momentum = (closes[-1] - mean(closes[-20:])) / max(mean(closes[-20:]), 1)
    volume_price_score = _normalize((vol_ratio - 1) * 0.6 + price_momentum * 4 * 0.4, 0, 1)

    total = (
        fund_flow_score * weights["fund_flow_weight"]
        + chip_score * weights["chip_weight"]
        + volume_price_score * weights["volume_price_weight"]
        + position_score * weights["position_weight"]
    ) * 100

    reason = (
        f"主力流入强度={fund_flow_score:.2f}, 筹码结构={chip_score:.2f}, "
        f"量价结构={volume_price_score:.2f}, 位置优势={position_score:.2f}"
    )
    return round(total, 2), reason


def map_action(score: float, thresholds: dict[str, float]) -> str:
    if score >= thresholds["strong_buy"]:
        return "强烈建议买入"
    if score >= thresholds["buy"]:
        return "建议买入"
    if score >= thresholds["watch"]:
        return "重点观望"
    if score >= thresholds["sell"]:
        return "建议卖出"
    return "强烈建议卖出"
