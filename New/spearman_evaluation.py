from evaluation import Evaluation
from scipy.stats import spearmanr



class SpearmanEvaluation(Evaluation):
    """
    Classe fille pour appliquer le test de corrélation de Spearman
    afin de comparer les positions simulées aux positions réelles.
    """
    def evaluate(self):
        rs, p_value = spearmanr(self.actual_data, self.simulated_data)
        print("\n📊 Résultats du test de corrélation de Spearman:")
        print(f"Coefficient de corrélation (rs) : {rs:.4f}")
        print(f"P-value : {p_value:.5f}")
        
        alpha = 0.05
        if p_value < alpha:
            print("❌ Rejet de H0 : Les positions simulées et réelles sont significativement corrélées.")
        else:
            print("✅ Non-rejet de H0 : Aucune corrélation significative entre les positions simulées et réelles.")
            
        return rs, p_value
