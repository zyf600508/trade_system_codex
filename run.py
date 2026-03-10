import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent / "src"))

from trade_system import TradingMonitorApp


if __name__ == "__main__":
    app = TradingMonitorApp("config.json")
    app.bootstrap()
    app.run_daily()
