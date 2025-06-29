import pandas as pd
from typing import Dict, Set

class DataPreprocessor:
    """
    Nettoyage des données selon :
    - Exclusion des courses/enqualifs mouillées
    - Sélection des colonnes utiles
    """
    def __init__(
        self,
        required_columns: Dict[str, list[str]],
        wet_races: Dict[int, list[str]],
        wet_qualifyings: Dict[int, list[str]]
    ):
        self.required_columns = required_columns
        self.wet_races_map = wet_races
        self.wet_quals_map = wet_qualifyings

    def preprocess(self, tables: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        races = tables.get("races", pd.DataFrame())
        exclude_ids = self._collect_exclude_ids(races)

        result: Dict[str, pd.DataFrame] = {}
        for name, df in tables.items():
            df_clean = df.copy()
            if "race_id" in df_clean.columns:
                df_clean = df_clean[~df_clean["race_id"].isin(exclude_ids)]
            if name == "races" and "id" in df_clean.columns:
                df_clean = df_clean[~df_clean["id"].isin(exclude_ids)]
            cols = self.required_columns.get(name)
            if cols:
                df_clean = df_clean[cols]
            result[name] = df_clean.reset_index(drop=True)
        return result

    def _collect_exclude_ids(self, races: pd.DataFrame) -> Set[int]:
        exclude: Set[int] = set()
        if races.empty:
            return exclude

        races["season"] = races["season"].astype(int)
        exclude.update(
            self._filter_ids(races, self.wet_races_map)
        )
        exclude.update(
            self._filter_ids(races, self.wet_quals_map)
        )
        return exclude

    def _filter_ids(
        self,
        races: pd.DataFrame,
        year_map: Dict[int, list[str]]
    ) -> Set[int]:
        ids: Set[int] = set()
        for year, locs in year_map.items():
            mask = (races["season"] == year) & (races["location"].isin(locs))
            ids.update(races.loc[mask, "id"].astype(int).tolist())
        return ids