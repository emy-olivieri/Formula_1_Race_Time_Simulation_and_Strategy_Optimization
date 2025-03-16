import pandas as pd

class Evaluation:
    """
    Classe mère pour l'évaluation statistique.
    Elle stocke les données réelles et simulées et impose l'implémentation
    d'une méthode evaluate() dans les classes filles.
    """
    def __init__(self, actual_data: pd.Series, simulated_data: pd.Series):
        self.actual_data = actual_data
        self.simulated_data = simulated_data

    def evaluate(self):
        raise NotImplementedError("Les classes filles doivent implémenter la méthode evaluate().")
