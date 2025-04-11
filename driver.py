# driver.py
import numpy as np
import pandas as pd
from dnf_model import DNFModel
from fuel_and_tire_model import FuelAndTireModel
from team import TeamRegistry

class Driver:
    """
    Représente un pilote avec ses paramètres et modèles associés (DNF, Fuel/Tire).
    """
    def __init__(self, season: int, race_id: int, dataframes: dict, name: str, strategy):
        self.season = season
        self.dataframes = dataframes
        self.name = name
        self.driver_id = None
        self.initials = None
        self.team = None

        self.position = None
        self.best_qualif_time = None
        self.current_lap_time = None
        self.cumulative_lap_time = 0

        self.fuelc = 100
        self.next_pit_stop = 1
        self.pit_stops_info = strategy if strategy else {}
        self.compound = self.pit_stops_info.get("starting_compound", None)
        self.tire_age = self.pit_stops_info.get("starting_tire_age", None)

        self.accident_dnf_probability = None
        self.failure_dnf_probability = None
        self.accident_dnf_lap = None
        self.failure_dnf_lap = None
        self.earliest_dnf_lap = None
        self.alive = True

        self.fuel_tire_model = None
        self.variability = None

        self._get_driver_parameters(race_id)

    def _get_driver_parameters(self, race_id):
        drivers_df = self.dataframes["drivers"].copy()
        starterfields_df = self.dataframes["starterfields"].copy()
        races_df = self.dataframes["races"].copy()

        driver_row = drivers_df[drivers_df["name"] == self.name]
        if driver_row.empty:
            raise ValueError(f"Driver '{self.name}' non trouvé dans la table 'drivers'.")
        self.driver_id = driver_row.iloc[0]["id"]
        self.initials = driver_row.iloc[0]["initials"]

        qualif_laps_df = self.dataframes["qualifyings"]
        qualif_laps_df_for_driver = qualif_laps_df[
            (qualif_laps_df["driver_id"] == self.driver_id) & (qualif_laps_df["race_id"] == race_id)
        ].copy()
        self.best_qualif_time = (
            qualif_laps_df_for_driver[["race_id", "q1laptime", "q2laptime", "q3laptime"]]
            .groupby("race_id").min().min(axis=1)
            .reset_index(drop=True).iloc[0]
        )
        if np.isnan(self.best_qualif_time):
            qualif_laps_df = qualif_laps_df[qualif_laps_df["race_id"] == race_id]
            self.best_qualif_time = (
                qualif_laps_df[["race_id", "q1laptime", "q2laptime", "q3laptime"]]
                .groupby("race_id").min().mean(axis=1)
                .reset_index(drop=True).iloc[0]
            )

        merged_data = starterfields_df.merge(
            races_df, left_on="race_id", right_on="id", suffixes=("_sf", "_races")
        )
        team_row = merged_data[
            (merged_data["driver_id"] == self.driver_id) & (merged_data["season"] == self.season)
        ]
        if not team_row.empty:
            team_name = team_row.iloc[0]["team"]
            self.team = TeamRegistry.get_team(team_name)

        dnf_model = DNFModel(self.dataframes)
        dnf_model.fit(driver=self, season=self.season)
        (acc_prob, fail_prob) = dnf_model.predict()
        self.accident_dnf_probability = acc_prob
        self.failure_dnf_probability = fail_prob

        fuel_tire_model_obj = FuelAndTireModel(
            season=self.season,
            driver_id=self.driver_id,
            race_id=race_id,
            dataframes=self.dataframes,
        )
        fuel_tire_model_obj.fit()
        self.fuel_tire_model = fuel_tire_model_obj
        self.variability = fuel_tire_model_obj.variability

    def update_status(self, current_lap):
        """Ensure that drivers retire at the correct lap."""
        if self.earliest_dnf_lap is not None:
            if current_lap >= self.earliest_dnf_lap:  # DNF at this lap
                self.alive = False  # Stop the driver
                
    def update_info(self, current_lap: int, total_laps: int):
        self.tire_age += 1
        self.fuelc = max(self.fuelc - (100/total_laps), 0)
