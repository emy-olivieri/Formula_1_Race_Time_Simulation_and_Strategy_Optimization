import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from run import Run
from data_loader import DataLoader
from spearman_evaluation import SpearmanEvaluation
from wilcoxon_evaluation import WilcoxonEvaluation


class MonteCarloSimulator:
    """
    Monte Carlo Simulation for F1 race modeling.
    Runs multiple simulations to assess variability in race outcomes
    and compare simulated outcomes with actual race results.
    """
    def __init__(self, season, gp_location, db_path, driver_strategies, num_simulations=1000):
        """
        Initialize the Monte Carlo simulator.

        Args:
            season (int): The racing season (year).
            gp_location (str): Grand Prix location.
            db_path (str): Path to the SQLite database.
            driver_strategies (dict): Strategies for each driver.
            num_simulations (int): Number of Monte Carlo iterations.
        """
        self.season = season
        self.driver_strategies = driver_strategies
        self.gp_location = gp_location
        self.num_simulations = num_simulations
        self.db_path = db_path
        self.data_loader = DataLoader(db_path=self.db_path)
        self.dataframes = self.data_loader.load_data()
        self.results = []
        self.final_outcomes = pd.DataFrame()
        self.comparison_df=pd.DataFrame()

    def run_simulation(self):
        """
        Runs multiple race simulations and stores the final outcomes.
        """
        for i in range(self.num_simulations):
            race_run = Run(
                season=self.season,
                gp_location=self.gp_location,
                dataframes=self.dataframes,
                driver_strategies=self.driver_strategies
            )
            race_run.run()
            self.results.append(race_run.outcomes.copy())
            print(f"Simulation {i+1}/{self.num_simulations} completed.")
        
        self.final_outcomes = pd.concat(self.results, ignore_index=True)

    def compare_outcomes(self):
        """
        Compare simulated race results with actual results.

        Returns:
            DataFrame: Contains comparison of simulated and actual positions and times.
        """
        if self.final_outcomes.empty:
            print("No simulated outcomes available.")
            return pd.DataFrame()

        if "starterfields" not in self.dataframes or "laps" not in self.dataframes:
            print("Missing required race data.")
            return pd.DataFrame()

        # Get the race_id of the current GP
        races_df = self.dataframes["races"]
        race_row = races_df[(races_df["season"] == self.season) & (races_df["location"] == self.gp_location)]
        if race_row.empty:
            print("No race found for the specified season and location.")
            return pd.DataFrame()
        race_id = race_row["id"].iloc[0]

        # Simulated results
        sim_outcomes = self.final_outcomes.groupby("driver_id").agg({
            "final_position": "mean",
            "cumulative_time": "mean"
        }).reset_index().rename(columns={
            "final_position": "final_position_sim",
            "cumulative_time": "cumulative_time_sim"
        })

        # Actual results
        actual_outcomes = self.dataframes["starterfields"]
        actual_outcomes = actual_outcomes[actual_outcomes["race_id"] == race_id]
        actual_outcomes = actual_outcomes.rename(columns={"resultposition": "final_position_actual"})
        actual_outcomes = actual_outcomes[["driver_id", "final_position_actual"]]

        # Actual lap times from `laps` table
        laps_df = self.dataframes["laps"]
        last_laps = laps_df[laps_df["race_id"] == race_id].groupby("driver_id")["lapno"].max().reset_index()
        final_times = pd.merge(laps_df[laps_df["race_id"] == race_id], last_laps, on=["driver_id", "lapno"], how="inner")[["driver_id", "racetime"]]
        final_times = final_times.rename(columns={"racetime": "cumulative_time_actual"})

        # Merge all data
        self.comparison_df = pd.merge(sim_outcomes, actual_outcomes, on="driver_id", how="inner")
        self.comparison_df = pd.merge(self.comparison_df, final_times, on="driver_id", how="inner")

        return self.comparison_df

    def summarize(self):
        """
        Summarizes simulation results, compares outcomes, and performs statistical tests.
        """
        self.compare_outcomes()  

        if self.comparison_df.empty:
            print("\nNo actual race results available for comparison.")
            return

        # Ensure required columns exist
        required_columns = {"final_position_actual", "final_position_sim", "cumulative_time_actual", "cumulative_time_sim"}
        if not required_columns.issubset(self.comparison_df.columns):
            print("\nMissing required columns for evaluation. Check `compare_outcomes()`.")
            return

        # Run Wilcoxon test on race times
        print("\n=== Wilcoxon Test for Lap Times ===")
        wilcoxon_eval = WilcoxonEvaluation(
            actual_data=self.comparison_df["cumulative_time_actual"],
            simulated_data=self.comparison_df["cumulative_time_sim"]
        )
        wilcoxon_eval.evaluate()

        # Run Spearman Rank test for positions
        print("\n=== Spearman Rank Correlation for Positions ===")
        spearman_eval = SpearmanEvaluation(
            actual_data=self.comparison_df["final_position_actual"],
            simulated_data=self.comparison_df["final_position_sim"]
        )
        spearman_eval.evaluate()


if __name__ == "__main__":
    db_path = "F1_timingdata_2014_2019.sqlite"
    season = 2016
    gp_location = "Austin"
    num_simulations = 2

    driver_strategies = {
        'Lewis Hamilton': {'starting_compound': 'A3',
                           'starting_tire_age': 2,
                           1: {'compound': 'A3',
                               'pitstop_interval': [11, 11],
                               'pit_stop_lap': 11,
                               'tire_age': 13},
                           2: {'compound': 'A3',
                               'pitstop_interval': [31, 31],
                               'pit_stop_lap': 31,
                               'tire_age': 20}},
        'Nico Rosberg': {'starting_compound': 'A3',
                         'starting_tire_age': 2,
                         1: {'compound': 'A3',
                             'pitstop_interval': [10, 10],
                             'pit_stop_lap': 10,
                             'tire_age': 12},
                         2: {'compound': 'A2',
                             'pitstop_interval': [31, 31],
                             'pit_stop_lap': 31,
                             'tire_age': 21}},
        'Daniel Ricciardo': {'starting_compound': 'A4',
                             'starting_tire_age': 2,
                             1: {'compound': 'A4',
                                 'pitstop_interval': [8, 8],
                                 'pit_stop_lap': 8,
                                 'tire_age': 10},
                             2: {'compound': 'A3',
                                 'pitstop_interval': [25, 25],
                                 'pit_stop_lap': 25,
                                 'tire_age': 17}},
        'Max Verstappen': {'starting_compound': 'A3',
                           'starting_tire_age': 2,
                           1: {'compound': 'A3',
                               'pitstop_interval': [9, 9],
                               'pit_stop_lap': 9,
                               'tire_age': 11},
                           2: {'compound': 'A3',
                               'pitstop_interval': [26, 26],
                               'pit_stop_lap': 26,
                               'tire_age': 17}},
        'Kimi Raikkonen': {'starting_compound': 'A4',
                           'starting_tire_age': 2,
                           1: {'compound': 'A4',
                               'pitstop_interval': [8, 8],
                               'pit_stop_lap': 8,
                               'tire_age': 10},
                           2: {'compound': 'A3',
                               'pitstop_interval': [24, 24],
                               'pit_stop_lap': 24,
                               'tire_age': 16},
                           3: {'compound': 'A4',
                               'pitstop_interval': [38, 38],
                               'pit_stop_lap': 38,
                               'tire_age': 14}},
        'Sebastian Vettel': {'starting_compound': 'A4',
                             'starting_tire_age': 2,
                             1: {'compound': 'A4',
                                 'pitstop_interval': [14, 14],
                                 'pit_stop_lap': 14,
                                 'tire_age': 16},
                             2: {'compound': 'A3',
                                 'pitstop_interval': [29, 29],
                                 'pit_stop_lap': 29,
                                 'tire_age': 15},
                             3: {'compound': 'A2',
                                 'pitstop_interval': [53, 53],
                                 'pit_stop_lap': 53,
                                 'tire_age': 24}},
        'Nico Hulkenberg': {'starting_compound': 'A4', 'starting_tire_age': 2},
        'Valtteri Bottas': {'starting_compound': 'A4',
                            'starting_tire_age': 2,
                            1: {'compound': 'A4',
                                'pitstop_interval': [1, 1],
                                'pit_stop_lap': 1,
                                'tire_age': 3},
                            2: {'compound': 'A3',
                                'pitstop_interval': [20, 20],
                                'pit_stop_lap': 20,
                                'tire_age': 19}},
        'Felipe Massa': {'starting_compound': 'A4',
                         'starting_tire_age': 2,
                         1: {'compound': 'A4',
                             'pitstop_interval': [11, 11],
                             'pit_stop_lap': 11,
                             'tire_age': 13},
                         2: {'compound': 'A3',
                             'pitstop_interval': [29, 29],
                             'pit_stop_lap': 29,
                             'tire_age': 18},
                         3: {'compound': 'A2',
                             'pitstop_interval': [54, 54],
                             'pit_stop_lap': 54,
                             'tire_age': 25}},
        'Carlos Sainz Jnr': {'starting_compound': 'A4',
                             'starting_tire_age': 2,
                             1: {'compound': 'A4',
                                 'pitstop_interval': [11, 11],
                                 'pit_stop_lap': 11,
                                 'tire_age': 13},
                             2: {'compound': 'A3',
                                 'pitstop_interval': [30, 30],
                                 'pit_stop_lap': 30,
                                 'tire_age': 19}},
        'Sergio Perez': {'starting_compound': 'A4',
                         'starting_tire_age': 0,
                         1: {'compound': 'A4',
                             'pitstop_interval': [10, 10],
                             'pit_stop_lap': 10,
                             'tire_age': 10},
                         2: {'compound': 'A2',
                             'pitstop_interval': [27, 27],
                             'pit_stop_lap': 27,
                             'tire_age': 17}},
        'Fernando Alonso': {'starting_compound': 'A3',
                            'starting_tire_age': 0,
                            1: {'compound': 'A3',
                                'pitstop_interval': [11, 11],
                                'pit_stop_lap': 11,
                                'tire_age': 11},
                            2: {'compound': 'A2',
                                'pitstop_interval': [30, 30],
                                'pit_stop_lap': 30,
                                'tire_age': 19}},
        'Daniil Kvyat': {'starting_compound': 'A3',
                         'starting_tire_age': 0,
                         1: {'compound': 'A3',
                             'pitstop_interval': [21, 21],
                             'pit_stop_lap': 21,
                             'tire_age': 21}},
        'Esteban Gutierrez': {'starting_compound': 'A3',
                              'starting_tire_age': 0,
                              1: {'compound': 'A3',
                                  'pitstop_interval': [13, 13],
                                  'pit_stop_lap': 13,
                                  'tire_age': 13}},
        'Jolyon Palmer': {'starting_compound': 'A3',
                          'starting_tire_age': 0,
                          1: {'compound': 'A3',
                              'pitstop_interval': [15, 15],
                              'pit_stop_lap': 15,
                              'tire_age': 15},
                          2: {'compound': 'A3',
                              'pitstop_interval': [26, 26],
                              'pit_stop_lap': 26,
                              'tire_age': 11}},
        'Marcus Ericsson': {'starting_compound': 'A3',
                            'starting_tire_age': 0,
                            1: {'compound': 'A3',
                                'pitstop_interval': [17, 17],
                                'pit_stop_lap': 17,
                                'tire_age': 17}},
        'Romain Grosjean': {'starting_compound': 'A4',
                            'starting_tire_age': 0,
                            1: {'compound': 'A4',
                                'pitstop_interval': [10, 10],
                                'pit_stop_lap': 10,
                                'tire_age': 10},
                            2: {'compound': 'A3',
                                'pitstop_interval': [27, 27],
                                'pit_stop_lap': 27,
                                'tire_age': 17}},
        'Kevin Magnussen': {'starting_compound': 'A3',
                            'starting_tire_age': 0,
                            1: {'compound': 'A3',
                                'pitstop_interval': [13, 13],
                                'pit_stop_lap': 13,
                                'tire_age': 13},
                            2: {'compound': 'A3',
                                'pitstop_interval': [27, 27],
                                'pit_stop_lap': 27,
                                'tire_age': 14},
                            3: {'compound': 'A2',
                                'pitstop_interval': [43, 43],
                                'pit_stop_lap': 43,
                                'tire_age': 16}},
        'Jenson Button': {'starting_compound': 'A4',
                          'starting_tire_age': 0,
                          1: {'compound': 'A4',
                              'pitstop_interval': [10, 10],
                              'pit_stop_lap': 10,
                              'tire_age': 10},
                          2: {'compound': 'A2',
                              'pitstop_interval': [28, 28],
                              'pit_stop_lap': 28,
                              'tire_age': 18}},
        'Pascal Wehrlein': {'starting_compound': 'A3',
                            'starting_tire_age': 0,
                            1: {'compound': 'A3',
                                'pitstop_interval': [13, 13],
                                'pit_stop_lap': 13,
                                'tire_age': 13},
                            2: {'compound': 'A2',
                                'pitstop_interval': [30, 30],
                                'pit_stop_lap': 30,
                                'tire_age': 17}},
        'Felipe Nasr': {'starting_compound': 'A2',
                        'starting_tire_age': 0,
                        1: {'compound': 'A2',
                            'pitstop_interval': [29, 29],
                            'pit_stop_lap': 29,
                            'tire_age': 29}},
        'Esteban Ocon': {'starting_compound': 'A2',
                         'starting_tire_age': 0,
                         1: {'compound': 'A2',
                             'pitstop_interval': [17, 17],
                             'pit_stop_lap': 17,
                             'tire_age': 17},
                         2: {'compound': 'A3',
                             'pitstop_interval': [26, 26],
                             'pit_stop_lap': 26,
                             'tire_age': 9},
                         3: {'compound': 'A3',
                             'pitstop_interval': [44, 44],
                             'pit_stop_lap': 44,
                             'tire_age': 18}}
        }
    
    
    simulator = MonteCarloSimulator(season, gp_location, db_path, driver_strategies, num_simulations)
    simulator.run_simulation()
    simulator.summarize()
