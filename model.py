import pandas as pd
import statsmodels.formula.api as smf

class Model:    

    def __init__(self, driver_id, race, dataframes):
        self.driver_id = driver_id
        self.race = race
        self.dfs = dataframes

    def clean_data(self):
        """
        Keep only races where the status in starterfields is 'F' (Finished).
        """
        laps = self.dfs['laps']
        laps=laps[laps["driver_id"] == self.driver_id]
        starterfields = self.dfs['starterfields']
        starterfields=starterfields[starterfields["driver_id"] == self.driver_id]
        finished_races = starterfields[starterfields['status'] == 'F']
        self.dfs['laps'] = laps[(laps['race_id'].isin(finished_races['race_id']))]
        print(self.dfs['laps'])
        qualif_laps = self.dfs["qualifyings"]
        qualif_laps=qualif_laps[qualif_laps["driver_id"] == self.driver_id]
        self.dfs['qualifying'] = qualif_laps[(qualif_laps['race_id'].isin(finished_races['race_id']))]

    def get_best_qualif_time(self):
        qualif_laps = self.dfs["qualifyings"]
        self.best_qualif_times = (
            qualif_laps[["race_id", "q1laptime", "q2laptime", "q3laptime"]]
            .groupby("race_id")
            .min()
            .min(axis=1)
        
        
        )

    def get_train_laps_time(self):
        laps = self.dfs["laps"]
        self.train_laps_time = laps[
           (laps["race_id"] < self.race)
        ].merge(self.best_qualif_times, on="race_id", how="left")

    def get_test_laps_time(self):
        laps = self.dfs["laps"]
        self.test_laps_time = laps[
            (laps["race_id"] == self.race)
        ].merge(self.best_qualif_times, on="race_id", how="left")

    def add_columns(self):
        self.train_laps_time = self.train_laps_time.reset_index(drop=True)
        self.test_laps_time = self.test_laps_time.reset_index(drop=True)

        self.train_laps_time['fuelc'] = (
            100 - (100 / self.train_laps_time.groupby('race_id')['lapno'].transform('max')) * self.train_laps_time['lapno']
        )
        self.test_laps_time['fuelc'] = (
            100 - (100 / self.test_laps_time.groupby('race_id')['lapno'].transform('max')) * self.test_laps_time['lapno']
        )

    def estimate_parameters(self):
        formula = "laptime ~ -1+best_qualif_time + fuelc + C(compound) + C(compound):tireage + C(compound):I(tireage**2) "
        combined_data = pd.concat([self.train_laps_time, self.test_laps_time], ignore_index=True)
        model = smf.ols(formula=formula, data=combined_data).fit()
        print(model.summary())
