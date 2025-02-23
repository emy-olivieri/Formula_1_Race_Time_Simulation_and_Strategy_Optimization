# pit_stop.py
import pandas as pd
from scipy.stats import fisk

class PitStop:
    """
    Gère la logique des arrêts aux stands pour une équipe, un circuit et une saison donnés.
    """
    def __init__(self, team, gp_location, season, dataframes):
        self.team = team.name
        self.gp_location = gp_location
        self.season = season
        self.dfs = dataframes
        self.len_train_df = 2

        df_races = self.dfs["races"]
        race_row = df_races[(df_races["season"] == self.season) & (df_races["location"] == self.gp_location)]
        if race_row.empty:
            raise ValueError(f"Aucune course trouvée pour {self.gp_location} en saison {self.season}.")
        self.race_id = race_row["id"].iloc[0]
        self.avg_min_pit_stop_duration = None

    def calculate_best_pit_stop_duration(self):
        df_laps = self.dfs["laps"]
        df_races = self.dfs["races"]
        location = df_races[df_races["id"] == self.race_id]["location"].iloc[0]
        seasons_to_train = [self.season - x for x in range(1, self.len_train_df + 1)]
        races_to_train = list(df_races[(df_races["location"] == location) & (df_races["season"].isin(seasons_to_train))]["id"])
        min_pit_stop_per_race = (
            df_laps[df_laps["race_id"].isin(races_to_train)]
            .dropna(subset=["pitstopduration"])
            .groupby("race_id")[["pitstopduration"]]
            .quantile(q=0.025)
        )
        self.avg_min_pit_stop_duration = min_pit_stop_per_race["pitstopduration"].mean()

    def calibrate_pit_stop_variability_law(self):
        df_laps = self.dfs["laps"]
        df_starterfields = self.dfs["starterfields"]
        df_races = self.dfs["races"]
        df_laps_with_season = df_laps.merge(df_races[["id", "season"]], left_on="race_id", right_on="id", how="left").drop(columns=["id"])
        df_merged = df_laps_with_season.merge(df_starterfields[["race_id", "driver_id", "team"]], on=["race_id", "driver_id"], how="left")
        df_filtered = df_merged[
            (df_merged["team"] == self.team) &
            (df_merged["season"] == self.season) &
            (df_merged["race_id"] < self.race_id) &
            (df_merged["pitstopduration"].notna()) &
            (df_merged["pitstopduration"] < 700)
        ].copy()
        df_filtered["pitstop_diff"] = df_filtered["pitstopduration"] - self.avg_min_pit_stop_duration
        shape, loc, scale = fisk.fit(df_filtered["pitstop_diff"])
        return [shape, loc, scale]

    def calculate_pit_stop_duration(self):
        shape, loc, scale = self.calibrate_pit_stop_variability_law()
        variability = fisk.rvs(shape, loc=loc, scale=scale, size=1)[0]
        return self.avg_min_pit_stop_duration + variability
