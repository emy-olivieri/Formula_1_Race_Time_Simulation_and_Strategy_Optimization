from data import Data
from model import Model


path = "F1_timingdata_2014_2019.sqlite"

objet1 = Data(path)
objet1.get_data()
dataframes1 = objet1.dataframes

objet2 = Model(driver_id=1, race=12, dataframes=dataframes1)

objet2.clean_data()

# objet2.get_best_qualif_time()
# objet2.get_train_laps_time()
# objet2.get_test_laps_time()

# objet2.add_columns()

# print(objet2.train_laps_time[["best_qualif_time","fuelc","compound","tireage"]])


# combined_data = pd.concat([objet2.train_laps_time, objet2.test_laps_time], ignore_index=True)


# formula = "laptime ~ best_qualif_time + fuelc + C(compound) + C(compound):tireage + C(compound):I(tireage**2) "


objet2.estimate_parameters()
