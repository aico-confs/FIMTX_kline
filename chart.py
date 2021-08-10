
#%%

import os
import pandas as pd
import numpy as np
import mplfinance as mpf


df = pd.read_csv('./TradingData/dayk/7.csv')

for i in range(len(df.columns)-1, -1, -1):
    try:
        df[list(df.columns)[i]] = df[list(df.columns)[i-1]]
    except Exception as e:
        print(e)
    if i == 0:
        df.drop(columns=list(df.columns)[i], inplace=True)

df.head()
#%%
# 只看小型台指08
search = '202108'
df_08= df.query('`到期月份(週別)` == @search')
df_08.head()

#%%
# 只看小型台指08早盤
search = '202108'
df_08_normal = df.query('(`到期月份(週別)` == @search) and (交易時段 == "一般")')


df_08_normal.reset_index(drop=True, inplace=True)
df_08_normal.tail(5)
#%%
# 轉換型態

def turn_int(name):
    df_08_normal[name] = np.array([int(i) for i in df_08_normal[name].values])
    print(df_08_normal[name].describe())
    return df_08_normal[name]

for i in ['開盤價','最高價','最低價','收盤價']:
    turn_int(i)


df_08_normal['交易日期'] = pd.to_datetime(df_08_normal['交易日期'],format = '%Y-%m-%d')

# df_08_normal = df.query('開盤價 > 0')

df_08_normal.head()


#%%
# 以日期為index
# df_08_normal.index = df_08_normal['交易日期']
df_08_normal.index = pd.DatetimeIndex(df_08_normal['交易日期'])

# 取adjClose至adjOpen的欄位資料
df_kline = df_08_normal.iloc[:,3:7]

# 更改columns的名稱，以讓mplfinance看得懂
df_kline.columns = ['Open','High','Low','Close']
# ['開盤價','最高價','最低價','收盤價']

# 抓取近20日的資料
df_adj_20d = df_kline.iloc[-20:,:]
df_adj_20d.head()
df_kline.head()
# %%
# oclh

mpf.plot(df_adj_20d)
mpf.plot(df_adj_20d,type='candle')
mpf.plot(df_adj_20d,type='line')

