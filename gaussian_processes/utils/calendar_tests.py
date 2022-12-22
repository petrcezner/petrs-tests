import pandas as pd
from holidays import Czechia

cz_holidays = Czechia(years=[2022])

range_of_dates = pd.date_range("2020-01-01", "2022-12-31")
df = pd.DataFrame(
    index=range_of_dates,
    data={"is_holiday": [date in cz_holidays for date in range_of_dates]}
)



