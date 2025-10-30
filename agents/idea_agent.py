import json
from typing import Optional

from utils.llm_client import LLMClient

class IdeaAgent:
    """
    The IdeaAgent class is responsible for taking a user's trading idea and refining it into a structured market hypothesis.
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client

    def propose_hypothesis(self, user_input: str) -> str:
        """
        Takes a user's trading idea and refines it into a structured market hypothesis.

        Args:
            user_input: A string containing the user's trading idea.

        Returns:
            A JSON string representing the structured market hypothesis.
        """

        if self.llm and self.llm.is_available():
            system_prompt = (
                "You are a quantitative research assistant. "
                "Convert the user's trading idea into a structured JSON hypothesis with the keys: "
                "Observation, Knowledge, Argument, Specification. "
                "Each value should be a short paragraph."
            )
            user_prompt = (
                "Trading idea:\n"
                f"{user_input}\n\n"
                "Return only valid JSON."
            )
            try:
                hypothesis_dict = self.llm.chat_json(system_prompt, user_prompt)
                return json.dumps(hypothesis_dict, indent=4)
            except Exception as exc:
                print(f"LLM hypothesis generation failed, falling back to template: {exc}")

        # This is a simplified implementation. In a real-world scenario, this method would use an LLM to generate the hypothesis.
        # For this example, we will use a predefined structure based on the user's input.

        if "momentum after price breakouts" in user_input:
            hypothesis = {
                "Observation": "Prices of financial assets often exhibit momentum, continuing to move in the same direction after a significant price change, known as a breakout.",
                "Knowledge": "This phenomenon is often attributed to behavioral biases such as herding and confirmation bias, as well as the gradual dissemination of information in the market.",
                "Argument": "By identifying price breakouts, we can systematically enter positions in the direction of the breakout to capture the subsequent momentum.",
                "Specification": "A trading strategy will be developed to identify breakouts (e.g., price exceeding a 20-day high) and enter a long position, with a trailing stop-loss to manage risk."
            }
        elif "Order Flow Imbalance" in user_input:
            hypothesis = {
                "Observation": "Market microstructure data reveals that imbalances between buying and selling pressure at the micro-level often precede short-term price movements.",
                "Knowledge": "These imbalances, known as order flow imbalances, reflect the aggressive side of the market and can be a strong predictor of immediate price direction.",
                "Argument": "By using machine learning to model the relationship between order flow imbalances and price changes, we can create a predictive model for intraday scalping.",
                "Specification": "A model will be trained on historical order flow data to predict price movements. The model's predictions will be used to generate trading signals for a high-frequency scalping strategy."
            }
        else:
            # Generic hypothesis for other ideas
            hypothesis = {
                "Observation": f"The user has proposed an idea based on: {user_input}",
                "Knowledge": "Further research is needed to understand the underlying principles of this idea.",
                "Argument": "A trading strategy could be developed to test the validity of this idea.",
                "Specification": "The strategy will be backtested using historical data to evaluate its performance."
            }

        return json.dumps(hypothesis, indent=4)
