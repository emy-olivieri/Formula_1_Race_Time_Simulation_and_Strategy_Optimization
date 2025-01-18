
class Run:
    def __init__(self, season, race_name, dataframes):
        self.season = season
        self.race_name = race_name
        self.dfs = dataframes

        self.number_of_laps = None        # Nombre de tours (nolapsplanned)
        self.drivers_list = []           # On stockera ici des objets Driver
        self.starting_grid = None        # Grille de départ (positions)

        # DataFrame récap
        self.laps_recap = pd.DataFrame(
            columns=["tour", "driver_id", "position", "lapTime", "cumul_lap_time"]
        )

    def get_parameters_for_simulation(self):
        """
        Récupère les paramètres nécessaires pour la simulation :
          - Nombre de tours (self.number_of_laps) depuis 'races'
          - Liste des pilotes instanciés (self.drivers_list)
          - Grille de départ (self.starting_grid) depuis 'qualifyings'
        """

        # ------------------------------------------------------------------
        # 1) Récupérer le nombre de tours depuis 'races'
        # ------------------------------------------------------------------
        races_df = self.dfs["races"]
        race_row = races_df[
            (races_df["location"] == self.race_name) &
            (races_df["season"] == self.season)
        ]
        if race_row.empty:
            raise ValueError(f"Pas de course trouvée pour '{self.race_name}' en {self.season}.")

        self.number_of_laps = race_row["nolapsplanned"].iloc[0]

        # ------------------------------------------------------------------
        # 2) Fusion qualifier -> Pour récupérer tous les pilotes + positions
        # ------------------------------------------------------------------
        qualifyings_df = self.dfs["qualifyings"]

        merged_q = qualifyings_df.merge(
            races_df,
            left_on="race_id",
            right_on="id",
            suffixes=("_q", "_races")
        )
        merged_filtered = merged_q[
            (merged_q["season"] == self.season) &
            (merged_q["location"] == self.race_name)
        ]
        if merged_filtered.empty:
            raise ValueError(f"Pas de qualifications trouvées pour '{self.race_name}' ({self.season}).")

        # Tri pour la grille de départ
        q_sorted = merged_filtered.sort_values(by="position")

        # On construit self.starting_grid comme une liste de tuples (driver_id, position)
        self.starting_grid = list(zip(q_sorted["driver_id"], q_sorted["position"]))

        # ------------------------------------------------------------------
        # 3) Instancier la liste de Driver
        # ------------------------------------------------------------------
        # d_id_list => liste unique des driver_id
        d_id_list = merged_filtered["driver_id"].unique().tolist()

        # On récupère le DataFrame "drivers" pour faire la correspondance ID -> name
        drivers_df = self.dfs["drivers"]

        for d_id in d_id_list:
            # On cherche le nom du pilote correspondant à ce d_id
            row_driver = drivers_df[drivers_df["id"] == d_id]
            if row_driver.empty:
                continue  # Ou lever une exception, selon votre logique

            driver_name = row_driver["name"].iloc[0]

            # On crée un objet Driver
            driver_obj = Driver(
                season=self.season,
                dataframes=self.dfs,
                name=driver_name
            )

            # On appelle sa méthode get_driver_parameters()
            driver_obj.get_driver_parameters()

            # On ajoute l'objet driver à la liste
            self.drivers_list.append(driver_obj)

        # ------------------------------------------------------------------
        # 4) Affichage pour debug
        # ------------------------------------------------------------------
        print(f"GP : {self.race_name}, saison : {self.season}")
        print(f"Nombre de tours : {self.number_of_laps}")
        print(f"Grille de départ : {self.starting_grid}")
        print("Pilotes instanciés :", [d.name for d in self.drivers_list])

        # (Optionnel) Retourner self.drivers_list si besoin


    # def run(self):

        
    #     # # Creer un objet Race (attribut = Recap_Tour / Positions -> liste / Drivers_Alive  -> dico / Safety_Car_Laps -> liste ... )
    #     # # Methodes (compute_lap_time(Driver, lap_number) -> cette fonction check si y'a une SC et si le driver est alive et lance le modele / Change les attributs de positions)
    #     self.get_parameters_for_simulation()
    #     # for i in range(1,no_laps+1) : 
    #     #     for driver in list_all_driver :  (list_all_driver est une liste d'objets driver)
    #     #         driver.change_status(i)
    #     #         # Normal Lap
    #     #         time = self.compute_lap_time(driver, i)
    #     #         driver.cumul_time += time
    #     #         # Pit stop :
    #     #         driver.cumul_time += self.pit_stop(driver)
    #                 # driver.update_info()

    #         # # Overtaking
    #         # # Aggrémenter le recap des tours
    #     print("Winner  :  ")
    #     return(self.laps_recap)  

  

        
    
    # def DNF_nolap(self,driver):

    #     finish=True
    #     # Accident :
    #     if loi de bernouilli(driver.p)== 1: 
    #         driver.no_lap_accident=np.randint(self.number_of_laps)

    #     # Failures :
    #     if loi de bernouilli(driver.p)== 1: 
    #         driver.no_lap_failures=np.randint(self.number_of_laps)
        
    #     driver.min_no_laps_DNF=min(driver.no_lap_accident,driver.no_lap_failures) ## Vérifier si ça marche avec le None sinon modifier
    

    # def pit_stop(self,driver):
    #     #     Dico ={1: { "compound" : , "pitstop_interval" :, "pit_stop_lap" : aléatoire dans pitstop_interval}} # Le dico est un input et sera mis dans driver.pit_stops_informations
    #     # - Check si i == pitstop_lap : # Récupérer pit_stop_lap dans le dico
            
    #     #     driver.age_tire = 0
    #     #     driver.compound = # dans le dico de strategy avec la clé [driver.next_pitstop] et la deuxième clé [compound] 
    #     #     driver.cumul_time += driver.team.calculate_pit_stop_time() # Driver a un attribut qui est un objet Team de la classe Team 
    #     #     driver.next_pitstop += 1
    #     # - check si i isin race.Safety_car_laps and i isin pitstop_interval : 
    #     #     pitstop_lap = i # Changer la valeur dans le dico
    #     #     driver.age_tire = 0
    #     #     driver.compound = # dans le dico de strategy avec la clé [driver.next_pitstop] et la deuxième clé [compound] 
    #     #     driver.cumul_time += driver.team.calculate_pit_stop_time() # Driver a un attribut qui est un objet Team de la classe Team 
    #     #     driver.next_pitstop += 1 


    # def compute_lap_time(self,driver,nolap):
    #     lap_time=0
    #     if driver.alive:
    #         # FUel & TIre Model
    #         model=driver.model
    #         data_for_predictions=driver.select_features(nolap)
    #         lap_time+=model.predict(data_for_predictions) # Fuel level, tire age, coupound

    #     if nolap.isin(self.safetycar_laps):
    #         lap_time*=1.2

    #     return(lap_time)

if __name__ == "__main__":
    # 1) Importations nécessaires
    import sqlite3
    import pandas as pd
    
    # Supposons que vous avez le code suivant importé ou défini dans le même fichier :
    # - DataLoader
    # - Driver
    # - Run
    
    # 2) Créer le DataLoader et charger les DataFrames
    data_loader = DataLoader(db_path="F1_timingdata_2014_2019.sqlite")
    dataframes = data_loader.load_data()

    # 3) Choisir une saison et un nom de GP
    #    Assurez-vous que la table 'races' contient bien un 'location' = "SaoPaulo" pour la saison 2019
    season_test = 2019
    race_name_test = "SaoPaulo"

    # 4) Instancier l'objet Run
    run_simulation = Run(
        season=season_test,
        race_name=race_name_test,
        dataframes=dataframes
    )

    # 5) Appeler get_parameters_for_simulation()
    run_simulation.get_parameters_for_simulation()

    # 6) Vérifier ce qui est récupéré
    print("\n=== Test de la classe Run ===")
    print("Nom de la course  :", race_name_test)
    print("Saison            :", season_test)
    print("Nombre de tours   :", run_simulation.number_of_laps)
    print("Grille de départ  :", run_simulation.starting_grid)
    print("Pilotes instanciés:")

    # run_simulation.drivers_list est une liste d'objets Driver
    for d in run_simulation.drivers_list:
        print(f" - {d.name} (ID={d.driver_id}) | Team={d.team}")
    
    # 7) Affichage du laps_recap (pour l'instant, probablement vide)
    print("\nDataFrame laps_recap :")
    print(run_simulation.laps_recap)
    
    print("\n=== Fin du test ===")

