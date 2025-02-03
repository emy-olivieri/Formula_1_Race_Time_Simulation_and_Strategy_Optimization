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

        # Example safety car laps (could be configurable)
        self.safety_car_laps =  []

        self.number_of_laps = None
        self.drivers_list = []
        self.starting_grid = None

        # Summaries of laps, including status (running / DNF)
        self.laps_summary = pd.DataFrame(
            columns=["lap", "driver_id", "position",
            
                     "lap_time", "cumulative_lap_time", "status"]
        )

        self._initialize_parameters(driver_strategies)

    def run(self):
        """
        Simulate the race from lap 1 to number_of_laps.
        For each lap:
            - Update driver status (DNF or alive)
            - Compute lap time (with possible pit stop)
            - Update positions
            - Record the results in laps_summary
        """

        #    This function modifies self.safety_car_laps and sets each driver's earliest_dnf_lap.
        self._initialize_retirements_and_safety_car()

        for lap in range(1, self.number_of_laps + 1):
            # 1) Update DNF status
            for driver in self.drivers_list:
                driver.update_status(lap)

                # 2) If alive, compute lap time
                if driver.alive:
                    driver.update_info(lap, self.number_of_laps)
                    lap_time = self._compute_lap_time(driver, lap)
                    pit_stop_time = self._pit_stop(driver, lap)

                    driver.current_lap_time = lap_time + pit_stop_time
                    driver.cumulative_lap_time += driver.current_lap_time
                else:
                    driver.current_lap_time = 0

            # 3) Update positions for all alive drivers
            for driver in self.drivers_list:
                if driver.alive:
                    self._get_driver_position(driver)
                else:
                    driver.position = np.nan

            # 4) Fill laps_summary for each driver
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


    def _initialize_retirements_and_safety_car(self):
        """
        1) Calls `simulate_dnf_lap(driver)` for each driver to assign earliest_dnf_lap.
        2) If earliest_dnf_lap is set for a driver, we deploy the safety car
           for 5 laps with probability p_safety_car (e.g., 0.2).
        """
        p_safety_car = 0.2
        safety_car_duration = 5

        for driver in self.drivers_list:
            # 1) Call the existing function that sets earliest_dnf_lap
            self.simulate_dnf_lap(driver)

            # 2) If the driver does retire at some lap, we have earliest_dnf_lap
            if driver.earliest_dnf_lap is not None:
                # Deploy safety car for the next 5 laps with probability 0.2
                if np.random.rand() < p_safety_car:
                    sc_start = driver.earliest_dnf_lap
                    sc_end = min(sc_start + safety_car_duration - 1, self.number_of_laps)
                    for lap_sc in range(sc_start, sc_end + 1):
                        if lap_sc not in self.safety_car_laps:
                            self.safety_car_laps.append(lap_sc)

    def _compute_lap_time(self, driver: Driver, current_lap: int) -> float:
        """
        Calculate the lap time for a driver using their regression model,
        adding a random stochastic term, and adjusting for safety car.

        Args:
            driver (Driver): The driver object.
            current_lap (int): The lap number.

        Returns:
            float: Computed lap time for this lap.
        """
        import pandas as pd

        features = pd.DataFrame({
            "fuelc": [driver.fuelc],
            "compound": [driver.compound],
            "tireage": [driver.tire_age],
        })

        # Base time from the FuelAndTireModel
        base_time = driver.fuel_tire_model.predict(features).iloc[0]

        # Random variation
        time_variability = np.random.normal(0, driver.variability)
        lap_time = driver.best_qualif_time + base_time + time_variability

        # Safety car adjustment
        if current_lap in self.safety_car_laps:
            lap_time *= 1.2

        return lap_time

    def _pit_stop(self, driver: Driver, current_lap: int) -> float:
        """
        Manage pit stop if the driver is scheduled on this lap or if
        there's a beneficial time during safety car, etc.
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

                    driver.tire_age =  pit_stop_data["tire_age"]
                    driver.compound = pit_stop_data["compound"]
                    driver.next_pit_stop += 1

                    return calculated_duration
            return 0.0
        except ValueError as err:
            print(f"Error during pit stop for driver {driver.name}: {err}")
            return 0.0

    def _get_driver_position(self, driver: Driver):
        """
        Sort alive drivers by cumulative lap time and assign positions.
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
        # Pour éviter les erreurs si driver_strategies est None
        if driver_strategies is None:
            driver_strategies = {}

        races_df = self.dataframes["races"]
        qualifyings_df = self.dataframes["qualifyings"]

        # Récupération de la course en fonction de la saison & location
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

        # Construction de la grille de départ depuis les qualifs
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

        # On instancie les Driver
        drivers_df = self.dataframes["drivers"]
        driver_ids = sorted_rows["driver_id"].unique().tolist()

        for d_id in driver_ids:
            driver_row = drivers_df[drivers_df["id"] == d_id]
            if driver_row.empty:
                continue

            driver_name = driver_row.iloc[0]["name"]

            # On récupère la stratégie pour ce pilote depuis le dictionnaire
            # Si le nom du pilote n'y est pas, on envoie un dict vide.
            strategy_for_this_driver = driver_strategies.get(driver_name, {})

            driver_obj = Driver(
                season=self.season,
                race_id=self.race_id,
                dataframes=self.dataframes,
                name=driver_name,
                strategy=strategy_for_this_driver,  # On passe la stratégie ici
            )
            self.drivers_list.append(driver_obj)

    def simulate_dnf_lap(self, driver: Driver):
        """
        Randomly select an accident lap and a failure lap for the driver
        based on binomial draws for accidents/failures.
        The earliest of these, if any, is the actual DNF lap.
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
