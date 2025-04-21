import numpy as np
import pandas as pd
from pit_stop import PitStop
from driver import Driver

class Run:
    """
    Orchestre la simulation d'une course pour une saison, un circuit et un jeu de données donnés.
    """
    def __init__(self, season: int, gp_location: str, dataframes: dict, driver_strategies=None,test=False):
        safety_car_dict_for_testing= {
            "Suzuka": [],
            "Austin": [31, 32],
            "Mexico City": [1,2],
            "Yas Marina": []
        }
        self.test=test
        self.season = season
        self.gp_location = gp_location
        self.race_id = None
        self.dataframes = dataframes
        self.safety_car_laps = safety_car_dict_for_testing.get(gp_location, []) if test else []
        self.number_of_laps = None
        self.drivers_list = []
        self.starting_grid = None
        self.laps_summary = pd.DataFrame(
    columns=["lap", "driver_id", "position", "lap_time", "cumulative_lap_time", "status"],
    dtype=object 
)
        self.outcomes = {}
        self._initialize_parameters(driver_strategies)

    def run(self):
        self._initialize_retirements_and_safety_car()
        
        for lap in range(1, self.number_of_laps + 1):
            for driver in self.drivers_list:
                driver.update_status(lap)  # Ensure DNF status is updated

                if driver.alive:  
                    driver.update_info(lap, self.number_of_laps)
                    lap_time = self._compute_lap_time(driver, lap)
                    pit_stop_time = self._pit_stop(driver, lap)
                    driver.current_lap_time = lap_time + pit_stop_time
                    driver.cumulative_lap_time += driver.current_lap_time
                else:
                    driver.current_lap_time = 0 
                    
            # Update driver positions
            for driver in self.drivers_list:
                if driver.alive:
                    self._get_driver_position(driver)
                else:
                    driver.position = None

            # Save lap data
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
                    # new_row_df = pd.DataFrame([new_row]).dropna(axis=1, how='all')
                    # if not new_row_df.empty:  # Avoid concatenating an empty DataFrame
                    #     self.laps_summary = pd.concat([self.laps_summary, new_row_df.dropna(axis=1, how='all')], ignore_index=True)

                    if any(v is not None and not pd.isna(v) for v in new_row.values()):
                        # Construire la liste des valeurs dans l’ordre des colonnes existantes
                        row_values = [new_row.get(col, pd.NA) for col in self.laps_summary.columns]
                        # Ajouter la ligne en place
                        self.laps_summary.loc[len(self.laps_summary)] = row_values

        # Sorting finishers and DNF drivers
        finishers = [driver for driver in self.drivers_list if driver.alive]
        dnfs = [driver for driver in self.drivers_list if not driver.alive]
        finishers_sorted = sorted(finishers, key=lambda d: d.cumulative_lap_time)
        dnfs_sorted = sorted(dnfs, key=lambda d: d.earliest_dnf_lap if d.earliest_dnf_lap is not None else np.inf)

        total_drivers = len(self.drivers_list)

        for idx, driver in enumerate(finishers_sorted, start=1):
            driver.position = idx

        for idx, driver in enumerate(dnfs_sorted, start=1):
            driver.position = total_drivers - idx + 1  # Rank DNF drivers at the bottom

        outcomes_list = []
        for driver in self.drivers_list:
            outcomes_list.append({
                "driver_id": driver.driver_id,
                "driver_name": driver.name,
                "final_position": driver.position,
                "cumulative_time": driver.cumulative_lap_time,
            })
        self.outcomes = pd.DataFrame(outcomes_list)

    def _initialize_retirements_and_safety_car(self):
        # Deterministic test mode : 
        if self.test:  
            for driver in self.drivers_list:
                self.simulate_dnf_lap(driver)
            return  # For TESTS
        # Probabilistic mode : 
        else:
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
        try:
            if driver.next_pit_stop in driver.pit_stops_info:
                pit_stop_data = driver.pit_stops_info[driver.next_pit_stop]
                is_pit_stop_lap = current_lap == pit_stop_data["pit_stop_lap"]
                is_safety_car_pit_stop = (current_lap in self.safety_car_laps and 
                                          current_lap in range(pit_stop_data["pitstop_interval"][0], pit_stop_data["pitstop_interval"][1] + 1))
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
            print(f"Erreur lors de l'arrêt aux stands pour {driver.name}: {err}")
            return 0.0

    def _get_driver_position(self, driver: Driver):
        sorted_drivers = sorted([drv for drv in self.drivers_list if drv.alive], key=lambda d: d.cumulative_lap_time)
        for idx, drv in enumerate(sorted_drivers, start=1):
            if drv == driver:
                driver.position = idx

    def _initialize_parameters(self, driver_strategies):
        driver_strategies = driver_strategies or {}
        races_df = self.dataframes["races"]
        qualifyings_df = self.dataframes["qualifyings"]
        race_row = races_df[(races_df["season"] == self.season) & (races_df["location"] == self.gp_location)]
        if race_row.empty:
            raise ValueError(f"Aucune course trouvée pour {self.gp_location} en saison {self.season}.")
        self.race_id = race_row["id"].iloc[0]
        self.number_of_laps = race_row.iloc[0]["nolapsplanned"]
        merged_data = qualifyings_df.merge(races_df, left_on="race_id", right_on="id", suffixes=("_qualifying", "_race"))
        qualifying_rows = merged_data[(merged_data["season"] == self.season) & (merged_data["location"] == self.gp_location)]
        if qualifying_rows.empty:
            raise ValueError(f"Aucune donnée de qualification pour {self.gp_location} en saison {self.season}.")
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
        # Deterministic test mode : 
        if self.test: 
            dnf_dict_for_testing = {  # TESTS
                "Austin": {"Kimi Raikkonen": 38, "Max Verstappen": 28, "Esteban Gutierrez": 16, "Nico Hulkenberg": 1},
                "MexicoCity": {"Pascal Wehrlein": 0, "Esteban Ocon": 69},
                "YasMarina": {"Valtteri Bottas": 6, "Kevin Magnussen": 5, "Jenson Button" : 12, "Daniil Kvyat": 14, " Carlos Sainz Jr.": 41}
            }
            
            predefined_dnf_laps = dnf_dict_for_testing.get(self.gp_location, {})
            
            if driver.name in predefined_dnf_laps:
                    driver.earliest_dnf_lap = predefined_dnf_laps[driver.name]
            
        else:
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
            potential = [t for t in [driver.accident_dnf_lap, driver.failure_dnf_lap] if t is not None]
            driver.earliest_dnf_lap = min(potential) if potential else None
