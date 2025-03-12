from evaluation import Evaluation
import numpy as np
from scipy.stats import wilcoxon


class WilcoxonEvaluation(Evaluation):
    """
    Classe fille pour appliquer le test de Wilcoxon
    afin de comparer les temps de course simulés aux temps réels.
    """
    def evaluate(self):
        differences = self.simulated_data - self.actual_data
        
        if np.all(differences == 0):
            print("Toutes les différences sont nulles, le test de Wilcoxon ne peut être appliqué.")
            return None, 1.0
        
        test_statistic, p_value = wilcoxon(differences)
        print("\n📊 Résultats du test de Wilcoxon:")
        print(f"Statistique de test : {test_statistic}")
        print(f"P-value : {p_value:.5f}")
        
        alpha = 0.05
        if p_value < alpha:
            print("❌ Rejet de H0 : Les temps simulés et réels diffèrent significativement.")
        else:
            print("✅ Non-rejet de H0 : Aucune différence significative entre les temps simulés et réels.")
            
        return test_statistic, p_value
