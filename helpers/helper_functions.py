import pandas as pd 

def generate_pit_stop_strategy(season: int, location: str, dataframes: dict):
    """
    Generates pit stop strategies for each driver in a given season and location.
    
    Args:
        season (int): The racing season.
        location (str): Grand Prix location.
        dataframes (dict): Dictionary containing race-related data.
    
    Returns:
        dict: Pit stop strategies for each driver.
    """
    # Load required data from the dataframes
    df_pit_stops = dataframes.get("laps", pd.DataFrame())
    df_races = dataframes.get("races", pd.DataFrame())
    df_drivers = dataframes.get("drivers", pd.DataFrame())
    
    # Find the race ID for the given season and location
    race_row = df_races[(df_races["season"] == season) & (df_races["location"] == location)]
    if race_row.empty:
        raise ValueError(f"No race found for location '{location}' in season {season}.")
    
    race_id = race_row.iloc[0]["id"]
    
    # Filter pit stop data for the selected race
    pit_stop_data = df_pit_stops[df_pit_stops["race_id"] == race_id]
    
    # Extract unique drivers from the filtered data
    drivers = pit_stop_data["driver_id"].unique()
    
    pit_stop_strategies = {}
    
    for driver_id in drivers:
        driver_pit_stops = pit_stop_data[pit_stop_data["driver_id"] == driver_id]
        driver_name = df_drivers[df_drivers["id"] == driver_id]["name"].values[0]
        
        # Find the starting tire compound and tire age (lap 0)
        starting_tire = driver_pit_stops[driver_pit_stops["lapno"] == 0]
        if not starting_tire.empty:
            starting_compound = starting_tire.iloc[0]["compound"]
            starting_tire_age = starting_tire.iloc[0]["tireage"]
        else:
            starting_compound = "Unknown"
            starting_tire_age = "Unknown"
        
        strategy = {"starting_compound": starting_compound, "starting_tire_age": starting_tire_age}
        
        # Filter only actual pit stops (where pitstopduration is not NaN or zero)
        valid_pit_stops = driver_pit_stops[driver_pit_stops["pitstopduration"].notna() & (driver_pit_stops["pitstopduration"] > 0)]
        
        for idx, (lap, duration, compound, tireage) in enumerate(
            zip(valid_pit_stops["lapno"], valid_pit_stops["pitstopduration"], valid_pit_stops["compound"], valid_pit_stops["tireage"])
        ):
            pitstop_interval = [lap,lap]
            strategy[idx+1] = {
                "compound": compound,
                "pitstop_interval": pitstop_interval,
                "pit_stop_lap": lap,
                "tire_age": tireage
            }
        
        pit_stop_strategies[driver_name] = strategy

        for idx, (lap, compound, tireage) in enumerate(
            zip(valid_pit_stops["lapno"], valid_pit_stops["compound"], valid_pit_stops["tireage"])
        ):
            strategy[idx + 1] = {
                "compound": compound,
                "pitstop_interval": [lap, lap],
                "pit_stop_lap": lap,
                "tire_age": tireage,
            }

        pit_stop_strategies[driver_name] = strategy
    
    return pit_stop_strategies
