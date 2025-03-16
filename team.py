# -*- coding: utf-8 -*-
"""
team.py

Defines the Team class and a TeamRegistry to ensure one instance per unique team name.
"""


class Team:
    """
    Represents a racing team (e.g., Mercedes, Ferrari).
    """

    def __init__(self, name: str):
        """
        Args:
            name (str): Team name.
        """
        self.name = name


class TeamRegistry:
    """
    Registry (or cache) to ensure a single instance of Team per unique name.
    """

    _teams_cache = {}

    @classmethod
    def get_team(cls, name: str) -> Team:
        """
        If a team with `name` exists in cache, returns it.
        Otherwise, create a new Team and store it.

        Args:
            name (str): Team name to fetch.

        Returns:
            Team: A Team instance.
        """
        if name not in cls._teams_cache:
            cls._teams_cache[name] = Team(name)
        return cls._teams_cache[name]
