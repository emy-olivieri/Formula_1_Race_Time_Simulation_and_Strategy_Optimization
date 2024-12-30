from data import Data
from model import Model
path="F1_timingdata_2014_2019.sqlite"
objet1=Data(path)
objet1.get_data()
dataframes1=objet1.dataframes


## objet2=Model(driver=,race=,data=dataframes1)