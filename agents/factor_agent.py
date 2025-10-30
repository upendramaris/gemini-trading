import ast
import difflib
import json
from typing import Optional

from utils.llm_client import LLMClient

class FactorAgent:
    """
    The FactorAgent class is responsible for constructing a formulaic alpha from a structured market hypothesis.
    It also applies regularization to control complexity and enforce originality.
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client
        self.common_factors = [
            'Rank(close)',
            'RSI(close)',
            'ts_delta(close, 10)',
            'Correlation(close, volume, 20)'
        ]

    def _get_ast_depth(self, node):
        """
        Recursively calculates the depth of an AST node.
        """
        if not isinstance(node, ast.AST):
            return 0
        
        max_depth = 0
        for child_node in ast.iter_child_nodes(node):
            max_depth = max(max_depth, self._get_ast_depth(child_node))
            
        return max_depth + 1

    def _check_complexity(self, formula: str) -> bool:
        """
        Checks the complexity of the formula.
        A formula is considered too complex if its depth is greater than 7 or it has more than 5 parameters.
        """
        try:
            tree = ast.parse(formula)
            depth = self._get_ast_depth(tree)
            
            num_params = 0
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    num_params += len(node.args)

            if depth > 7 or num_params > 5:
                print(f"Complexity check failed: depth={depth}, params={num_params}")
                return False
            return True
        except SyntaxError:
            return False

    def _check_originality(self, formula: str) -> bool:
        """
        Checks the originality of the formula by comparing its AST to a list of common factors.
        """
        for common_factor in self.common_factors:
            similarity = difflib.SequenceMatcher(None, formula, common_factor).ratio()
            if similarity > 0.8:
                print(f"Originality check failed: similar to {common_factor} with similarity {similarity:.2f}")
                return False
        return True

    def construct_factor(self, hypothesis: dict) -> str:
        """
        Constructs a formulaic alpha from a structured market hypothesis.

        Args:
            hypothesis: A dictionary representing the structured market hypothesis.

        Returns:
            A string representing the formulaic alpha, or an error message if regularization checks fail.
        """
        # This is a simplified implementation. In a real-world scenario, this method would use an LLM to generate the formula.
        # For this example, we will use a predefined formula based on the hypothesis.

        formula: Optional[str] = None

        if self.llm and self.llm.is_available():
            try:
                formula = self._generate_with_llm(hypothesis)
            except Exception as exc:
                print(f"LLM factor generation failed, falling back to heuristics: {exc}")

        if not formula:
            hypothesis_text = " ".join(str(value).lower() for value in hypothesis.values())

            if "breakout" in hypothesis_text and "momentum" in hypothesis_text:
                formula = "Rank(ts_delta(close, 20) - ts_delta(close, 5))"
            elif "order flow" in hypothesis_text and "imbalance" in hypothesis_text:
                formula = "Rank(ts_delta(close, 1) * volume)"
            elif "mean reversion" in hypothesis_text or "revert" in hypothesis_text:
                formula = "-Rank(ts_delta(close, 5))"
            else:
                formula = "Rank(ts_delta(close, 7) - ts_delta(close, 30))"

        if not self._check_complexity(formula):
            return "Error: Formula is too complex."

        if not self._check_originality(formula):
            return "Error: Formula is not original enough."

        return formula

    def _generate_with_llm(self, hypothesis: dict) -> str:
        system_prompt = (
            "You are a quantitative researcher who writes concise alpha factors. "
            "Return a single Python expression using helper functions such as Rank, ts_delta, Correlation, "
            "SMA, EMA, and data series like close, open, high, low, volume."
        )
        hypothesis_json = json.dumps(hypothesis, indent=2)
        user_prompt = (
            "Hypothesis:\n"
            f"{hypothesis_json}\n\n"
            "Produce a single-line factor expression (no code fences, no explanation)."
        )
        expression = self.llm.chat(system_prompt, user_prompt).strip()
        return expression.splitlines()[0].strip()
