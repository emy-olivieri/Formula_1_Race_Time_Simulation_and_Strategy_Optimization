# tests/test_data_loader.py

import os
import sqlite3
import pandas as pd
import pytest
from f1sim.data.loader import DataLoader

DB_TEST = "test_f1.db"

@pytest.fixture(scope="module", autouse=True)
def create_test_db():

    # Création d'une base SQLite de test avec plusieurs tables
    conn = sqlite3.connect(DB_TEST)
    cur = conn.cursor()
    # Table lap_times
    cur.execute("""
        CREATE TABLE lap_times (
            year INTEGER,
            circuit TEXT,
            driver_id INTEGER,
            lap INTEGER,
            time REAL
        )
    """)
    cur.executemany(
        "INSERT INTO lap_times VALUES (?,?,?,?,?)",
        [
            (2021, 'Monza', 1, 1, 82.0),
            (2022, 'Monza', 1, 2, 83.0),
            (2022, 'Spa',   2, 1, 120.0),
        ]
    )
    # Table race_results
    cur.execute("""
        CREATE TABLE race_results (
            year INTEGER,
            circuit TEXT,
            driver_id INTEGER,
            position INTEGER,
            status TEXT
        )
    """)
    cur.executemany(
        "INSERT INTO race_results VALUES (?,?,?,?,?)",
        [
            (2022, 'Monza', 1, 1, 'Finished'),
            (2022, 'Monza', 2, None, 'DNF'),
        ]
    )
    # Table qualifying
    cur.execute("""
        CREATE TABLE qualifying (
            year INTEGER,
            circuit TEXT,
            driver_id INTEGER,
            q1 REAL,
            q2 REAL,
            q3 REAL
        )
    """)
    cur.executemany(
        "INSERT INTO qualifying VALUES (?,?,?,?,?,?)",
        [
            (2022, 'Monza', 1, 80.0, 79.5, 79.0),
            (2022, 'Spa',   2, 90.0, None, None),
        ]
    )
    conn.commit()
    conn.close()

    yield


def test_load_all_tables():
    loader = DataLoader(DB_TEST, historical_years=1)
    all_tables = loader.load_all()
    # On attend au moins ces trois tables
    assert set(['lap_times', 'race_results', 'qualifying']).issubset(all_tables.keys())
    # Chaque entrée est un DataFrame
    for df in all_tables.values():
        assert isinstance(df, pd.DataFrame)

def test_load_table_no_filter():
    loader = DataLoader(DB_TEST, historical_years=1)
    df = loader.load_table('lap_times')
    # Sans filtre, on doit charger toutes les lignes
    assert len(df) == 3

def test_load_table_year_filter():
    loader = DataLoader(DB_TEST, historical_years=1)
    # historical_years=1 → start = 2022-1 = 2021 → accepte 2021 et 2022
    df = loader.load_table('lap_times', year=2022)
    # On doit voir les années 2021 et 2022
    assert set(df['year']) == {2021, 2022}

def test_load_table_strict_year_window():
    # Avec fenêtre à 0 an
    loader0 = DataLoader(DB_TEST, historical_years=0)
    df0 = loader0.load_table('lap_times', year=2022)
    # historical_years=0 → start=2022 → seul 2022
    assert set(df0['year']) == {2022}
    # Et on perd la ligne 2021
    assert all(df0['year'] == 2022)

def test_load_table_circuit_filter():
    loader = DataLoader(DB_TEST, historical_years=2)
    df = loader.load_table('lap_times', year=2022, circuit='Monza')
    # Il ne doit rester que Monza
    assert set(df['circuit']) == {'Monza'}
    # Et deux lignes pour Monza en 2021 et 2022
    assert len(df) == 2

def test_load_nonexistent_table_raises():
    loader = DataLoader(DB_TEST, historical_years=1)
    with pytest.raises(pd.io.sql.DatabaseError):
        loader.load_table('no_such_table')

def test_missing_db_raises():
    with pytest.raises(FileNotFoundError):
        DataLoader("no_such.db")
