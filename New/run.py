# -*- coding: utf-8 -*-
"""
run.py

Defines the Run class to orchestrate a race simulation for a given season,
Grand Prix location, and dataset.
"""

import numpy as np
import pandas as pd

from pit_stop import PitStop
from driver import Driver


class Run:
    """
    Orchestrates a race simulation for a given season, location, and data.
    """

    def __init__(self, season: int, gp_location: str, dataframes: dict, driver_strategies=None):
        """
        Args:
            season (int): The racing season (year).
            gp_location (str): Grand Prix location (e.g., 'SaoPaulo').
            dataframes (dict): Dictionary of DataFrames from the SQLite DB.
        """
        self.season = season
        self.gp_location = gp_location
        self.race_id = None
        self.dataframes = dataframes

        self.safety_car_laps = []

        self.number_of_laps = None
        self.drivers_list = []
        self.starting_grid = None

        self.laps_summary = pd.DataFrame(
            columns=["lap", "driver_id", "position",
                     "lap_time", "cumulative_lap_time", "status"]
        )

        # Ce dictionnaire (ou DataFrame) sera rempli à la fin de la course
        # et contiendra pour chaque pilote le temps total et la position finale.
        self.outcomes = {}
        self._initialize_parameters(driver_strategies)

    def run(self):
        """
        Simule la course de la première à la dernière boucle.
        Pour chaque tour :
            - Mise à jour du statut du pilote (DNF ou en course)
            - Calcul du temps de tour (avec éventuel arrêt aux stands)
            - Mise à jour des positions
            - Enregistrement des résultats dans laps_summary

        À la fin de la course, les pilotes en DNF se voient attribuer les dernières places.
        Ensuite, un dictionnaire (ou DataFrame) outcomes est créé pour enregistrer
        pour chaque pilote le temps cumulé et le classement final.
        """
        # 1) Initialisation des DNFs et des laps safety car
        self._initialize_retirements_and_safety_car()

        for lap in range(1, self.number_of_laps + 1):
            # 1) Mise à jour du statut DNF et calcul du temps de tour
            for driver in self.drivers_list:
                driver.update_status(lap)
                if driver.alive:
                    driver.update_info(lap, self.number_of_laps)
                    lap_time = self._compute_lap_time(driver, lap)
                    pit_stop_time = self._pit_stop(driver, lap)
                    driver.current_lap_time = lap_time + pit_stop_time
                    driver.cumulative_lap_time += driver.current_lap_time
                else:
                    driver.current_lap_time = 0

            # 2) Mise à jour des positions pour les pilotes en course
            for driver in self.drivers_list:
                if driver.alive:
                    self._get_driver_position(driver)
                else:
                    driver.position = None

            # 3) Enregistrement du résumé du tour pour chaque pilote
            for driver in self.drivers_list:
                if driver.alive or (driver.earliest_dnf_lap == lap):
                    status_str = "running" if driver.alive else "DNF"
                    new_row = {
                        "lap": lap,
                        "driver_id": driver.driver_id,
                        "position": driver.position,
                        "lap_time": driver.current_lap_time,
                        "cumulative_lap_time": driver.cumulative_lap_time,
                        "status": status_str,
                    }
                    self.laps_summary = pd.concat(
                        [self.laps_summary, pd.DataFrame([new_row])],
                        ignore_index=True,
                    )

        # 4) Finalisation du classement
        finishers = [driver for driver in self.drivers_list if driver.alive]
        dnfs = [driver for driver in self.drivers_list if not driver.alive]

        # Classement des finishers par temps cumulé croissant.
        finishers_sorted = sorted(finishers, key=lambda d: d.cumulative_lap_time)
        # Pour les DNFs, le pilote qui a quitté le plus tôt sera classé le plus bas.
        dnfs_sorted = sorted(dnfs, key=lambda d: d.earliest_dnf_lap)

        total_drivers = len(self.drivers_list)
        # Attribution des positions aux finishers (1 = meilleur temps)
        for idx, driver in enumerate(finishers_sorted, start=1):
            driver.position = idx
        # Attribution des positions aux DNFs : premier DNF prend la dernière place, etc.
        for idx, driver in enumerate(dnfs_sorted, start=1):
            driver.position = total_drivers - idx + 1

        # 5) Création du dictionnaire outcomes pour chaque pilote
        outcomes_list = []
        for driver in self.drivers_list:
            outcomes_list.append({
                "driver_id": driver.driver_id,
                "driver_name": driver.name,
                "final_position": driver.position,
                "cumulative_time": driver.cumulative_lap_time,
            })
        self.outcomes = pd.DataFrame(outcomes_list)
        # On peut également garder outcomes sous forme de dict si besoin :
        # self.outcomes = {driver.driver_id: {"driver_name": driver.name,
        #                                      "final_position": driver.position,
        #                                      "cumulative_time": driver.cumulative_lap_time}
        #                  for driver in self.drivers_list}

    def _initialize_retirements_and_safety_car(self):
        """
        1) Appelle `simulate_dnf_lap(driver)` pour chaque pilote afin d'assigner earliest_dnf_lap.
        2) Si earliest_dnf_lap est défini pour un pilote, déploie le safety car pendant 5 tours
           avec une probabilité p_safety_car (par exemple 0.2).
        """
        p_safety_car = 0.2
        safety_car_duration = 5

        for driver in self.drivers_list:
            self.simulate_dnf_lap(driver)
            if driver.earliest_dnf_lap is not None:
                if np.random.rand() < p_safety_car:
                    sc_start = driver.earliest_dnf_lap
                    sc_end = min(sc_start + safety_car_duration - 1, self.number_of_laps)
                    for lap_sc in range(sc_start, sc_end + 1):
                        if lap_sc not in self.safety_car_laps:
                            self.safety_car_laps.append(lap_sc)

    def _compute_lap_time(self, driver: Driver, current_lap: int) -> float:
        """
        Calcule le temps de tour pour un pilote en utilisant son modèle de régression,
        en ajoutant un terme stochastique, et en ajustant en cas de safety car.

        Args:
            driver (Driver): L'objet pilote.
            current_lap (int): Numéro du tour.

        Returns:
            float: Temps de tour calculé.
        """
        import pandas as pd

        features = pd.DataFrame({
            "fuelc": [driver.fuelc],
            "compound": [driver.compound],
            "tireage": [driver.tire_age],
        })

        base_time = driver.fuel_tire_model.predict(features).iloc[0]
        time_variability = np.random.normal(0, driver.variability)
        lap_time = driver.best_qualif_time + base_time + time_variability

        if current_lap in self.safety_car_laps:
            lap_time *= 1.2

        return lap_time

    def _pit_stop(self, driver: Driver, current_lap: int) -> float:
        """
        Gère l'arrêt aux stands si le pilote est programmé à ce tour ou si un arrêt pendant
        le safety car est avantageux.
        """
        try:
            if driver.next_pit_stop in driver.pit_stops_info:
                pit_stop_data = driver.pit_stops_info[driver.next_pit_stop]
                is_pit_stop_lap = current_lap == pit_stop_data["pit_stop_lap"]
                is_safety_car_pit_stop = (
                    current_lap in self.safety_car_laps
                    and current_lap in range(
                        pit_stop_data["pitstop_interval"][0],
                        pit_stop_data["pitstop_interval"][1] + 1,
                    )
                )
                if is_pit_stop_lap or is_safety_car_pit_stop:
                    pit_stop_obj = PitStop(
                        team=driver.team,
                        gp_location=self.gp_location,
                        season=self.season,
                        dataframes=self.dataframes,
                    )
                    pit_stop_obj.calculate_best_pit_stop_duration()
                    calculated_duration = pit_stop_obj.calculate_pit_stop_duration()

                    driver.tire_age = pit_stop_data["tire_age"]
                    driver.compound = pit_stop_data["compound"]
                    driver.next_pit_stop += 1

                    return calculated_duration
            return 0.0
        except ValueError as err:
            print(f"Error during pit stop for driver {driver.name}: {err}")
            return 0.0

    def _get_driver_position(self, driver: Driver):
        """
        Trie les pilotes encore en course par temps cumulé et assigne une position.
        """
        sorted_drivers = sorted(
            [drv for drv in self.drivers_list if drv.alive],
            key=lambda d: d.cumulative_lap_time,
        )
        for idx, drv in enumerate(sorted_drivers, start=1):
            if drv == driver:
                driver.position = idx

    def _initialize_parameters(self, driver_strategies):
        """
        Initialise la course, détermine les pilotes participants et leur stratégie.
        """
        if driver_strategies is None:
            driver_strategies = {}

        races_df = self.dataframes["races"]
        qualifyings_df = self.dataframes["qualifyings"]

        race_row = races_df[
            (races_df["season"] == self.season)
            & (races_df["location"] == self.gp_location)
        ]
        if race_row.empty:
            raise ValueError(
                f"No race found for location '{self.gp_location}' in season {self.season}."
            )

        self.race_id = race_row["id"].iloc[0]
        self.number_of_laps = race_row.iloc[0]["nolapsplanned"]

        merged_data = qualifyings_df.merge(
            races_df,
            left_on="race_id",
            right_on="id",
            suffixes=("_qualifying", "_race"),
        )
        qualifying_rows = merged_data[
            (merged_data["season"] == self.season)
            & (merged_data["location"] == self.gp_location)
        ]
        if qualifying_rows.empty:
            raise ValueError(
                f"No qualifying data found for '{self.gp_location}' in season {self.season}."
            )

        sorted_rows = qualifying_rows.sort_values(by="position")
        self.starting_grid = list(zip(sorted_rows["driver_id"], sorted_rows["position"]))

        drivers_df = self.dataframes["drivers"]
        driver_ids = sorted_rows["driver_id"].unique().tolist()

        for d_id in driver_ids:
            driver_row = drivers_df[drivers_df["id"] == d_id]
            if driver_row.empty:
                continue

            driver_name = driver_row.iloc[0]["name"]
            strategy_for_this_driver = driver_strategies.get(driver_name, {})

            driver_obj = Driver(
                season=self.season,
                race_id=self.race_id,
                dataframes=self.dataframes,
                name=driver_name,
                strategy=strategy_for_this_driver,
            )
            self.drivers_list.append(driver_obj)

    def simulate_dnf_lap(self, driver: Driver):
        """
        Sélectionne aléatoirement un tour pour un accident et un tour pour une défaillance
        en utilisant des tirages binomiaux. Le plus tôt de ces deux tours, s'il existe,
        sera le tour effectif du DNF.
        """
        driver.accident_dnf_lap = (
            np.random.randint(1, self.number_of_laps + 1)
            if np.random.binomial(1, driver.accident_dnf_probability)
            else None
        )
        driver.failure_dnf_lap = (
            np.random.randint(1, self.number_of_laps + 1)
            if np.random.binomial(1, driver.failure_dnf_probability)
            else None
        )

        potential_dnf_laps = [
            lap
            for lap in (driver.accident_dnf_lap, driver.failure_dnf_lap)
            if lap is not None
        ]
        driver.earliest_dnf_lap = min(potential_dnf_laps, default=None)
