# -*- coding: utf-8 -*-
"""
fuel_and_tire_model.py

Defines a class that estimates lap times based on fuel load, tire compound, etc.,
inheriting from the abstract base class `Model`.
"""

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from model import Model


class FuelAndTireModel(Model):
    """
    Refactored class to avoid destructive modifications of shared DataFrames
    and to handle tire compound categories explicitly.
    Inherits from the abstract `Model` base class.
    """

    # Un df 
    # Les Courses non modélisables doivent etre ajoutées dans un df et récupérer

    ALL_COMPOUNDS = ["A1", "A2", "A3", "A4", "A6", "A7", "I", "W"]

    def __init__(self, season: int, driver_id: int, race_id: int, dataframes: dict):
        """
        Args:
            season (int): Target season.
            driver_id (int): Driver ID.
            race_id (int): Target race ID for the test.
            dataframes (dict): Dictionary of DataFrames (locally copied).
        """
        self.season = season
        self.driver_id = driver_id
        self.race_id = race_id

        # Local copy to avoid altering the original DataFrames
        self.dfs_local = {n: df.copy() for n, df in dataframes.items()}

        # Internal attributes
        self.best_qualif_times = pd.DataFrame()
        self.laps_df = pd.DataFrame()
        self.train_data = pd.DataFrame()
        self.test_data = pd.DataFrame()
        self.model = None
        self.variability = None

        # Fit check
        self.is_fitted = False

    # -------------------------------------------------------------------
    # Implement the abstract Model interface
    # -------------------------------------------------------------------
    def fit(self):
        """
        Full pipeline to clean data, build a regression model,
        and compute residual variability.
        """
        self._clean_data()
        self._get_best_qualif_time()
        self._add_features()
        self._clean_to_regression()
        self._split_train_test()
        self._regression()

        # Standard deviation of residuals => measure of variability
        self.variability = np.std(self.model.resid)
        self.is_fitted = True

    def predict(self, features: pd.DataFrame) -> pd.Series:
        """
        Predict or compute lap times using the fitted OLS model.

        Args:
            features (pd.DataFrame): Must contain at least 'fuelc', 'compound', 'tireage'.

        Returns:
            pd.Series: Predicted lap times for each row in `features`.
        """
        if not self.is_fitted:
            raise RuntimeError("FuelAndTireModel has not been fitted yet. Call `fit()` first.")

        return self.model.predict(features)

    # -------------------------------------------------------------------
    # Private pipeline methods (unchanged in logic, just underscore-named)
    # -------------------------------------------------------------------
    def _clean_data(self):
        """
        Apply various filters (finished races, exclude rain, safety car laps,
        pit stops) and store the result in self.laps_df.
        """
        laps_df = self.dfs_local["laps"]
        races_df = self.dfs_local["races"]
        starterfields_df = self.dfs_local["starterfields"]
        fcyphases_df = self.dfs_local["fcyphases"]

        # Filter laps for this driver in the specified season
        race_ids_season = races_df[races_df["season"] == self.season]["id"]
        laps_df = laps_df[
            (laps_df["driver_id"] == self.driver_id)
            & (laps_df["race_id"].isin(race_ids_season))
        ]

        # Keep only races the driver actually finished (status == "F")
        starterfields_df = starterfields_df[
            (starterfields_df["driver_id"] == self.driver_id)
            & (starterfields_df["race_id"].isin(race_ids_season))
        ]
        finished_races = starterfields_df[starterfields_df["status"] == "F"]
        laps_df = laps_df[laps_df["race_id"].isin(finished_races["race_id"])]

        # Exclude rainy races by location (example logic)
        rainy_races = ["Budapest", "SaoPaulo"]
        rainy_race_ids = races_df[races_df["location"].isin(rainy_races)]["id"]
        laps_df = laps_df[~laps_df["race_id"].isin(rainy_race_ids)]

        # Exclude laps under Safety Car or Virtual Safety Car (from fcyphases)
        fcyphases_df = fcyphases_df[fcyphases_df["race_id"].isin(race_ids_season)]
        for _, row in fcyphases_df.iterrows():
            begin = row["startlap"]
            end = row["endlap"]
            laps_df = laps_df[
                ~(
                    (laps_df["race_id"] == row["race_id"])
                    & (laps_df["lapno"].between(begin, end))
                )
            ]

        # Exclude laps with pit stop and the immediate next lap
        laps_df = laps_df.reset_index(drop=True)
        pit_in_index = laps_df[~laps_df["pitintime"].isna()].index
        pit_out_index = [i + 1 for i in pit_in_index]
        laps_df = laps_df[~laps_df.index.isin(list(pit_in_index) + pit_out_index)]

        self.laps_df = laps_df

    def _get_best_qualif_time(self):
        """
        Compute the best qualifying time (min of Q1, Q2, Q3) for each race,
        then merge into self.laps_df as 'best_qualif_time'.
        """
        if self.laps_df.empty:
            raise RuntimeError("self.laps_df is empty. _clean_data() not called or no data left.")

        qualif_laps_df = self.dfs_local["qualifyings"]
        valid_race_ids = self.laps_df["race_id"].unique()

        # Restrict to this driver + relevant races
        qualif_laps_df = qualif_laps_df[
            (qualif_laps_df["driver_id"] == self.driver_id)
            & (qualif_laps_df["race_id"].isin(valid_race_ids))
        ]

        # Minimum among Q1, Q2, Q3
        best_qualif_times = (
            qualif_laps_df[["race_id", "q1laptime", "q2laptime", "q3laptime"]]
            .groupby("race_id")
            .min()
            .min(axis=1)
        )
        self.best_qualif_times = pd.DataFrame(
            best_qualif_times, columns=["best_qualif_time"]
        )

        self.laps_df = self.laps_df.merge(
            self.best_qualif_times, on="race_id", how="left"
        )

    def _add_features(self):
        """
        Example feature addition: estimate 'fuelc' as a linear drop
        from 100 to 0 across the total laps in each race.
        """
        if self.laps_df.empty:
            raise RuntimeError("self.laps_df is empty. Make sure earlier steps ran.")

        laps_df = self.laps_df.copy()

        # Simple example of fuel usage
        laps_df["fuelc"] = (
            100
            - (100 / laps_df.groupby("race_id")["lapno"].transform("max"))
            * laps_df["lapno"]
        )

        self.laps_df = laps_df

    def _clean_to_regression(self):
        """
        Prepare the 'corrected_lap_time' column and handle the 'compound'
        categorical variable with known categories.
        """
        if self.laps_df.empty:
            raise RuntimeError("self.laps_df is empty. Ensure prior steps ran.")

        required_features = [
            "laptime",
            "best_qualif_time",
            "fuelc",
            "compound",
            "tireage",
        ]

        # Subtract best qualifying time to get a "corrected" lap time
        self.laps_df["corrected_lap_time"] = (
            self.laps_df["laptime"] - self.laps_df["best_qualif_time"]
        )

        # Explicitly set the categories for 'compound'
        self.laps_df["compound"] = pd.Categorical(
            self.laps_df["compound"],
            categories=self.ALL_COMPOUNDS
        )

        # Drop rows missing any required feature
        self.laps_df.dropna(subset=required_features, inplace=True)

    def _split_train_test(self):
        """
        Split into a training set (races in [start_race_id, race_id - 1])
        and a test set (race_id).
        """
        if self.laps_df.empty:
            raise RuntimeError("self.laps_df is empty. Make sure prior steps succeeded.")

        start_race_id = np.min(self.laps_df["race_id"])

        # Train: all races from earliest to (race_id-1)
        self.train_data = self.laps_df[
            self.laps_df["race_id"].between(start_race_id, self.race_id - 1)
        ]
        # Test: only the target race
        self.test_data = self.laps_df[self.laps_df["race_id"] == self.race_id]

    def _regression(self):
        """
        Train an OLS regression model on 'corrected_lap_time'
        with fuel, compound, and tire-age interactions.
        """
        formula = "corrected_lap_time ~ fuelc + C(compound) + C(compound):tireage"
        self.model = smf.ols(formula=formula, data=self.train_data).fit()
