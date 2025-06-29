import numpy as np
from evaluation import Evaluation


class MAEEvaluation(Evaluation):
    """
    Class for evaluating the Mean Absolute Eroor (MAE) between simulated and actual data.
    Inherits from the abstract `Evaluation` base class.
    """
    def evaluate(self):

        mae = np.mean(np.abs(self.simulated_data - self.actual_data))
        print("\n=== MAE for Cumulative Times ===")
        print(f"MAE: {mae:.4f}")
        return mae