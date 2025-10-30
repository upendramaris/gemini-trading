import datetime
from backtester.events import FillEvent, OrderEvent

class SimulatedExecutionHandler:
    """
    The simulated execution handler simply converts all order objects into their equivalent fill objects without
    considering slippage or latency. This allows a straightforward first-pass backtest.
    """

    def __init__(self, events):
        """
        Initialises the handler, setting the event queue to an empty list.
        """
        self.events = events

    def execute_order(self, event):
        """
        Simply converts Order objects into Fill objects naively, i.e. without any latency, slippage or fill ratio problems.
        Parameters:
        event - Contains an Event object with order information.
        """
        if event.type == 'ORDER':
            fill_event = FillEvent(
                datetime.datetime.utcnow(), event.symbol, 'ARCA', event.quantity, event.direction, None
            )
            self.events.put(fill_event)