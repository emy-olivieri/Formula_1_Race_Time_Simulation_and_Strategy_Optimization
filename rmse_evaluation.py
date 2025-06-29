import numpy as np
from evaluation import Evaluation


class RMSEEvaluation(Evaluation):
    """
    Class for evaluating the Root Mean Square Error (RMSE) between simulated and actual data.
    Inherits from the abstract `Evaluation` base class.
    """
    def evaluate(self):
        # MSE = mean((sim - actual)^2)
        mse = np.mean((self.simulated_data - self.actual_data) ** 2)
        rmse = np.sqrt(mse)
        print("\n=== RMSE for Cumulative Times ===")
        print(f"RMSE: {rmse:.4f}")
        return rmse
