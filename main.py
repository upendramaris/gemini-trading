import queue
import json
from ib_insync import Stock  # type: ignore[import-not-found]
from dotenv import load_dotenv
from agents.idea_agent import IdeaAgent
from agents.factor_agent import FactorAgent
from agents.eval_agent import EvalAgent
from backtester.data_handler import IBKRDataHandler
from utils.llm_client import LLMClient

def main():
    """
    Main orchestration loop for the AlphaAgent framework.
    """
    load_dotenv()
    llm_client = LLMClient()

    # 1. Initialize the event queue and the IBKRDataHandler
    events = queue.Queue()
    # Make sure you have TWS or IB Gateway running
    try:
        data_handler = IBKRDataHandler(events, host='127.0.0.1', port=7497, clientId=1)
    except Exception as e:
        print(f"Could not connect to IBKR: {e}")
        return

    try:
        # 2. Define an ib_insync contract object
        contract = Stock('ES', 'SMART', 'USD')
        data_handler.symbol_list = [contract.symbol]
        data_handler.fetch_historical_data(contract.symbol)

        # 3. Instantiate the agents
        idea_agent = IdeaAgent(llm_client=llm_client)
        factor_agent = FactorAgent(llm_client=llm_client)
        eval_agent = EvalAgent()

        # 4. Prompt the user for an initial trading idea
        user_idea = input("Please enter your trading idea: ")

        best_factor = None
        best_performance = {"Sharpe Ratio": -1000}

        # 5. Start a loop for a fixed number of iterations
        for i in range(5):
            print(f"\n----- Iteration {i+1} -----")

            # 6a. The IdeaAgent refines the idea into a hypothesis
            print("IdeaAgent: Refining the idea...")
            hypothesis_json = idea_agent.propose_hypothesis(user_idea)
            hypothesis = json.loads(hypothesis_json)
            print(f"Hypothesis: {hypothesis['Argument']}")

            # 6b. The FactorAgent constructs a formulaic alpha
            print("FactorAgent: Constructing a factor...")
            factor_code = factor_agent.construct_factor(hypothesis)
            if "Error" in factor_code:
                print(f"FactorAgent Error: {factor_code}")
                user_idea += " The previous formula was not good. Let's try a different approach."
                continue
            print(f"Factor: {factor_code}")

            # 6c. The EvalAgent backtests the alpha
            print("EvalAgent: Evaluating the factor...")
            eval_result = eval_agent.evaluate_factor(factor_code, data_handler)
            print(f"Performance: {eval_result['performance_metrics']}")
            print(f"Feedback: {eval_result['feedback']}")

            # 6d. Print the best-performing factor so far
            current_sharpe = 0
            for metric in eval_result['performance_metrics']:
                if metric[0] == "Sharpe Ratio":
                    current_sharpe = float(metric[1])
            
            if current_sharpe > best_performance["Sharpe Ratio"]:
                best_performance["Sharpe Ratio"] = current_sharpe
                best_factor = factor_code
                print(f"New best factor found: {best_factor} with Sharpe Ratio: {current_sharpe}")

            # 6e. Use the feedback to refine the initial idea
            user_idea += f" {eval_result['feedback']}"

        # 7. Output the final, best-performing alpha factor
        print("\n----- Final Result -----")
        print(f"Best performing factor: {best_factor}")
        print(f"Best performance (Sharpe Ratio): {best_performance['Sharpe Ratio']}")

    finally:
        # Ensure the connection to IBKR is properly disconnected
        print("\nDisconnecting from IBKR...")
        data_handler.disconnect()

if __name__ == "__main__":
    main()
