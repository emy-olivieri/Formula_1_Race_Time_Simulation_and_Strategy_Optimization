# -*- coding: utf-8 -*-
"""
dnf_model.py

Defines a class for obtaining probabilities related to "Did Not Finish" (DNF) events,
inheriting from the abstract base class `Model`.
"""
import numpy as np
from model import Model


class DNFModel(Model):
    """
    Example class for returning DNF-related probabilities per driver and season.
    Inherits from the abstract `Model` base class.
    """

    def __init__(self, dataframes: dict):
        """
        Store any needed attributes.
        """
        self.driver_name = None
        self.season = None
        self.dfs_local = {n: df.copy() for n, df in dataframes.items()}

        self.accident_probability = None
        self.failure_probability = None
        self.is_fitted = False

    def fit(self, driver, season):
        """
        Fit or initialize the model. In a real scenario, you might look up stats
        from historical data. Here, we'll just store the parameters.
        """
        self.driver = driver
        self.team = self.driver.team
        self.season = season

        # TODO: Potentially do a DB lookup or other logic for real usage
        # We'll keep the probabilities at 0.2 / 0.2 as placeholders


        ### Instanciate dataframe needed and quick cleaning
        races_df = self.dfs_local["races"]
        starterfields_df = self.dfs_local["starterfields"]
        retirements_df = self.dfs_local["retirements"]
        retirements_df = retirements_df.fillna(0)
        seasons_to_train = [self.season - x for x in range (0, 2 +1)]
        df_filtered = retirements_df[retirements_df['season'].isin(seasons_to_train)].copy()

        ### To compute probability of accident per driver we need to compute the number of races did by each driver
        count_of_races_by_driver_df = starterfields_df[['race_id', 'driver_id']].merge(races_df[['id', 'season']], left_on='race_id', right_on='id')
        count_of_races_by_driver_df = count_of_races_by_driver_df.drop('id', axis=1)
        count_of_races_by_driver_df = count_of_races_by_driver_df[count_of_races_by_driver_df['season'].isin(seasons_to_train)]
        count_of_races_by_driver_df = count_of_races_by_driver_df.groupby('driver_id').agg(count_of_race=('race_id','count'))

        ### To compute probability of failure per team we need to compute the number of races did by each team
        link_driver_season_races_df = (starterfields_df[['race_id', 'driver_id', 'team']].merge(
                                        races_df[['id', 'season']], left_on='race_id', right_on ='id', how='inner').merge(
                                        df_filtered, on=['season', 'driver_id'], how='inner'))
        count_of_races_by_team_df = link_driver_season_races_df.groupby(['team']).agg(count_of_race=('race_id','count'))


        ### Compute for each driver the number of accident made and divide by the number of races ran (- > the proportion)
        dnf_accident_df = df_filtered.groupby("driver_id").agg(total_accident=('accidents','sum'))
        dnf_accident_df = dnf_accident_df.merge(count_of_races_by_driver_df, on='driver_id')
        dnf_accident_df['accident_proportion'] = dnf_accident_df['total_accident'] / dnf_accident_df['count_of_race']

        ### From the proportion we obtain mu and sigma by taking the mean and standard deviation
        ### We take into account only data of drivers who ran at least 20 races.
        mu_accident    = np.mean(dnf_accident_df[dnf_accident_df['count_of_race']>20]['accident_proportion'])
        sigma_accident = np.std(dnf_accident_df[dnf_accident_df['count_of_race']>20]['accident_proportion'])

        ### From mu and sigma we can compute alpha and beta of the prior distribution and then obtain the posterior distribution
        alpha_accident = ((1-mu_accident)/sigma_accident**2 - 1/mu_accident)*mu_accident**2
        beta_accident = alpha_accident*(1/mu_accident - 1)
        dnf_accident_df['alpha_posterior'] = dnf_accident_df['total_accident'] + alpha_accident
        dnf_accident_df['beta_posterior'] = dnf_accident_df['count_of_race'] - dnf_accident_df['total_accident'] + beta_accident

        ### Finally we can have the probability of accident by taking the expected value of the posterior distribution
        dnf_accident_df['accident_proba'] = dnf_accident_df['alpha_posterior'] / (dnf_accident_df['alpha_posterior'] + dnf_accident_df['beta_posterior'])

        ### Compute for each team the number of failures that occurred and divide by the number of races ran (-> the proportion)
        dnf_failure_df = link_driver_season_races_df.groupby(['team', 'driver_id', 'season']).agg(failures_agg=('failures','mean'))
        dnf_failure_df = dnf_failure_df.groupby("team").agg(total_failure=('failures_agg','sum'))
        dnf_failure_df = dnf_failure_df.merge(count_of_races_by_team_df, on='team')
        dnf_failure_df['failure_proportion'] = dnf_failure_df['total_failure'] / dnf_failure_df['count_of_race']
        
        ### From the proportion we obtain mu and sigma by taking the mean and standard deviation
        mu_failure    = np.mean(dnf_failure_df['failure_proportion'])
        sigma_failure = np.std(dnf_failure_df['failure_proportion'])

        ### From mu and sigma we can compute alpha and beta of the prior distribution and then obtain the posterior distribution
        alpha_failure = ((1-mu_failure)/sigma_failure**2 - 1/mu_failure)*mu_failure**2
        beta_failure = alpha_failure*(1/mu_failure - 1)
        dnf_failure_df['alpha_posterior'] = dnf_failure_df['total_failure'] + alpha_failure
        dnf_failure_df['beta_posterior'] = dnf_failure_df['count_of_race'] - dnf_failure_df['total_failure'] + beta_failure

        ### Finally we can have the probability of accident by taking the expected value of the posterior distribution
        dnf_failure_df['failure_proba'] = dnf_failure_df['alpha_posterior'] / (dnf_failure_df['alpha_posterior'] + dnf_failure_df['beta_posterior'])

        self.accident_probability = dnf_accident_df[dnf_accident_df.index==self.driver.driver_id]['accident_proba'].iloc[0]
        self.failure_probability = dnf_failure_df[dnf_failure_df.index==self.driver.team.name]['failure_proba'].iloc[0]

        self.is_fitted = True

    def predict(self):
        """
        Return a tuple (probability_of_accident, probability_of_failure).
        """
        if not self.is_fitted:
            raise RuntimeError("DNFModel is not fitted. Call `fit()` first.")

        return (self.accident_probability, self.failure_probability)
