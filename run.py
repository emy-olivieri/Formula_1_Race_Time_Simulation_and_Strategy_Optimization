
class Run():
    def __init__(self, season, race, dataframes):
        self.number_of_laps = None # Recuperer dans le dataframe races (nolapsplanned)
        self.starting_grid = None # Recuperer dans le dataframe qualifyings (positions) 
        self.dfs = dataframes

    
    def get_parameters_for_simulation(self) :
        #DNF PROBA / 
        #for drivers in list de driver :
            #Driver.get_parameters() -> DNF PROBA, et tour de dnf, Coefficient de la regression, Pitstop_duration

    def run(self):

        
        # Creer un objet Race (attribut = Recap_Tour / Positions -> liste / Drivers_Alive  -> dico / Safety_Car_Laps -> liste ... )
        # Methodes (compute_lap_time(Driver, lap_number) -> cette fonction check si y'a une SC et si le driver est alive et lance le modele / Change les attributs de positions)
        
        '''
        for i in range(no_laps) : 
            for driver in list_all_driver :  (list_all_driver est une liste d'objets driver)
                time = Race.compute_lap_time(driver, i)
                driver.cumul_time += time
                driver.pit_stop() -> 
                     - Check si i == pitstop_lap :
                        driver.next_pitstop += 1
                        drive.age_tire =
                        driver.compound =
                        driver.cumul_time += pitstop_duration
                     - check si i isin race.Safety_car_laps and i isin pitstop_interval : 
                        pitstop_lap = i #
                        driver.next_pitstop += 1 
                        drive.age_tire =
                        driver.compound =
                        driver.cumul_time += pitstop_duration 

            ## Overtaking

        '''


