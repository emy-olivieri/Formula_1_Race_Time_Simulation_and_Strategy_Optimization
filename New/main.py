# -*- coding: utf-8 -*-
"""
main.py

Entry point to test the updated Run class: 
- driver retirements determined by simulate_dnf_lap(driver),
- safety car possibly deployed for 5 laps after each retirement with p=0.2
"""

from data_loader import DataLoader
from run import Run

def main():
    db_path = "F1_timingdata_2014_2019.sqlite"
    data_loader = DataLoader(db_path=db_path)
    dataframes = data_loader.load_data()

    driver_strategies = {
        "Lewis Hamilton": {
            1: {
                "compound": "A2",
                "pitstop_interval": [10, 15],
                "pit_stop_lap": 12
            },
            2: {
                "compound": "A3",
                "pitstop_interval": [25, 35],
                "pit_stop_lap": 30
            },
        },
        "Max Verstappen": {
            1: {
                "compound": "A3",
                "pitstop_interval": [8, 18],
                "pit_stop_lap": 10
            },
            2: {
                "compound": "A2",
                "pitstop_interval": [20, 35],
                "pit_stop_lap": 25
            }
        },
    }
    season = 2016
    gp_location = "SaoPaulo"
    race_run = race_run = Run(
        season=season,
        gp_location=gp_location,
        dataframes=dataframes,
        driver_strategies=driver_strategies
    )
    
    race_run.run()
    drivers_names=[drv.name for drv in race_run.drivers_list ]

    print(drivers_names)
    print("\n=== DNF Drivers ===")
    dnf_drivers = [drv for drv in race_run.drivers_list if not drv.alive]
    if not dnf_drivers:
        print("No drivers retired (DNF).")
    else:
        for drv in dnf_drivers:
            print(f"Driver: {drv.name}, DNF lap: {drv.earliest_dnf_lap}")

    # Print the summary and safety car laps
    print("\n=== Laps Summary ===")
    print(race_run.laps_summary)
    print("\nSafety Car Laps:", sorted(race_run.safety_car_laps))

    # Print DNF
    print(race_run.laps_summary[race_run.laps_summary["status"]!="running"])
    print(race_run.laps_summary[race_run.laps_summary["cumulative_lap_time"]>7000])
if __name__ == "__main__":
    main()
