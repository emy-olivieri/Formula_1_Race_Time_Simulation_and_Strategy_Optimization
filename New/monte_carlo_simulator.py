import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from run import Run
from data_loader import DataLoader

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
        # On suppose que le DataLoader charge les tables suivantes :
        # - "races", "qualifyings", "drivers", et "results"
        self.dataframes = self.data_loader.load_data()
        # Stocke les outcomes simulés de chaque simulation
        self.results = []
        # DataFrame final regroupant tous les outcomes simulés
        self.final_outcomes = pd.DataFrame()

    def run_simulation(self):
        """
        Exécute plusieurs simulations de course et stocke les outcomes finaux.
        """
        for i in range(self.num_simulations):
            race_run = Run(
                season=self.season,
                gp_location=self.gp_location,
                dataframes=self.dataframes,
                driver_strategies=self.driver_strategies
            )
            race_run.run()
            # On récupère directement le DataFrame outcomes généré dans la classe Run.
            self.results.append(race_run.outcomes.copy())
            print(f"Simulation {i+1}/{self.num_simulations} terminée.")
        
        # Concatène tous les outcomes simulés dans un DataFrame final
        self.final_outcomes = pd.concat(self.results, ignore_index=True)

    def analyze_results(self):
        """
        Calcule la moyenne des outcomes simulés par pilote.

        Returns:
            DataFrame: Moyennes des positions finales et des temps cumulés simulés,
                       triées par position finale moyenne.
        """
        if self.final_outcomes.empty:
            print("Aucun outcome simulé à analyser. Veuillez exécuter d'abord run_simulation().")
            return pd.DataFrame()
        
        mean_results = self.final_outcomes.groupby("driver_id").agg({
            "final_position": "mean",
            "cumulative_time": "mean"
        }).reset_index()
        mean_results = mean_results.sort_values(by="final_position")
        return mean_results
    

    def compare_outcomes(self):
      """
      Compare les outcomes simulés moyens avec les résultats réels de la course
      issus de la table 'starterfields'. On filtre pour ne sélectionner que la course
      correspondant au season et gp_location de la simulation.
      
      On utilise 'resultposition' comme la position finale réelle.

      Returns:
          DataFrame: Tableau de comparaison contenant :
              - driver_id
              - final_position_sim (moyenne simulée)
              - final_position_actual (résultat réel)
              - position_diff (écart)
      """
      if self.final_outcomes.empty:
          print("Aucun outcome simulé à comparer. Veuillez exécuter d'abord run_simulation().")
          return pd.DataFrame()

      # Vérifier que la table starterfields existe
      if "starterfields" not in self.dataframes:
          print("Les résultats réels ne sont pas disponibles dans les données (table 'starterfields' non trouvée).")
          return pd.DataFrame()

      # Détermination du race_id correspondant à la simulation
      races_df = self.dataframes["races"]
      race_row = races_df[(races_df["season"] == self.season) & (races_df["location"] == self.gp_location)]
      if race_row.empty:
          print("Aucune course trouvée pour la saison et le gp_location spécifiés.")
          return pd.DataFrame()
      race_id = race_row["id"].iloc[0]

      # Calcul des outcomes simulés moyens par pilote
      sim_outcomes = self.final_outcomes.groupby("driver_id").agg({
          "final_position": "mean"
      }).reset_index().rename(columns={
          "final_position": "final_position_sim"
      })

      # Récupération et filtrage des résultats réels depuis la table 'starterfields'
      actual_outcomes = self.dataframes["starterfields"].copy()
      # Filtrer pour la bonne course
      actual_outcomes = actual_outcomes[actual_outcomes["race_id"] == race_id]
      # Renommer 'resultposition' pour la comparaison
      actual_outcomes = actual_outcomes.rename(columns={
          "resultposition": "final_position_actual"
      })
      # On ne conserve que les colonnes nécessaires
      actual_outcomes = actual_outcomes[["driver_id", "final_position_actual"]]

      # Fusion sur driver_id
      comparison_df = pd.merge(sim_outcomes, actual_outcomes, on="driver_id", how="inner")
      # Calcul de l'écart
      comparison_df["position_diff"] = comparison_df["final_position_sim"] - comparison_df["final_position_actual"]

      return comparison_df


    def plot_driver_outcomes(self, driver_id_input):
        """
        Affiche la distribution des outcomes simulés pour un pilote donné.

        Args:
            driver_id_input: Le driver_id (sera converti en int).
        """
        try:
            driver_id = int(driver_id_input)
        except ValueError:
            print("Driver_id invalide, il doit être un entier.")
            return

        if self.final_outcomes.empty:
            print("Aucun outcome simulé disponible. Exécutez run_simulation() d'abord.")
            return

        driver_data = self.final_outcomes[self.final_outcomes["driver_id"] == driver_id]
        if driver_data.empty:
            print(f"Aucun résultat trouvé pour le pilote {driver_id}.")
            return

        positions = driver_data["final_position"].values
        times = driver_data["cumulative_time"].values

        fig, axs = plt.subplots(1, 2, figsize=(12, 5))
        axs[0].hist(positions, bins=range(int(positions.min()), int(positions.max())+2),
                    color='blue', alpha=0.7, edgecolor='black')
        axs[0].set_xlabel("Position finale")
        axs[0].set_ylabel("Fréquence")
        axs[0].set_title(f"Distribution des positions finales pour le pilote {driver_id}")

        axs[1].hist(times, bins=20, color='red', alpha=0.7, edgecolor='black')
        axs[1].set_xlabel("Temps cumulé")
        axs[1].set_ylabel("Fréquence")
        axs[1].set_title(f"Distribution du temps cumulé pour le pilote {driver_id}")

        plt.tight_layout()
        plt.show()

    def summarize(self):
        """
        Affiche le résumé des simulations (moyennes simulées) et la comparaison
        avec les résultats réels, puis propose d'afficher le plot pour un pilote choisi.
        """
        mean_results = self.analyze_results()
        if mean_results.empty:
            return

        print("Résultats moyens simulés (triés par position finale) issus des simulations Monte Carlo:")
        print(mean_results)

        comparison_df = self.compare_outcomes()
        if not comparison_df.empty:
            print("\nComparaison entre outcomes simulés et réels:")
            print(comparison_df)
        else:
            print("\nImpossible de comparer avec les résultats réels (vérifiez la présence de la table 'results').")

        driver_choice = input(
            "Entrez le driver_id du pilote pour lequel vous souhaitez afficher le graphique "
            "(ou appuyez sur Entrée pour quitter) : "
        ).strip()
        if driver_choice:
            self.plot_driver_outcomes(driver_choice)
        else:
            print("Aucun pilote sélectionné pour le plot.")


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
                             'tire_age': 18}}
        }
    
    gp_location = "Austin"
    num_simulations = 20  # Pour tester

    simulator = MonteCarloSimulator(season, gp_location, db_path, driver_strategies, num_simulations)
    simulator.run_simulation()
    simulator.summarize()


  
