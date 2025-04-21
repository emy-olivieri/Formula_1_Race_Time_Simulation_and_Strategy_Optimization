import pandas as pd 

class DataPreprocessor:
    """
    Applies cleaning:
      - keeps only required columns
      - filters out wet-weather races and wet qualifying sessions from 2014-2019 
    """
    # Map season -> list of circuit locations to exclude for modelisation
    WET_RACES_BY_YEAR = {
        2014: ["Budapest", "Suzuka"],
        2015: ["Silverstone", "Austin"],
        2016: ["MonteCarlo", "Silverstone", "SaoPaulo"],
        2017: ["Shanghai", "Singapore"],
        2018: ["Hockenheim"],
        2019: ["Hockenheim"],
    }

    # Map season -> list of circuit locations to exclude for modelisation
    WET_QUALIFYINGS_BY_YEAR = {
        2014: ["Melbourne", "KualaLumpur", "Shanghai", "Silverstone"],
        2015: ["Austin"],
        2016: ["Spielberg"],
        2017: ["Monza"],
        2018: ["Hockenheim"],
    }

    def __init__(self, required_columns: dict[str, list[str]]) -> None:
        """
        Args:
            required_columns: map table_name -> columns to retain
        """
        self.required_columns = required_columns

    def preprocess(
        self,
        data: dict[str, pd.DataFrame]
    ) -> dict[str, pd.DataFrame]:
        """
        1. Identify wet-weather race IDs based on WET_RACES_BY_YEAR.
        2. Identify wet-qualifying race IDs based on WET_QUALIFYINGS_BY_YEAR.
        3. Combine both sets and remove those race IDs from every table.
        4. Keep only the required columns per table.

        Args:
            data: dict of raw DataFrames from DataLoader.
        Returns:
            dict of cleaned DataFrames.
        """
        races_df = data.get("races", pd.DataFrame())
        wet_race_ids = self._gather_wet_race_ids(races_df, self.WET_RACES_BY_YEAR)
        wet_qual_ids = self._gather_wet_race_ids(races_df, self.WET_QUALIFYINGS_BY_YEAR)
        # Union ensures overlapping IDs removed once
        exclude_ids = wet_race_ids.union(wet_qual_ids)

        cleaned = {}
        for table_name, df in data.items():
            # Drop rows for any excluded races
            if "race_id" in df.columns:
                df = df[~df["race_id"].isin(exclude_ids)].copy()
            if table_name == "races" and "id" in df.columns:
                df = df[~df["id"].isin(exclude_ids)].copy()

            # Keep only specified columns
            cols = self.required_columns.get(table_name)
            if cols:
                df = df[cols].copy()

            cleaned[table_name] = df.reset_index(drop=True)

        return cleaned

    def _gather_wet_race_ids(
        self,
        races_df: pd.DataFrame,
        year_map: dict[int, list[str]]
    ) -> set[int]:
        """
        From the races DataFrame, collect all IDs for seasons and locations
        specified in year_map.

        Args:
            races_df: DataFrame of the 'races' table.
            year_map: dict mapping season -> list of locations.
        Returns:
            Set of race IDs to exclude.
        """
        wet_ids: set[int] = set()
        if races_df.empty:
            return wet_ids

        tmp = races_df.copy()
        tmp["season"] = tmp["season"].astype(int)

        for year, locations in year_map.items():
            mask = (tmp["season"] == year) & (tmp["location"].isin(locations))
            for rid in tmp.loc[mask, "id"]:
                wet_ids.add(int(rid))

        return wet_ids

import pandas as pd

if __name__ == "__main__":
    # Exemple de DataFrame 'races' avec des courses mouillées et sèches
    races = pd.DataFrame({
        "id": [10, 11, 12, 13, 14],
        "season": [2014, 2014, 2015, 2015, 2016],
        "location": ["Budapest", "Melbourne", "Austin", "Spa", "Monza"]
    })

    # Autre table liée (ex: 'laps'), avec des race_id correspondants
    laps = pd.DataFrame({
        "race_id": [10, 11, 12, 13, 14],
        "lap_time": [90.5, 91.0, 88.3, 87.9, 89.1]
    })

    data = {
        "races": races,
        "laps": laps
    }

    required_columns = {
        "races": ["id", "season", "location"],
        "laps": ["race_id", "lap_time"]
    }

    preprocessor = DataPreprocessor(required_columns)
    cleaned = preprocessor.preprocess(data)

    for table, df in cleaned.items():
        print(f"\nTable : {table}")
        print(df)
