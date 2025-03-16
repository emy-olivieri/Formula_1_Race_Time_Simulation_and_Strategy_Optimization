# -*- coding: utf-8 -*-
"""
data_loader.py

Module responsible for loading data from an SQLite database into pandas DataFrames.
"""

import sqlite3
import pandas as pd


class DataLoader:
    """
    Class responsible for loading data from an SQLite database.
    """

    def __init__(self, db_path: str):
        """
        Args:
            db_path (str): Path to the SQLite database file.
        """
        self.db_path = db_path
        self.dataframes = {}

    def load_data(self) -> dict:
        """
        Load data from the SQLite database and store it in a dictionary.

        Returns:
            dict: A dictionary where keys are table names and values are DataFrames.
        """
        connection = sqlite3.connect(self.db_path)

        # List of relevant tables in the database
        tables = [
            "drivers",
            "fcyphases",
            "laps",
            "qualifyings",
            "races",
            "retirements",
            "starterfields",
        ]

        # Create a dict {table_name: DataFrame}
        self.dataframes = {
            table: pd.read_sql_query(f"SELECT * FROM {table}", connection)
            for table in tables
        }

        connection.close()
        return self.dataframes
