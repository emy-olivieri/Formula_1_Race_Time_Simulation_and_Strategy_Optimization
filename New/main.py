# main.py
from data_loader import DataLoader
from run import Run

def main():
    db_path = "F1_timingdata_2014_2019.sqlite"
    data_loader = DataLoader(db_path=db_path)
    dataframes = data_loader.load_data()

    season = 2016
    driver_strategies = {
        'Lewis Hamilton': {'starting_compound': 'A3', 'starting_tire_age': 2},
        'Nico Rosberg': {'starting_compound': 'A3', 'starting_tire_age': 2},
        # Stratégies supplémentaires pour les autres pilotes...
    }
    gp_location = "Austin"

    race_run = Run(
        season=season,
        gp_location=gp_location,
        dataframes=dataframes,
        driver_strategies=driver_strategies
    )
    
    race_run.run()
    drivers_names = [drv.name for drv in race_run.drivers_list]
    print("Pilotes participants :", drivers_names)
    print("\n=== Pilotes en DNF ===")
    dnf_drivers = [drv for drv in race_run.drivers_list if not drv.alive]
    if not dnf_drivers:
        print("Aucun pilote retiré (DNF).")
    else:
        for drv in dnf_drivers:
            print(f"Driver: {drv.name}, DNF lap: {drv.earliest_dnf_lap}")
    print("\n=== Résumé des tours ===")
    print(race_run.laps_summary)
    print("\nSafety Car Laps:", sorted(race_run.safety_car_laps))

if __name__ == "__main__":
    main()
