import pandas as pd
from holidays import Czechia

cz_holidays = Czechia(years=[2022])

frequency = 15
range_of_dates = pd.date_range("2020-01-01", "2022-12-31", freq=f'{frequency}min')
df = pd.DataFrame(
    index=range_of_dates,
    data={"is_holiday": [date in cz_holidays for date in range_of_dates]}
)
df['is_holiday'] = df['is_holiday'].astype(int)



