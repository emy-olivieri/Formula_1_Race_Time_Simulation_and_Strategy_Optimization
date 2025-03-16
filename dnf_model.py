# dnf_model.py
import numpy as np
from model import Model

class DNFModel(Model):
    """
    Modèle pour calculer les probabilités d'accident et d'échec (DNF) par pilote et saison.
    Utilise des opérations vectorisées pour les agrégations et met en cache les résultats.
    """
    # Cache pour stocker les résultats déjà calculés (clé = (driver_id, season))
    cache = {}

    def __init__(self, dataframes: dict):
        self.driver = None
        self.team = None
        self.season = None
        # Copie locale pour éviter des modifications destructrices
        self.dfs_local = {n: df.copy() for n, df in dataframes.items()}
        self.accident_probability = None
        self.failure_probability = None
        self.is_fitted = False

    def fit(self, driver, season):
        self.driver = driver
        self.team = self.driver.team
        self.season = season
        key = (self.driver.driver_id, self.season)
        # Si le résultat est en cache, on le récupère directement
        if key in DNFModel.cache:
            cached = DNFModel.cache[key]
            self.accident_probability = cached["accident_probability"]
            self.failure_probability = cached["failure_probability"]
            self.is_fitted = True
            return

        # Chargement des DataFrames nécessaires
        races_df = self.dfs_local["races"]
        starterfields_df = self.dfs_local["starterfields"]
        retirements_df = self.dfs_local["retirements"].fillna(0)
        # On considère ici la saison courante et les deux précédentes
        seasons_to_train = [self.season - x for x in range(3)]
        df_filtered = retirements_df[retirements_df['season'].isin(seasons_to_train)]

        # Calcul vectorisé du nombre de courses par pilote
        merged = starterfields_df[['race_id', 'driver_id']].merge(
            races_df[['id', 'season']], left_on='race_id', right_on='id', how='inner'
        )
        merged = merged[merged['season'].isin(seasons_to_train)]
        races_per_driver = merged.groupby('driver_id')['race_id'].count().rename("count_of_race")

        # Calcul vectorisé du nombre total d'accidents par pilote
        total_accidents = df_filtered.groupby('driver_id')['accidents'].sum().rename("total_accident")

        # Assemblage des résultats dans un DataFrame
        dnf_df = total_accidents.to_frame().join(races_per_driver, how='inner')
        dnf_df['accident_proportion'] = dnf_df['total_accident'] / dnf_df['count_of_race']

        # Calcul de la moyenne et de l'écart-type sur les pilotes ayant plus de 20 courses
        valid = dnf_df['count_of_race'] > 20
        mu_accident = dnf_df.loc[valid, 'accident_proportion'].mean()
        sigma_accident = dnf_df.loc[valid, 'accident_proportion'].std()

        # Calcul des hyperparamètres pour la distribution beta (prior)
        alpha_prior = ((1 - mu_accident) / sigma_accident**2 - 1 / mu_accident) * mu_accident**2
        beta_prior = alpha_prior * (1 / mu_accident - 1)
        dnf_df['alpha_posterior'] = dnf_df['total_accident'] + alpha_prior
        dnf_df['beta_posterior'] = dnf_df['count_of_race'] - dnf_df['total_accident'] + beta_prior

        # Calcul de la probabilité d'accident (espérance de la loi Beta)
        dnf_df['accident_proba'] = dnf_df['alpha_posterior'] / (dnf_df['alpha_posterior'] + dnf_df['beta_posterior'])

        # Récupération de la probabilité pour le pilote courant
        self.accident_probability = dnf_df.loc[self.driver.driver_id, 'accident_proba']
        # Pour l'exemple, on attribue une valeur fictive pour la probabilité d'échec
        self.failure_probability = 0.1

        # Stockage dans le cache
        DNFModel.cache[key] = {
            "accident_probability": self.accident_probability,
            "failure_probability": self.failure_probability
        }
        self.is_fitted = True

    def predict(self):
        if not self.is_fitted:
            raise RuntimeError("DNFModel n'a pas été ajusté. Veuillez appeler fit() d'abord.")
        return (self.accident_probability, self.failure_probability)
