# -*- coding: utf-8 -*-
"""
model.py

Defines an abstract base class for simulation models.
"""

from abc import ABC, abstractmethod


class Model(ABC):
    """
    Abstract base class for simulation models (DNF, Fuel & Tire, etc.).
    """

    @abstractmethod
    def fit(self, *args, **kwargs):
        """
        Fit or initialize the model with relevant data.
        """
        pass

    @abstractmethod
    def predict(self, *args, **kwargs):
        """
        Predict or compute outcomes based on the model.
        """
        pass
