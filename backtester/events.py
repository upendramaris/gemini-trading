class Event:
    """
    Base class for all events.
    """
    pass

class MarketEvent(Event):
    """
    Handles the event of receiving new market data.
    """
    def __init__(self):
        self.type = 'MARKET'

class SignalEvent(Event):
    """
    Handles the event of sending a signal from a Strategy object.
    This is received by a Portfolio object and acted upon.
    """
    def __init__(self, symbol, datetime, signal_type):
        self.type = 'SIGNAL'
        self.symbol = symbol
        self.datetime = datetime
        self.signal_type = signal_type # 'LONG' or 'SHORT'

class OrderEvent(Event):
    """
    Handles the event of sending an Order to an execution system.
    The order contains a symbol (e.g. GOOG), a type (market or limit),
    quantity and a direction.
    """
    def __init__(self, symbol, order_type, quantity, direction):
        self.type = 'ORDER'
        self.symbol = symbol
        self.order_type = order_type
        self.quantity = quantity
        self.direction = direction # 'BUY' or 'SELL'

    def print_order(self):
        print(f"Order: Symbol={self.symbol}, Type={self.order_type}, Quantity={self.quantity}, Direction={self.direction}")

class FillEvent(Event):
    """
    Encapsulates the notion of a filled order, as returned from a brokerage.
    Stores the quantity of an instrument actually filled and at what price.
    In addition, stores the commission of the trade from the brokerage.
    """
    def __init__(self, timeindex, symbol, exchange, quantity, direction, fill_cost, commission=None):
        self.type = 'FILL'
        self.timeindex = timeindex
        self.symbol = symbol
        self.exchange = exchange
        self.quantity = quantity
        self.direction = direction
        self.fill_cost = fill_cost

        # Calculate commission
        if commission is None:
            self.commission = self.calculate_ib_commission()
        else:
            self.commission = commission

    def calculate_ib_commission(self):
        """
        Calculates the fees of trading based on an Interactive Brokers fee structure for API, in USD.
        This does not include exchange or ECN fees.
        Based on https://www.interactivebrokers.com/en/index.php?f=1590&p=stocks2
        """
        full_cost = 1.3
        if self.quantity <= 500:
            full_cost = max(1.3, 0.013 * self.quantity)
        else: # Greater than 500
            full_cost = max(1.3, 0.008 * self.quantity)
        return full_cost