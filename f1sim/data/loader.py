import sqlite3
from pathlib import Path
import pandas as pd
from typing import Dict, List, Optional

class DataLoader:
    """
    Chargement flexible des données :
    - `load_all()` pour toutes les tables
    - `load_table()` générique avec filtres `year` et `circuit`
    - Méthodes dédiées pour rétrocompatibilité
    - Vérification immédiate de l'existence de la DB
    """
    def __init__(self, db_path: str, historical_years: int = 1):
        # Vérification à l'initialisation
        if not Path(db_path).exists():
            raise FileNotFoundError(f"Base de données non trouvée : {db_path}")
        self.db_path = db_path
        self.historical_years = historical_years

    def _connect(self) -> sqlite3.Connection:
        # Ouvre une connexion SQLite
        return sqlite3.connect(self.db_path)

    def load_all(self) -> Dict[str, pd.DataFrame]:
        """Charge toutes les tables existantes dans la DB"""
        with self._connect() as conn:
            tbls = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
            tables = tbls['name'].tolist()
            return {t: pd.read_sql(f"SELECT * FROM {t}", conn) for t in tables}

    def load_table(
        self,
        table: str,
        year: Optional[int] = None,
        circuit: Optional[str] = None
    ) -> pd.DataFrame:
        """Charge une table avec filtres optionnels"""
        sql = f"SELECT * FROM {table}"
        clauses: List[str] = []
        params: List = []
        # Filtre années
        if year is not None:
            start = year - self.historical_years
            clauses.append("year BETWEEN ? AND ?")
            params.extend([start, year])
        # Filtre circuit
        if circuit is not None:
            clauses.append("circuit = ?")
            params.append(circuit)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        with self._connect() as conn:
            return pd.read_sql(sql, conn, params=params)