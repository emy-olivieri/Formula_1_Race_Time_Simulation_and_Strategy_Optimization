import logging
from typing import Dict, Any

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from rich.progress import Progress

from data_loader import DataLoader
from run import Run
from spearman_evaluation import SpearmanEvaluation
from rmse_evaluation import RMSEEvaluation
from wilcoxon_evaluation import WilcoxonEvaluation


class MonteCarloSimulator:
    """
    Monte Carlo Simulation for F1 race modeling.
    Runs multiple simulations, compares with real results, evaluates
    statistics, and plots outcomes.
    """

    def __init__(
        self,
        season: int,
        gp_location: str,
        db_path: str,
        driver_strategies: Dict[str, Dict[int, Any]],
        num_simulations: int = 1000,
        test_mode: bool = False,
        starting_grid: list[tuple[int,int]] | None = None,
        verbose: bool = True,
    ) -> None:
        """
        Args:
            season: F1  season year.
            gp_location: GP location.
            db_path: SQLite database path.
            driver_strategies: Dict mapping driver names to pit strategies.
            num_simulations: Number of Monte Carlo runs.
            test_mode: Use deterministic events from the real race if True.
            verbose: Enable INFO logging if True.
        """
        self.season = season
        self.gp_location = gp_location
        self.db_path = db_path
        self.driver_strategies = driver_strategies
        self.num_simulations = num_simulations
        self.test_mode = test_mode

        self.starting_grid = starting_grid

        # Load data once
        loader = DataLoader(db_path=self.db_path)
        self.dataframes = loader.load_data()

        # Placeholders for results
        self.results = []  # type: list[pd.DataFrame]
        self.final_outcomes = pd.DataFrame()
        self.comparison_df = pd.DataFrame()

        # Logger configuration
        self.logger = logging.getLogger(f"MCSim.{self.gp_location}")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            fmt = "[%(levelname)s] %(name)s: %(message)s"
            handler.setFormatter(logging.Formatter(fmt))
            self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO if verbose else logging.WARNING)

    def run_simulation(self) -> None:
        """Run the Monte Carlo simulations and aggregate outcomes."""
        self.logger.info(
            "Simulating %d races for %s %d",
            self.num_simulations, self.gp_location, self.season
        )

        # Clear previous results
        self.results.clear()

        with Progress() as progress:
            task = progress.add_task(
                "[cyan]Running simulations...", total=self.num_simulations
            )
            for _ in range(self.num_simulations):
                sim = Run(
                    season=self.season,
                    gp_location=self.gp_location,
                    dataframes=self.dataframes,
                    driver_strategies=self.driver_strategies,
                    test_mode=self.test_mode,
                    starting_grid=self.starting_grid,
                )
                sim.run()
                self.results.append(sim.outcomes)
                progress.update(task, advance=1)

        self.final_outcomes = pd.concat(self.results, ignore_index=True)
        self.logger.info("Simulations completed.")

    def compare_outcomes(self) -> pd.DataFrame:
        """
        Compare simulated averages to actual race results.

        Returns:
            DataFrame with columns:
                driver_id,
                final_position_sim,
                cumulative_time_sim,
                final_position_actual,
                cumulative_time_actual
        """
        if self.final_outcomes.empty:
            self.logger.error("No simulation data to compare.")
            return pd.DataFrame()

        races = self.dataframes["races"]
        race = races[
            (races["season"] == self.season)
            & (races["location"] == self.gp_location)
        ]
        if race.empty:
            self.logger.error("Race not found in data.")
            return pd.DataFrame()
        race_id = int(race["id"].iloc[0])

        # Simulated averages
        sim_df = (
            self.final_outcomes
            .groupby("driver_id", as_index=False)
            .agg(
                final_position_sim=("final_position", "mean"),
                cumulative_time_sim=("cumulative_time", "mean"),
            )
        )

        # Actual positions
        sf = self.dataframes["starterfields"]
        actual_pos = (
            sf[sf["race_id"] == race_id]
            .rename(columns={"resultposition": "final_position_actual"})
            [["driver_id", "final_position_actual"]]
        )

        # Actual cumulative times
        laps = self.dataframes["laps"]
        last_laps = (
            laps[laps["race_id"] == race_id]
            .groupby("driver_id", as_index=False)["lapno"]
            .max()
        )
        actual_time = (
            laps[laps["race_id"] == race_id]
            .merge(last_laps, on=["driver_id", "lapno"], how="inner")
            .rename(columns={"racetime": "cumulative_time_actual"})
            [["driver_id", "cumulative_time_actual"]]
        )

        # Merge
        self.comparison_df = (
            sim_df
            .merge(actual_pos,   on="driver_id", how="right")
            .merge(actual_time,  on="driver_id", how="right")
            .sort_values("final_position_sim")
            .reset_index(drop=True)
        )
        self.logger.info("Comparison DataFrame is ready.")
        return self.comparison_df

    def evaluate_statistics(self) -> Dict[str, Any]:
        """
        Perform Wilcoxon and Spearman tests.

        Returns:
            Dict with keys 'wilcoxon' and 'spearman' mapping to test results.
        """
        if self.comparison_df.empty:
            self.logger.error("No comparison data for statistical tests.")
            return {}

        self.logger.info("Running RMSE ...")
        rmse_res = RMSEEvaluation(
            actual_data=self.comparison_df["cumulative_time_actual"],
            simulated_data=self.comparison_df["cumulative_time_sim"],
        ).evaluate()

        self.logger.info("Running Wilcoxon test...")
        wil_res = WilcoxonEvaluation(
            actual_data=self.comparison_df["cumulative_time_actual"],
            simulated_data=self.comparison_df["cumulative_time_sim"],
        ).evaluate()

        self.logger.info("Running Spearman correlation...")
        spr_res = SpearmanEvaluation(
            actual_data=self.comparison_df["final_position_actual"],
            simulated_data=self.comparison_df["final_position_sim"],
        ).evaluate()

        return {"wilcoxon": wil_res, "RMSE": rmse_res, "spearman": spr_res}

    def plot_results(self) -> None:
        """
        Plot the results of the simulations and comparisons."""
        df = self.comparison_df

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        ax1.scatter(df["cumulative_time_actual"], df["cumulative_time_sim"])
        max_val = max(df["cumulative_time_actual"].max(), df["cumulative_time_sim"].max())
        ax1.plot([0, max_val], [0, max_val], linestyle="--")
        ax1.set_xlabel("Cumulative Time Actual")
        ax1.set_ylabel("Cumulative Time Simulated")
        ax1.set_title("Simulated vs Actual Cumulative Times")

        drivers = df["driver_id"].astype(str)
        x = np.arange(len(drivers))
        width = 0.35
        ax2.bar(x - width/2, df["final_position_actual"], width, label="Actual")
        ax2.bar(x + width/2, df["final_position_sim"], width, label="Simulated")
        ax2.set_xticks(x)
        ax2.set_xticklabels(drivers, rotation=90)
        ax2.set_ylabel("Position")
        ax2.set_title("Actual vs Simulated Positions")
        ax2.legend()

        fig.tight_layout()
        plt.show()

    def summarize(self) -> Dict[str, Any]:
        """
        Full pipeline: compare outcomes, evaluate stats, plot.
        
        Returns:
            Statistical test results dict.
        """
        self.compare_outcomes()
        # stats = self.evaluate_statistics()
        # self.plot_results()
        # return stats
        return

