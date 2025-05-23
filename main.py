from monte_carlo_simulator import MonteCarloSimulator

if __name__ == "__main__":
    db_path = "data/F1_timingdata_2014_2019.sqlite"
    season = 2016
    driver_strategies = {
            'Lewis Hamilton': {'starting_compound': 'A3',
                            'starting_tire_age': 2,
                            1: {'compound': 'A3',
                                'pitstop_interval': [11, 11],
                                'pit_stop_lap': 11,
                                'tire_age': 13},
                            2: {'compound': 'A3',
                                'pitstop_interval': [31, 31],
                                'pit_stop_lap': 31,
                                'tire_age': 20}},
            'Nico Rosberg': {'starting_compound': 'A3',
                            'starting_tire_age': 2,
                            1: {'compound': 'A3',
                                'pitstop_interval': [10, 10],
                                'pit_stop_lap': 10,
                                'tire_age': 12},
                            2: {'compound': 'A2',
                                'pitstop_interval': [31, 31],
                                'pit_stop_lap': 31,
                                'tire_age': 21}},
            'Daniel Ricciardo': {'starting_compound': 'A4',
                                'starting_tire_age': 2,
                                1: {'compound': 'A4',
                                    'pitstop_interval': [8, 8],
                                    'pit_stop_lap': 8,
                                    'tire_age': 10},
                                2: {'compound': 'A3',
                                    'pitstop_interval': [25, 25],
                                    'pit_stop_lap': 25,
                                    'tire_age': 17}},
            'Max Verstappen': {'starting_compound': 'A3',
                            'starting_tire_age': 2,
                            1: {'compound': 'A3',
                                'pitstop_interval': [9, 9],
                                'pit_stop_lap': 9,
                                'tire_age': 11},
                            2: {'compound': 'A3',
                                'pitstop_interval': [26, 26],
                                'pit_stop_lap': 26,
                                'tire_age': 17}},
            'Kimi Raikkonen': {'starting_compound': 'A4',
                            'starting_tire_age': 2,
                            1: {'compound': 'A4',
                                'pitstop_interval': [8, 8],
                                'pit_stop_lap': 8,
                                'tire_age': 10},
                            2: {'compound': 'A3',
                                'pitstop_interval': [24, 24],
                                'pit_stop_lap': 24,
                                'tire_age': 16},
                            3: {'compound': 'A4',
                                'pitstop_interval': [38, 38],
                                'pit_stop_lap': 38,
                                'tire_age': 14}},
            'Sebastian Vettel': {'starting_compound': 'A4',
                                'starting_tire_age': 2,
                                1: {'compound': 'A4',
                                    'pitstop_interval': [14, 14],
                                    'pit_stop_lap': 14,
                                    'tire_age': 16},
                                2: {'compound': 'A3',
                                    'pitstop_interval': [29, 29],
                                    'pit_stop_lap': 29,
                                    'tire_age': 15},
                                3: {'compound': 'A2',
                                    'pitstop_interval': [53, 53],
                                    'pit_stop_lap': 53,
                                    'tire_age': 24}},
            'Nico Hulkenberg': {'starting_compound': 'A4', 'starting_tire_age': 2},
            'Valtteri Bottas': {'starting_compound': 'A4',
                                'starting_tire_age': 2,
                                1: {'compound': 'A4',
                                    'pitstop_interval': [1, 1],
                                    'pit_stop_lap': 1,
                                    'tire_age': 3},
                                2: {'compound': 'A3',
                                    'pitstop_interval': [20, 20],
                                    'pit_stop_lap': 20,
                                    'tire_age': 19}},
            'Felipe Massa': {'starting_compound': 'A4',
                            'starting_tire_age': 2,
                            1: {'compound': 'A4',
                                'pitstop_interval': [11, 11],
                                'pit_stop_lap': 11,
                                'tire_age': 13},
                            2: {'compound': 'A3',
                                'pitstop_interval': [29, 29],
                                'pit_stop_lap': 29,
                                'tire_age': 18},
                            3: {'compound': 'A2',
                                'pitstop_interval': [54, 54],
                                'pit_stop_lap': 54,
                                'tire_age': 25}},
            'Carlos Sainz Jnr': {'starting_compound': 'A4',
                                'starting_tire_age': 2,
                                1: {'compound': 'A4',
                                    'pitstop_interval': [11, 11],
                                    'pit_stop_lap': 11,
                                    'tire_age': 13},
                                2: {'compound': 'A3',
                                    'pitstop_interval': [30, 30],
                                    'pit_stop_lap': 30,
                                    'tire_age': 19}},
            'Sergio Perez': {'starting_compound': 'A4',
                            'starting_tire_age': 0,
                            1: {'compound': 'A4',
                                'pitstop_interval': [10, 10],
                                'pit_stop_lap': 10,
                                'tire_age': 10},
                            2: {'compound': 'A2',
                                'pitstop_interval': [27, 27],
                                'pit_stop_lap': 27,
                                'tire_age': 17}},
            'Fernando Alonso': {'starting_compound': 'A3',
                                'starting_tire_age': 0,
                                1: {'compound': 'A3',
                                    'pitstop_interval': [11, 11],
                                    'pit_stop_lap': 11,
                                    'tire_age': 11},
                                2: {'compound': 'A2',
                                    'pitstop_interval': [30, 30],
                                    'pit_stop_lap': 30,
                                    'tire_age': 19}},
            'Daniil Kvyat': {'starting_compound': 'A3',
                            'starting_tire_age': 0,
                            1: {'compound': 'A3',
                                'pitstop_interval': [21, 21],
                                'pit_stop_lap': 21,
                                'tire_age': 21}},
            'Esteban Gutierrez': {'starting_compound': 'A3',
                                'starting_tire_age': 0,
                                1: {'compound': 'A3',
                                    'pitstop_interval': [13, 13],
                                    'pit_stop_lap': 13,
                                    'tire_age': 13}},
            'Jolyon Palmer': {'starting_compound': 'A3',
                            'starting_tire_age': 0,
                            1: {'compound': 'A3',
                                'pitstop_interval': [15, 15],
                                'pit_stop_lap': 15,
                                'tire_age': 15},
                            2: {'compound': 'A3',
                                'pitstop_interval': [26, 26],
                                'pit_stop_lap': 26,
                                'tire_age': 11}},
            'Marcus Ericsson': {'starting_compound': 'A3',
                                'starting_tire_age': 0,
                                1: {'compound': 'A3',
                                    'pitstop_interval': [17, 17],
                                    'pit_stop_lap': 17,
                                    'tire_age': 17}},
            'Romain Grosjean': {'starting_compound': 'A4',
                                'starting_tire_age': 0,
                                1: {'compound': 'A4',
                                    'pitstop_interval': [10, 10],
                                    'pit_stop_lap': 10,
                                    'tire_age': 10},
                                2: {'compound': 'A3',
                                    'pitstop_interval': [27, 27],
                                    'pit_stop_lap': 27,
                                    'tire_age': 17}},
            'Kevin Magnussen': {'starting_compound': 'A3',
                                'starting_tire_age': 0,
                                1: {'compound': 'A3',
                                    'pitstop_interval': [13, 13],
                                    'pit_stop_lap': 13,
                                    'tire_age': 13},
                                2: {'compound': 'A3',
                                    'pitstop_interval': [27, 27],
                                    'pit_stop_lap': 27,
                                    'tire_age': 14},
                                3: {'compound': 'A2',
                                    'pitstop_interval': [43, 43],
                                    'pit_stop_lap': 43,
                                    'tire_age': 16}},
            'Jenson Button': {'starting_compound': 'A4',
                            'starting_tire_age': 0,
                            1: {'compound': 'A4',
                                'pitstop_interval': [10, 10],
                                'pit_stop_lap': 10,
                                'tire_age': 10},
                            2: {'compound': 'A2',
                                'pitstop_interval': [28, 28],
                                'pit_stop_lap': 28,
                                'tire_age': 18}},
            'Pascal Wehrlein': {'starting_compound': 'A3',
                                'starting_tire_age': 0,
                                1: {'compound': 'A3',
                                    'pitstop_interval': [13, 13],
                                    'pit_stop_lap': 13,
                                    'tire_age': 13},
                                2: {'compound': 'A2',
                                    'pitstop_interval': [30, 30],
                                    'pit_stop_lap': 30,
                                    'tire_age': 17}},
            'Felipe Nasr': {'starting_compound': 'A2',
                            'starting_tire_age': 0,
                            1: {'compound': 'A2',
                                'pitstop_interval': [29, 29],
                                'pit_stop_lap': 29,
                                'tire_age': 29}},
            'Esteban Ocon': {'starting_compound': 'A2',
                            'starting_tire_age': 0,
                            1: {'compound': 'A2',
                                'pitstop_interval': [17, 17],
                                'pit_stop_lap': 17,
                                'tire_age': 17},
                            2: {'compound': 'A3',
                                'pitstop_interval': [26, 26],
                                'pit_stop_lap': 26,
                                'tire_age': 9},
                            3: {'compound': 'A3',
                                'pitstop_interval': [44, 44],
                                'pit_stop_lap': 44,
                                'tire_age': 18}}
            }
    
    
    gp_location = "Austin"
    num_simulations = 2  # Nombre de simulations

    # Exécuter la simulation
    simulator = MonteCarloSimulator(season, gp_location, db_path, driver_strategies, num_simulations)
    simulator.run_simulation()
    simulator.summarize()
    

