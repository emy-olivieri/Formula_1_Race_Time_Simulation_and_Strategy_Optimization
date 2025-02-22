import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from run import Run
from data_loader import DataLoader

class MonteCarloSimulator:
    """
    Monte Carlo Simulation for F1 race modeling.
    Runs multiple simulations to assess variability in race outcomes.
    """
    def __init__(self, season, gp_location, db_path, driver_strategies, num_simulations=1000):
        """
        Initialize the Monte Carlo simulator.

        Args:
            season (int): The racing season (year).
            gp_location (str): Grand Prix location.
            db_path (str): Path to the SQLite database.
            num_simulations (int): Number of Monte Carlo iterations.
        """
        self.season = season
        self.driver_strategies = driver_strategies
        self.gp_location = gp_location
        self.num_simulations = num_simulations
        self.db_path = db_path
        self.data_loader = DataLoader(db_path=self.db_path)
        self.dataframes = self.data_loader.load_data()
        # On stocke ici, pour chaque simulation, le DataFrame laps_summary (contenant tous les tours)
        self.results = []

    def run_simulation(self):
        """
        Execute multiple race simulations and store results.
        """
        for i in range(self.num_simulations):
            race_run = Run(season=self.season, gp_location=self.gp_location, 
                           dataframes=self.dataframes, driver_strategies=self.driver_strategies)
            race_run.run()
            # On stocke la simulation (par exemple le résumé des tours)
            self.results.append(race_run.laps_summary.copy())
            print(f"Simulation {i+1}/{self.num_simulations} terminée.")

    def analyze_results(self):
        """
        Analyze the results of the Monte Carlo simulations.
        Returns a DataFrame with mean finishing positions and cumulative times for each driver.
        """
        outcomes_list = []
        # Pour chaque simulation, on extrait le résultat final pour chaque pilote.
        # Le résultat final est la dernière ligne (du dernier tour) pour chaque driver.
        for sim in self.results:
            final_outcomes = sim.sort_values(by="lap").groupby("driver_id").last().reset_index()
            # On renomme les colonnes pour plus de clarté
            final_outcomes = final_outcomes.rename(columns={
                "position": "final_position",
                "cumulative_lap_time": "cumulative_time"
            })
            outcomes_list.append(final_outcomes[['driver_id', 'final_position', 'cumulative_time']])
        
        # Concaténer les résultats de toutes les simulations
        outcomes_concat = pd.concat(outcomes_list, ignore_index=True)
        # Calculer la moyenne pour chaque pilote
        mean_results = outcomes_concat.groupby("driver_id").agg({
            "final_position": "mean",
            "cumulative_time": "mean"
        }).reset_index()
        return mean_results

    def summarize(self):
        """
        Print a summary of the Monte Carlo simulation results and plot mean outcomes.
        """
        mean_results = self.analyze_results()
        print("Résultats moyens issus des simulations Monte Carlo:")
        print(mean_results)

        # Création d'un graphique avec deux axes
        fig, ax1 = plt.subplots(figsize=(10, 6))
        
        # Trace un bar plot pour la position finale moyenne
        ax1.bar(mean_results['driver_id'], mean_results['final_position'], color='blue', alpha=0.7)
        ax1.set_xlabel("Driver ID")
        ax1.set_ylabel("Position finale moyenne", color='blue')
        ax1.tick_params(axis='y', labelcolor='blue')
        ax1.set_title("Simulations Monte Carlo: Positions finales et temps cumulé moyens")
        plt.xticks(rotation=90)
        
        # Un second axe pour tracer le temps cumulé moyen
        ax2 = ax1.twinx()
        ax2.plot(mean_results['driver_id'], mean_results['cumulative_time'], color='red', marker='o', linestyle='--')
        ax2.set_ylabel("Temps cumulé moyen", color='red')
        ax2.tick_params(axis='y', labelcolor='red')
        
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    db_path = "F1_timingdata_2014_2019.sqlite"
    season = 2016
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
                             'tire_age': 18}}}
    gp_location = "Austin"
    num_simulations = 2
    
    simulator = MonteCarloSimulator(season, gp_location, db_path, driver_strategies, num_simulations)
    simulator.run_simulation()
    simulator.summarize()
