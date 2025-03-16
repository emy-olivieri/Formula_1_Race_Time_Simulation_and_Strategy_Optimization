# fuel_and_tire_model.py
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from model import Model

class FuelAndTireModel(Model):
    """
    Modèle pour estimer les temps au tour en fonction du carburant, du composé de pneus, etc.
    Utilise une régression OLS avec vectorisation et met en cache le modèle ajusté.
    """
    ALL_COMPOUNDS = ["A1", "A2", "A3", "A4", "A6", "A7", "I", "W"]
    # Cache pour stocker le modèle ajusté (clé = (driver_id, race_id, season))
    cache = {}

    def __init__(self, season: int, driver_id: int, race_id: int, dataframes: dict):
        self.season = season
        self.driver_id = driver_id
        self.race_id = race_id
        self.dfs_local = {n: df.copy() for n, df in dataframes.items()}
        self.best_qualif_times = pd.DataFrame()
        self.laps_df = pd.DataFrame()
        self.train_data = pd.DataFrame()
        self.test_data = pd.DataFrame()
        self.model = None
        self.variability = None
        self.is_fitted = False

    def fit(self):
        key = (self.driver_id, self.race_id, self.season)
        # Si le modèle est en cache, on le récupère directement
        if key in FuelAndTireModel.cache:
            cached = FuelAndTireModel.cache[key]
            self.model = cached["model"]
            self.variability = cached["variability"]
            self.is_fitted = True
            return

        self._clean_data()
        self._get_best_qualif_time()
        self._add_features()
        self._clean_to_regression()
        self._split_train_test()
        self._regression()

        self.variability = np.std(self.model.resid)
        self.is_fitted = True

        FuelAndTireModel.cache[key] = {"model": self.model, "variability": self.variability}

    def predict(self, features: pd.DataFrame) -> pd.Series:
        if not self.is_fitted:
            raise RuntimeError("FuelAndTireModel n'a pas été ajusté.")
        return self.model.predict(features)

    def _clean_data(self):
        laps_df = self.dfs_local["laps"]
        races_df = self.dfs_local["races"]
        starterfields_df = self.dfs_local["starterfields"]
        fcyphases_df = self.dfs_local["fcyphases"]

        race_ids_season = races_df[races_df["season"] == self.season]["id"]
        laps_df = laps_df[(laps_df["driver_id"] == self.driver_id) & (laps_df["race_id"].isin(race_ids_season))]

        starterfields_df = starterfields_df[(starterfields_df["driver_id"] == self.driver_id) & (starterfields_df["race_id"].isin(race_ids_season))]
        finished_races = starterfields_df[starterfields_df["status"] == "F"]
        laps_df = laps_df[laps_df["race_id"].isin(finished_races["race_id"])]

        # Suppression des phases de sécurité (Safety Car / VSC)
        fcyphases_df = fcyphases_df[fcyphases_df["race_id"].isin(race_ids_season)]
        for _, row in fcyphases_df.iterrows():
            begin = row["startlap"]
            end = row["endlap"]
            laps_df = laps_df[~((laps_df["race_id"] == row["race_id"]) & (laps_df["lapno"].between(begin, end)))]
        
        laps_df = laps_df.reset_index(drop=True)
        pit_in_index = laps_df[~laps_df["pitintime"].isna()].index
        pit_out_index = [i + 1 for i in pit_in_index]
        laps_df = laps_df[~laps_df.index.isin(list(pit_in_index) + pit_out_index)]

        self.laps_df = laps_df

    def _get_best_qualif_time(self):
        if self.laps_df.empty:
            raise RuntimeError("Aucune donnée de laps disponible après nettoyage.")
        qualif_laps_df = self.dfs_local["qualifyings"]
        valid_race_ids = self.laps_df["race_id"].unique()
        qualif_laps_df = qualif_laps_df[(qualif_laps_df["driver_id"] == self.driver_id) & (qualif_laps_df["race_id"].isin(valid_race_ids))]
        best_qualif_times = (
            qualif_laps_df[["race_id", "q1laptime", "q2laptime", "q3laptime"]]
            .groupby("race_id").min().min(axis=1)
        )
        self.best_qualif_times = pd.DataFrame(best_qualif_times, columns=["best_qualif_time"])
        self.laps_df = self.laps_df.merge(self.best_qualif_times, on="race_id", how="left")

    def _add_features(self):
        if self.laps_df.empty:
            raise RuntimeError("Aucune donnée de laps pour ajouter des features.")
        laps_df = self.laps_df.copy()
        laps_df["fuelc"] = 100 - (100 / laps_df.groupby("race_id")["lapno"].transform("max")) * laps_df["lapno"]
        self.laps_df = laps_df

    def _clean_to_regression(self):
        if self.laps_df.empty:
            raise RuntimeError("Aucune donnée de laps pour préparation de la régression.")
        required_features = ["laptime", "best_qualif_time", "fuelc", "compound", "tireage"]
        self.laps_df["corrected_lap_time"] = self.laps_df["laptime"] - self.laps_df["best_qualif_time"]
        self.laps_df["compound"] = pd.Categorical(self.laps_df["compound"], categories=self.ALL_COMPOUNDS)
        self.laps_df.dropna(subset=required_features, inplace=True)

    def _split_train_test(self):
        if self.laps_df.empty:
            raise RuntimeError("Aucune donnée de laps pour split train/test.")
        start_race_id = np.min(self.laps_df["race_id"])
        self.train_data = self.laps_df[self.laps_df["race_id"].between(start_race_id, self.race_id - 1)]
        self.test_data = self.laps_df[self.laps_df["race_id"] == self.race_id]

    def _regression(self):
        formula = "corrected_lap_time ~ fuelc + C(compound) + tireage"
        self.model = smf.ols(formula=formula, data=self.train_data).fit()
