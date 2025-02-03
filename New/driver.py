# -*- coding: utf-8 -*-
## Add tire_age in pit_stop_strategy option to take 
## into account not new tires

"""
driver.py

Defines the Driver class. Each driver references their team, uses DNFModel
and FuelAndTireModel (both inherit from Model), and has logic for
pit stops, DNF, etc.
"""

import numpy as np
import pandas as pd

from dnf_model import DNFModel
from fuel_and_tire_model import FuelAndTireModel
from team import TeamRegistry


class Driver:
    """
    Represents an individual driver. Holds references to season, data, team,
    and logic for simulation (pit stops, DNF, etc.).
    """

    def __init__(self, season: int, race_id: int, dataframes: dict, name: str, strategy):
        """
        Initialize the driver with the provided information and models.

        Args:
            season (int): The current season.
            race_id (int): The race ID to analyze.
            dataframes (dict): Dictionary of DataFrames from the database.
            name (str): Driver's name (must match entry in "drivers" table).
        """
        self.season = season
        self.dataframes = dataframes
        self.name = name
        self.driver_id = None
        self.initials = None
        self.team = None

        # Simulation attributes
        self.position = None
        self.best_qualif_time= None
        self.current_lap_time = None
        self.cumulative_lap_time = 0

        self.fuelc = 100
        self.next_pit_stop = 1
        # Pit stop strategy
        if strategy :
            self.pit_stops_info = strategy
        else: 
            self.pit_stops_info = None
                            
        self.compound = self.pit_stops_info["starting_compound"]
        self.tire_age = self.pit_stops_info["starting_tire_age"]

        # DNF attributes
        self.accident_dnf_probability = None
        self.failure_dnf_probability = None
        self.accident_dnf_lap = None
        self.failure_dnf_lap = None
        self.earliest_dnf_lap = None
        self.alive = True

        # Fuel & Tire Model
        self.fuel_tire_model = None
        self.variability = None

        # Initialize parameters
        self._get_driver_parameters(race_id)

    def _get_driver_parameters(self, race_id):
        """
        Retrieve driver/team info, DNF probabilities, and
        build the FuelAndTireModel for the driver.
        """
        drivers_df = self.dataframes["drivers"].copy()
        starterfields_df = self.dataframes["starterfields"].copy()
        races_df = self.dataframes["races"].copy()

        # Find driver ID
        driver_row = drivers_df[drivers_df["name"] == self.name]
        if driver_row.empty:
            raise ValueError(f"Driver '{self.name}' not found in 'drivers' table.")

        self.driver_id = driver_row.iloc[0]["id"]
        self.initials = driver_row.iloc[0]["initials"]

        # Get best qualif time 
        qualif_laps_df = self.dataframes["qualifyings"]
        qualif_laps_df_for_driver = qualif_laps_df[
            (qualif_laps_df["driver_id"] == self.driver_id)
            & (qualif_laps_df["race_id"]==race_id)
        ].copy()
       
        self.best_qualif_time = (qualif_laps_df_for_driver[["race_id", "q1laptime", "q2laptime", "q3laptime"]]
            .groupby("race_id")
            .min()
            .min(axis=1)
            .reset_index(drop=True).iloc[0]
                )
        if np.isnan(self.best_qualif_time):
            qualif_laps_df = qualif_laps_df[
             (qualif_laps_df["race_id"]==race_id)
        ]  

            self.best_qualif_time = (qualif_laps_df[["race_id", "q1laptime", "q2laptime", "q3laptime"]]
                .groupby("race_id")
                .min()
                .mean(axis=1)
                .reset_index(drop=True).iloc[0]
                    )
        # Merge to get the team for this season
        merged_data = starterfields_df.merge(
            races_df, left_on="race_id", right_on="id", suffixes=("_sf", "_races")
        )
        team_row = merged_data[
            (merged_data["driver_id"] == self.driver_id)
            & (merged_data["season"] == self.season)
        ]
        if not team_row.empty:
            team_name = team_row.iloc[0]["team"]
            self.team = TeamRegistry.get_team(team_name)

        # 1) DNFModel usage
        dnf_model = DNFModel(self.dataframes)
        dnf_model.fit(driver=self, season=self.season)
        (acc_prob, fail_prob) = dnf_model.predict()
        self.accident_dnf_probability = acc_prob
        self.failure_dnf_probability = fail_prob

        # 2) FuelAndTireModel usage
        fuel_tire_model_obj = FuelAndTireModel(
            season=self.season,
            driver_id=self.driver_id,
            race_id=race_id,
            dataframes=self.dataframes,
        )
        # Fit the model pipeline
        fuel_tire_model_obj.fit()
        # Store references in the Driver
        self.fuel_tire_model = fuel_tire_model_obj
        self.variability = fuel_tire_model_obj.variability

        
    def update_status(self, current_lap: int):
        """
        If the driver's earliest_dnf_lap equals the current lap,
        mark the driver as not alive (DNF).
        """
        if self.alive and self.earliest_dnf_lap == current_lap:
            self.alive = False

    def update_info(self, current_lap: int, total_laps: int):
        """
        Increment tire wear and update fuel based on the current lap.
        """
        self.tire_age += 1
        self.fuelc = 100 - (100.0 / total_laps) * current_lap
