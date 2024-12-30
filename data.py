import sqlite3
import pandas as pd

class Data:
    def __init__(self,path_data):
        self.path_data=path_data
        


    def get_data(self):
        con = sqlite3.connect(self.path_data)
        table_names = ["drivers", "fcyphases", "laps", "qualifyings", "races", "retirements", "starterfields"]
        dataframes = {}
        for table_name in table_names:
            query = f"SELECT * FROM {table_name}"
            dataframes[table_name] = pd.read_sql_query(query, con)
        self.dataframes=dataframes
        print(dataframes["drivers"])
    

