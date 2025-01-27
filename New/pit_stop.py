# -*- coding: utf-8 -*-
"""
pit_stop.py

Manages pit stop logic for a given team, location, and season.
"""

import pandas as pd
from scipy.stats import fisk


class PitStop:
    """
    Manages pit stop operations for a given team, location, and season.
    """

    def __init__(self, team, gp_location, season, dataframes):
        """
        Initialize PitStop with relevant dataframes and race context.

        Args:
            team (Team): The team object (with a `name` attribute).
            gp_location (str): Grand Prix location.
            season (int): The season year.
            dataframes (dict): Dictionary of DataFrames loaded from the database.
        """
        self.team = team.name
        self.gp_location = gp_location
        self.season = season
        self.dfs = dataframes

        # Number of past seasons to consider when computing baseline
        self.len_train_df = 2

        df_races = self.dfs["races"]
        race_row = df_races[
            (df_races["season"] == self.season)
            & (df_races["location"] == self.gp_location)
        ]
        if race_row.empty:
            raise ValueError(
                f"No race found for location '{self.gp_location}' "
                f"in season {self.season}."
            )

        # Unique ID of the race in the DB
        self.race_id = race_row["id"].iloc[0]
        self.avg_min_pit_stop_duration = None

    def calculate_best_pit_stop_duration(self):
        """
        Compute the best (minimum) pit stop duration over previous seasons
        at the same circuit, then store the average of these minima.
        """
        df_laps = self.dfs["laps"]
        df_races = self.dfs["races"]

        location = df_races[df_races["id"] == self.race_id]["location"].iloc[0]

        # Past seasons to consider
        seasons_to_train = [
            self.season - x for x in range(1, self.len_train_df + 1)
        ]

        # Gather race IDs for the same location in those past seasons
        races_to_train = list(
            df_races[
                (df_races["location"] == location)
                & (df_races["season"].isin(seasons_to_train))
            ]["id"]
        )

        # Take the 2.5th percentile pit stop time for each race, then average
        min_pit_stop_per_race = (
            df_laps[df_laps["race_id"].isin(races_to_train)]
            .dropna(subset=["pitstopduration"])
            .groupby(["race_id"])[["pitstopduration"]]
            .quantile(q=0.025)
        )
        avg_min_pit_stop_duration = min_pit_stop_per_race["pitstopduration"].mean()

        self.avg_min_pit_stop_duration = avg_min_pit_stop_duration

    def calibrate_pit_stop_variability_law(self):
        """
        Fit a Fisk distribution to the difference (pitstop_duration - baseline)
        for this team in the current season (up to the current race).
        Returns the shape, loc, scale parameters.
        """
        df_laps = self.dfs["laps"]
        df_starterfields = self.dfs["starterfields"]
        df_races = self.dfs["races"]

        df_laps_with_season = df_laps.merge(
            df_races[["id", "season"]],
            left_on="race_id",
            right_on="id",
            how="left",
        ).drop(columns=["id"])

        df_merged = df_laps_with_season.merge(
            df_starterfields[["race_id", "driver_id", "team"]],
            on=["race_id", "driver_id"],
            how="left",
        )

        # Only for this team, current season, and pit stop durations before this race
        df_filtered = df_merged[
            (df_merged["team"] == self.team)
            & (df_merged["season"] == self.season)
            & (df_merged["race_id"] < self.race_id)
            & (df_merged["pitstopduration"].notna())
            & (df_merged["pitstopduration"] < 700)
        ].copy()

        # Difference from the baseline average minimum
        df_filtered["pitstop_diff"] = (
            df_filtered["pitstopduration"] - self.avg_min_pit_stop_duration
        )

        shape, loc, scale = fisk.fit(df_filtered["pitstop_diff"])
        return [shape, loc, scale]

    def calculate_pit_stop_duration(self):
        """
        Sample a pit stop duration by adding a random variability
        to the average minimum pit stop duration based on the Fisk distribution.
        """
        shape, loc, scale = self.calibrate_pit_stop_variability_law()
        variability = fisk.rvs(shape, loc=loc, scale=scale, size=1)[0]
        return self.avg_min_pit_stop_duration + variability
