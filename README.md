# F1 Race Simulation: A Data-Driven Approach to Predicting Race Strategies and Lap Times -- In Progress

## Introduction

This repository hosts a race simulation framework for circuit motorsport events, with a particular focus on Formula 1. The model is designed to simulate and analyze race strategies, including pit stop planning (number of stops, inlaps, and tire compound selection), and long-term race effects (tire & fuel performance, etc).

Utilising a lap-wise discretisation approach, the simulation balances computational efficiency with high accuracy. To account for uncertainties and stochastic race events, probabilistic influences are integrated through Monte Carlo simulations, enabling an extensive evaluation of various race scenarios and optimising strategy selection.

## Utilisation

The model can be used for multiple applications, including:
- Race Outcome Prediction: Simulating race predicstions based on qualifying outcomes and strategic decisions.
- Strategy Optimisation: Comparing different pit stop strategies, tyre choices, and fuel management approaches to identify the most effective race strategy.
- What-If Scenarios: Testing various conditions, including safety car deployments, accidents, and different driver strategies to evaluate their impact on race results.

## Keywords

Formula 1, Race Simulation, Monte Carlo Methods, Discrete Event Simulation, Bayesian Inference, Pit Stop Strategy, Tire Degradation, Fuel Consumption, Lap Time Prediction, Strategy Optimisation 

## General Presentation

- **Lap Time Simulation**: Implements discrete-event simulation for lap time modeling.
- **On-Track Event Modeling**: Simulates race elements including fuel & tire performance, race incidents (failures and accidents), pit stops, and safety car deployments to create a more realistic race environment.
- **Fuel & Tire Performance**: Implements a model that dynamically adjusts lap times based on fuel consumption and tire degradation through OLS estimation, leveraging historical race data.
- **Race Incidents**: Separates failures and accidents using real data: mechanical breakdowns are modeled based on team-specific failure rates, while accidents are simulated using driver-specific historical incident data, including safety car deployments. Bayesian statistics are used to model the probability of failure and accident.
- **Pit Stop Modeling**: Uses historical race data to estimate pit stop durations based on team-specific performances at the same track. A probabilistic model, leveraging the Fisk distribution, accounts for variability in pit stop times.
- **Overtaking (Future Implementation)**: Planned feature to model position changes based on driver behavior and track conditions. Currently, overtaking is not implemented, and the hypothesis assumes that race positions are determined solely by cumulative race times, without in-race overtakes affecting final placements.

## Data Sources

- **F1 Timing Data (2014-2019)**: This data comes from the [F1 Timing Database](https://github.com/TUMFTM/f1-timing-database), a repository hosting an SQLite database containing Formula 1 lap and race information for the seasons from 2014 to 2019.

## Code Structure

A UML class diagram will be created to illustrate the relationships between the different components of the simulation.

### Core Simulation Components

- `model.py`: Defines an abstract base class for simulation models, enforcing the implementation of `fit` and `predict` methods for subclasses.
- `data_loader.py`: Loads race data from an SQLite database into pandas DataFrames for use in simulations.
- `team.py`: Defines the `Team` class representing a racing team and a `TeamRegistry` to ensure unique instances per team name.
- `driver.py`: Represents a driver, including their performance parameters, qualifying times, failure and accident probabilities, tire strategy, and fuel consumption. Tracks race progress by updating lap times and DNF status.
- `dnf_model.py`: Models the probability of a driver failing to finish a race (DNF) due to accidents with driver-specific modeling or mechanical failures with team-specific modeling.
- `fuel_and_tire_model.py`: Estimates lap times based on fuel consumption, tire degradation, and compound selection using OLS regression.
- `pit_stop.py`: Models pit stop duration using historical race data and probabilistic distributions. Estimates optimal pit stop times and calibrates variability using the Fisk distribution.
- `run.py`: Orchestrates the race simulation, handling driver updates, pit stops, lap times, retirements, and final race classification.
- `monte_carlo_simulator.py`: Runs multiple race simulations using Monte Carlo methods to analyze variability in race outcomes and compare simulated results with actual race data.

### Evaluation & Statistical Analysis

- `evaluation.py`: Provides a base class for statistical evaluation, storing actual and simulated race data. Enforces the implementation of an `evaluate()` method in subclasses.
- `spearman_evaluation.py`: Implements Spearman's rank correlation test to compare simulated race positions with actual race results.
- `wilcoxon_evaluation.py`: Applies the Wilcoxon signed-rank test to evaluate whether simulated race times significantly differ from actual race times.

## Installation & Usage

The code was developed with Python 3.12.9 on Windows 11.

### Prerequisites

- Required libraries (install via `requirements.txt`):
  ```sh
  pip install -r requirements.txt
  ```

### Running the Simulation

To run a race simulation, you need the following components:

- **Database File**: The SQLite database (`F1_timingdata_2014_2019.sqlite`) containing historical F1 race data.
- **Season and Grand Prix Location**: Specify the season (e.g., 2016) and the race location (e.g., Austin).
- **Driver Strategies**: Predefined tire and pit stop strategies for drivers, which are already included in the main script.
- **Number of Simulations**: Define how many Monte Carlo iterations will be performed to account for probabilistic variations in race outcomes.

### Execution:

1. Ensure that all dependencies are installed (see Installation & Usage section).
2. Run the main script to start the simulation:
   ```sh
   python main.py
   ```
3. The simulation will:
   - Execute multiple race iterations using Monte Carlo methods.
   - Simulate race dynamics, including lap times, pit stops, fuel consumption, and DNFs.
   - Compare the simulated results with historical race outcomes.
4. The summarized results, including race positions and statistical comparisons, will be displayed.

## Results

The simulation model will be utilized to analyze and optimize race strategies, offering insights into pit stop planning, compound choice, and fuel management. It will be applied to selected races from the test set to evaluate its predictive accuracy, and the results of these simulations will be presented here.

Additionally, a detailed document explaining the methodology, hypotheses, and assumptions behind the simulation will be made available soon.

## Test

To evaluate the performance of the model, various tests will be conducted:

- **Historical Data Comparison**: Simulated race results (positions and race times) will be compared with real-world F1 race outcomes from the dataset to measure accuracy.
- **Strategy Validation**: Different pit stop strategies will be tested to determine their impact on race outcomes.
- **Sensitivity Analysis**: The model’s responsiveness to key input parameters (e.g., fuel load, tire wear, and pit stop timing) will be analyzed.

The results of these tests will help refine the model and improve its predictive capabilities.

## Improvements

Future enhancements are outlined in the [TODO List](./TODO.md), which includes : 

- [ ] Clean and thoroughly comment the code to improve readability and maintainability.
- [ ] Implement time loss adjustments based on grid positions at the start of the race.
- [ ] Redesign the architecture to store model outputs for each driver in a specific race and save them in a CSV/Excel file to avoid re-running the model for every simulation.
- [ ] Optimize the running time by parallelizing simulations and improving dataset handling.
- [ ] Improve the existing models for better accuracy and performance.
- [ ] Develop and integrate a first-lap and overtaking model.

## References

1. Sulsters, C. (2018). *Simulating Formula One Race Strategies*. Vrije Universiteit Amsterdam.
2. Heilmeier, A., Graf, M., Betz, J., & Lienkamp, M. (2020). *Application of Monte Carlo Methods to Consider Probabilistic Effects in a Race Simulation for Circuit Motorsport*. MDPI Applied Sciences, 10(7), 2305.&#x20;

