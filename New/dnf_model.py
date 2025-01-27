# -*- coding: utf-8 -*-
"""
dnf_model.py

Defines a class for obtaining probabilities related to "Did Not Finish" (DNF) events,
inheriting from the abstract base class `Model`.
"""

from model import Model


class DNFModel(Model):
    """
    Example class for returning DNF-related probabilities per driver and season.
    Inherits from the abstract `Model` base class.
    """

    def __init__(self):
        """
        Store any needed attributes.
        """
        self.driver_name = None
        self.season = None

        # We might store probabilities after fit
        self.accident_probability = 0.2
        self.failure_probability = 0.2
        self.is_fitted = False

    def fit(self, driver_name: str, season: int):
        """
        Fit or initialize the model. In a real scenario, you might look up stats
        from historical data. Here, we'll just store the parameters.
        """
        self.driver_name = driver_name
        self.season = season

        # TODO: Potentially do a DB lookup or other logic for real usage
        # We'll keep the probabilities at 0.2 / 0.2 as placeholders

        self.is_fitted = True

    def predict(self):
        """
        Return a tuple (probability_of_accident, probability_of_failure).
        """
        if not self.is_fitted:
            raise RuntimeError("DNFModel is not fitted. Call `fit()` first.")

        return (self.accident_probability, self.failure_probability)
