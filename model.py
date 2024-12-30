class Model:
    

    def __init__(self,driver_id,race,dataframes):
        self.driver_id=driver_id
        self.race=race
        self.dfs=dataframes

    def get_best_qualif_time(self):
        qualif_laps=self.dfs["qualifyings"][self.dfs["qualifyings"]["driver_id"]==self.driver_id]
        self.best_qualif_time=qualif_laps[["q1laptime","q2laptime","q2laptime"]].min().min()

    def get_train_laps_time(self):
        laps=self.dfs["laps"]
        driver_train_laps=laps[(laps["driver_id"]==self.driver_id) & (laps["race_id"].isin([i for i in range(1,self.race)]))]
        self.train_laps_time=driver_train_laps

    def get_laps_time_test(self):
        laps=self.dfs["laps"]
        driver_train_laps=laps[(laps["driver_id"]==self.driver_id) & (laps["race_id"]==self.race)]
        self.train_laps_time=driver_train_laps

    def estimate_parameters(self):
        pass

