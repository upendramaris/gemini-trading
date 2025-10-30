from ib_insync import IB, Stock, util  # type: ignore[import-not-found]
import queue
from backtester.events import MarketEvent
import pandas as pd

class IBKRDataHandler:
    """
    IBKRDataHandler is designed to connect to Interactive Brokers Trader Workstation (TWS) or IB Gateway,
    fetch historical data, and provide market data for backtesting.
    """

    def __init__(self, events: queue.Queue, host='127.0.0.1', port=7497, clientId=1):
        """
        Initialises the data handler by connecting to IBKR.

        Args:
            events: The event queue for the backtesting system.
            host: The host address of TWS/IB Gateway.
            port: The port for TWS/IB Gateway.
            clientId: The client ID for the connection.
        """
        self.events = events
        self.ib = IB()
        try:
            self.ib.connect(host, port, clientId)
        except Exception as e:
            print(f"Failed to connect to IBKR: {e}")
            print("Please ensure TWS or IB Gateway is running and the connection parameters are correct.")
            raise

        self.symbol_data: dict[str, pd.DataFrame] = {}
        self.latest_symbol_data: dict[str, list] = {}
        self.continue_backtest = True

    def fetch_historical_data(self, symbol: str, durationStr='1 Y', barSizeSetting='1 day', whatToShow='TRADES'):
        """
        Fetches historical bar data for a specified contract.

        Args:
            symbol: The stock symbol (e.g., 'AAPL').
            durationStr: The duration of the data to fetch (e.g., '1 Y', '1 M', '1 D').
            barSizeSetting: The bar size (e.g., '1 min', '1 hour', '1 day').
            whatToShow: The type of data to fetch (e.g., 'TRADES', 'MIDPOINT', 'BID', 'ASK').
        """
        contract = Stock(symbol, 'SMART', 'USD')
        bars = self.ib.reqHistoricalData(
            contract,
            endDateTime='',
            durationStr=durationStr,
            barSizeSetting=barSizeSetting,
            whatToShow=whatToShow,
            useRTH=True
        )
        self.symbol_data[symbol] = util.df(bars)
        self.latest_symbol_data[symbol] = []

    def stream_next_bar(self):
        """
        Iterates through the fetched bars, converts each bar into a MarketEvent,
        and places it onto the event queue.
        This is a generator that yields each bar.
        """
        for symbol, data in self.symbol_data.items():
            for bar in data.itertuples():
                self.latest_symbol_data[symbol].append(bar)
                self.events.put(MarketEvent())
                yield

    def get_latest_bar_datetime(self, symbol: str):
        """
        Returns the datetime of the latest bar.
        """
        if self.latest_symbol_data.get(symbol):
            return self.latest_symbol_data[symbol][-1].date
        return None

    def get_latest_bar_value(self, symbol: str, val_type: str):
        """
        Returns a specific value (e.g., 'close') of the latest bar.
        """
        if self.latest_symbol_data.get(symbol):
            return getattr(self.latest_symbol_data[symbol][-1], val_type.lower())
        return None

    def disconnect(self):
        """
        Disconnects from IBKR.
        """
        self.ib.disconnect()