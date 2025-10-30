import queue
import numpy as np
import pandas as pd
from backtester.portfolio import Portfolio
from backtester.execution import SimulatedExecutionHandler
from backtester.events import SignalEvent, MarketEvent

# Helper functions for factor evaluation
def Rank(df):
    return df.rank(axis=1, pct=True)

def ts_delta(df, period=1):
    return df.diff(period)

class EvalAgent:
    """
    The EvalAgent class is responsible for evaluating a factor by running a backtest and generating feedback.
    """

    def _apply_factor(self, factor_code: str, data: pd.DataFrame) -> pd.DataFrame | None:
        """
        Applies the factor to the historical data.
        This is a simplified and unsafe implementation using eval.
        In a real-world scenario, a safer parsing and execution mechanism should be used.
        """
        try:
            # For simplicity, we assume the data has a 'Close' column
            close = data['Close']
            # The factor code is evaluated in the context of the helper functions
            factor_values = eval(factor_code, globals(), {'close': close})
            return factor_values
        except Exception as e:
            print(f"Error applying factor: {e}")
            return None

    def evaluate_factor(self, factor_code: str, data_handler) -> dict:
        """
        Evaluates a factor by running a backtest and generating feedback.

        Args:
            factor_code: A string representing the formulaic alpha.
            data_handler: An instance of a data handler class.

        Returns:
            A dictionary containing performance metrics and LLM-generated feedback.
        """
        events: queue.Queue = queue.Queue()
        bars = data_handler
        start_date = data_handler.symbol_data[data_handler.symbol_list[0]].index[0]
        portfolio = Portfolio(bars, events, start_date, initial_capital=100000.0)
        broker = SimulatedExecutionHandler(events)

        # Get all data for factor calculation
        all_data = {}
        for symbol in data_handler.symbol_list:
            all_data[symbol] = pd.DataFrame(data_handler.symbol_data[symbol], columns=data_handler.symbol_data[symbol].columns)
        
        # This is a simplification. In a real backtest, you would get data bar by bar.
        # For factor evaluation, we often need the full history at once.
        # We will assume a single dataframe with all symbols for this example.
        # This part of the code needs to be adapted to the actual data format.
        # For now, we will skip the data transformation and assume a single dataframe.
        
        # --- This is a placeholder for the backtesting loop ---
        # In a real implementation, you would have a loop that processes events
        # and updates the portfolio.
        # For this example, we will generate some dummy results.

        # 1. Apply the factor (dummy implementation)
        # factor_values = self._apply_factor(factor_code, all_data_df)

        # 2. Generate signals (dummy implementation)
        # signals = self._generate_signals(factor_values)

        # 3. Run backtest (dummy implementation)
        # The backtest loop would process MarketEvents, generate SignalEvents,
        # which are then converted to OrderEvents and FillEvents.
        # This is a complex process that is already partially implemented in the backtester module.
        # For this example, we will just create some dummy stats.

        # Create dummy equity curve
        dummy_returns = np.random.rand(100) * 0.01 - 0.005
        dummy_equity_curve = (1 + dummy_returns).cumprod()
        
        # Create a dummy portfolio to generate stats
        class DummyPortfolio:
            def __init__(self):
                self.equity_curve = pd.DataFrame({'equity_curve': dummy_equity_curve, 'returns': dummy_returns})
            def output_summary_stats(self):
                return [("Total Return", "10.50%"), ("Sharpe Ratio", "1.5"), ("Max Drawdown", "5.20%"), ("Drawdown Duration", "10")]

        dummy_portfolio = DummyPortfolio()
        performance_metrics = dummy_portfolio.output_summary_stats()

        # 4. Generate feedback
        feedback = self._generate_feedback(performance_metrics)

        return {
            "performance_metrics": performance_metrics,
            "feedback": feedback
        }

    def _generate_feedback(self, performance_metrics: list) -> str:
        """
        Generates feedback based on the backtest results.
        This is a simplified implementation that simulates an LLM's feedback.
        """
        sharpe_ratio: float = 0.0
        for metric in performance_metrics:
            if metric[0] == "Sharpe Ratio":
                sharpe_ratio = float(metric[1])

        if sharpe_ratio > 1.0:
            return "The factor shows promising performance with a good Sharpe Ratio. Consider testing it on a wider range of assets or timeframes."
        elif sharpe_ratio > 0.5:
            return "The factor has moderate performance. Consider refining the formula to improve the risk-adjusted returns. Perhaps a different time window for the ts_delta operator could be beneficial."
        else:
            return "The factor's performance is poor. The Sharpe Ratio is low, indicating a high level of risk for the returns generated. It is recommended to significantly revise the factor formula. Consider incorporating other data sources like volume or volatility."