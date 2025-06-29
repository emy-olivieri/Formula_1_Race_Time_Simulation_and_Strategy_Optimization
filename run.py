import numpy as np
import pandas as pd
from pit_stop import PitStop
from driver import Driver
import logging

from pit_stop import PitStop
from driver import Driver


class Run:
    """
    Orchestrates a single Grand Prix race simulation for a given season,
    track location, and preprocessed data.

    Attributes:
        season (int): Racing season year.
        gp_location (str): Grand Prix location name.
        test_mode (bool): If True, injects deterministic DNF and safety car events.
        race_id (int): Identifier of the race in the database.
        number_of_laps (int): Total laps planned for the race.
        safety_car_laps (list[int]): Laps under safety car conditions.
        drivers_list (list[Driver]): List of Driver instances participating.
        laps_summary (pd.DataFrame): Detailed lap-by-lap summary DataFrame.
        outcomes (pd.DataFrame): Final classification of drivers.
    """

    def __init__(
        self,
        season: int,
        gp_location: str,
        dataframes: dict,
        driver_strategies: dict = None,
        starting_grid: list[tuple[int,int]] | None = None,
        test_mode: bool = False,
    ) -> None:
        """
        Initialize simulation parameters and load starting grid.

        Args:
            season: The season year.
            gp_location: Track name.
            dataframes: Preprocessed tables (races, laps, etc.).
            driver_strategies: Dict mapping driver names to pit strategies.
            test_mode: If True, use deterministic events for testing.
        """

        self.season = season
        self.gp_location = gp_location
        self.test_mode = test_mode
        self.dataframes = dataframes
        self.driver_strategies = driver_strategies or {}

        self.race_id: int = None
        self.number_of_laps: int = 0

        # Load race parameters (race_id, number_of_laps)
        self._get_race_parameters()

        # Determine the starting grid
        if starting_grid is not None:
            self.starting_grid = starting_grid
        else:
            self.starting_grid = self._build_starting_grid()

        self.drivers_list: list[Driver] = []

        # Predefined safety car laps for deterministic testing
        sc_dict = {
            "Suzuka": [],
            "Austin": [31, 32],
            "MexicoCity": [1, 2],
            "YasMarina": []
        }
        self.safety_car_laps = sc_dict.get(self.gp_location, []) if self.test_mode else []
        
        # Initialize empty laps summary
        self.laps_summary = pd.DataFrame(
            columns=["lap", "driver_id", "position", "lap_time", "cumulative_lap_time", "status"],
            dtype=object
        )

        self.outcomes = pd.DataFrame()

        # Logger setup
        self.logger = logging.getLogger(f"Run.{self.gp_location}")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
            self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

        # Create driver instances
        self._initialize_drivers()

    def run(self) -> None:
        """
        Execute the race simulation: DNF handling, lap loops, pit stops,
        position updates, and final classification.
        """
        # Initialize DNF and safety car events
        self._initialize_retirements_and_safety_car()

        # Add starting grid time penalties
        self._add_starting_grid_time()

        for lap in range(1, self.number_of_laps + 1):
            for driver in self.drivers_list:
                driver.update_status(lap)
                if driver.alive:
                    driver.update_info(lap, self.number_of_laps)
                    lap_time = self._compute_lap_time(driver, lap)
                    pit_time = self._pit_stop(driver, lap)
                    driver.current_lap_time = lap_time + pit_time
                    driver.cumulative_lap_time += driver.current_lap_time
                else:
                    driver.current_lap_time = 0

            # Update positions
            for driver in self.drivers_list:
                if driver.alive:
                    self._get_driver_position(driver)
                else:
                    driver.position = None

            # Record lap summary
            for driver in self.drivers_list:
                if driver.alive or driver.earliest_dnf_lap == lap:
                    status = "running" if driver.alive else "DNF"
                    row = {
                        "lap": lap,
                        "driver_id": driver.driver_id,
                        "position": driver.position,
                        "lap_time": driver.current_lap_time,
                        "cumulative_lap_time": driver.cumulative_lap_time,
                        "status": status,
                    }
                    # Only add if any value non-null
                    if any(v is not None and not pd.isna(v) for v in row.values()):
                        self.laps_summary.loc[len(self.laps_summary)] = [
                            row.get(col, pd.NA) for col in self.laps_summary.columns
                        ]

        # Final classification
        finishers = sorted(
            [d for d in self.drivers_list if d.alive],
            key=lambda d: d.cumulative_lap_time
        )
        dnfs = sorted(
            (d for d in self.drivers_list if not d.alive),
            key=lambda d: d.earliest_dnf_lap or np.inf,
            reverse=True
        )

        
        # Assign positions
        for pos, d in enumerate(finishers, 1):
            d.position = pos
        for pos, d in enumerate(dnfs, 1):
            d.position = pos+ len(finishers)

        # Build outcomes DataFrame
        self.outcomes = pd.DataFrame([
            {
                "driver_id": d.driver_id,
                "driver_name": d.name,
                "final_position": d.position,
                "cumulative_time": d.cumulative_lap_time,
            }
            for d in self.drivers_list
        ])
        self.logger.info(f"Race simulation for {self.gp_location} in {self.season} completed.")

    def _add_starting_grid_time(self) -> None:
        """Add starting grid times to cumulative_lap_time according to the position."""
        t_per_grid_pos = 0.25 # Time penalty per grid position (in seconds) from Phillips' model
        for driver_id, position in self.starting_grid:
            driver = next((d for d in self.drivers_list if d.driver_id == driver_id), None)
            if driver is not None:
                driver.cumulative_lap_time += position * t_per_grid_pos
            else:
                self.logger.warning(f"Driver ID {driver_id} not found in drivers_list.")

    def _add_reaction_time_to_starting_grid(self) -> None:
        """
        Adds the reaction time to the starting grid.
        This is a placeholder for future implementation.
        """
        pass

    def _build_starting_grid(self) -> list[tuple[int,int]]:
        """
        Construct the starting grid by combining qualifying order and any missing drivers.
        Missing drivers are ordered alphabetically by name.

        Returns:
            List of (driver_id, grid_position).
        """
        quals = self.dataframes["qualifyings"]
        sf = self.dataframes["starterfields"]
        drivers_df = self.dataframes["drivers"]

        # 1) Main grid from qualifying
        qual_grid = (
            quals[quals["race_id"] == self.race_id]
            .sort_values("position")
            .loc[:, ["driver_id", "position"]]
        )
        max_pos = int(qual_grid["position"].max()) if not qual_grid.empty else 0

        # 2) Detect missing drivers
        entered = set(
            sf[sf["race_id"] == self.race_id]["driver_id"].unique()
        )
        missing = entered - set(qual_grid["driver_id"])

        if missing:
            # Order missing by driver name
            missing_df = (
                drivers_df[drivers_df["id"].isin(missing)]
                .loc[:, ["id", "name"]]
                .sort_values("name")
            )
            extra = pd.DataFrame({
                "driver_id": missing_df["id"].values,
                "position": max_pos + np.arange(1, len(missing_df) + 1)
            })
            qual_grid = pd.concat([qual_grid, extra], ignore_index=True)

        # Return as list of tuples
        return list(zip(qual_grid["driver_id"], qual_grid["position"]))

    def _get_race_parameters(self) -> None:
        """
        Load race_id and number_of_laps from the races table.
        """
        races = self.dataframes["races"]
        race = races[
            (races["season"] == self.season)
            & (races["location"] == self.gp_location)
        ]
        if race.empty:
            raise ValueError(
                f"No race for {self.gp_location}, season {self.season}."
            )
        self.race_id = race["id"].iloc[0]
        self.number_of_laps = race["nolapsplanned"].iloc[0]
        
    def _initialize_drivers(self) -> None:
        """Instantiate Driver objects based on starting grid and strategies."""
        drivers_df = self.dataframes["drivers"]
        for driver_id, _ in self.starting_grid:
            row = drivers_df[drivers_df["id"] == driver_id]
            if row.empty:
                continue
            name = row["name"].iloc[0]
            strat = self.driver_strategies.get(name, {})
            drv = Driver(
                season=self.season,
                race_id=self.race_id,
                dataframes=self.dataframes,
                name=name,
                strategy=strat,
            )
            self.drivers_list.append(drv)

    def _initialize_retirements_and_safety_car(self) -> None:
        """
        Determine earliest DNF lap per driver and optionally inject safety car phases.
        """
        if self.test_mode:
            for d in self.drivers_list:
                self.simulate_dnf_lap(d)
            return

        p_sc = 0.2 # Probability of safety car
        sc_dur = 5 # Duration of safety car in laps
        for d in self.drivers_list:
            self.simulate_dnf_lap(d)
            dnf_lap = d.earliest_dnf_lap
            if dnf_lap and np.random.rand() < p_sc:
                sc_end = min(dnf_lap + sc_dur - 1, self.number_of_laps)
                for lap in range(dnf_lap, sc_end + 1):
                    if lap not in self.safety_car_laps:
                        self.safety_car_laps.append(lap)

    def _compute_lap_time(self, driver: Driver, current_lap: int) -> float:
        """Compute a single lap time including fuel/tire model and safety car."""
        feats = pd.DataFrame({
            "fuelc": [driver.fuelc],
            "compound": [driver.compound],
            "tireage": [driver.tire_age],
        })
        base = driver.fuel_tire_model.predict(feats).iloc[0]
        var = 0 if self.test_mode else np.random.normal(0, driver.variability)
        lt = driver.best_qualif_time + base + var
        return lt * 1.2 if current_lap in self.safety_car_laps else lt

    def _pit_stop(self, driver: Driver, current_lap: int) -> float:
        """Handle pit stop logic, calculate duration if stopping this lap."""
        try:
            nps = driver.next_pit_stop
            if nps in driver.pit_stops_info:
                data = driver.pit_stops_info[nps]
                exact = current_lap == data["pit_stop_lap"]
                window = current_lap in range(*data["pitstop_interval"])
                if exact or window:
                    ps = PitStop(
                        team=driver.team,
                        gp_location=self.gp_location,
                        season=self.season,
                        dataframes=self.dataframes,
                    )
                    ps.calculate_best_pit_stop_duration()
                    dur = ps.calculate_pit_stop_duration()
                    driver.tire_age = data["tire_age"]
                    driver.compound = data["compound"]
                    driver.next_pit_stop += 1
                    return dur
        except ValueError as e:
            self.logger.error(f"Pit stop error for {driver.name}: {e}")
        return 0.0

    def _get_driver_position(self, driver: Driver) -> None:
        """Assign current position based on cumulative lap time among alive drivers."""
        alive = sorted(
            [d for d in self.drivers_list if d.alive],
            key=lambda d: d.cumulative_lap_time
        )
        for idx, d in enumerate(alive, 1):
            if d == driver:
                driver.position = idx

    def simulate_dnf_lap(self, driver: Driver) -> None:
        """
        Determine deterministic or probabilistic DNF lap for a driver.
        """
        if self.test_mode:
            test_dnfs = {
                "Austin": {"Kimi Raikkonen": 38, "Max Verstappen": 28, "Esteban Gutierrez": 16, "Nico Hulkenberg": 1},
                "MexicoCity": {"Esteban Ocon": 69, "Pascal Wehrlein": 0},
                "YasMarina": {"Carlos Sainz Jnr" :41, "Daniil Kvyat" : 14, "Jenson Button" : 12, "Valtteri Bottas": 6,"Kevin Magnussen": 5},
            }
            mapping = test_dnfs.get(self.gp_location, {})
            if driver.name in mapping:
                driver.earliest_dnf_lap = mapping[driver.name]
        else:
            acc = np.random.binomial(1, driver.accident_dnf_probability)
            fl = np.random.binomial(1, driver.failure_dnf_probability)
            a_lap = np.random.randint(1, self.number_of_laps + 1) if acc else None
            f_lap = np.random.randint(1, self.number_of_laps + 1) if fl else None
            laps = [lap for lap in (a_lap, f_lap) if lap]
            driver.earliest_dnf_lap = min(laps) if laps else None
