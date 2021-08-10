# C:\Users\q1233\OneDrive\Desktop\程式庫\Webframework\爬蟲\爬蟲作品\TradingView\Data
#%%
from pyecharts.charts import *
from pyecharts.components import Table
from pyecharts import options as opts
from pyecharts.commons.utils import JsCode
import random
import datetime
from pyecharts.globals import CurrentConfig
import numpy as np

CurrentConfig.ONLINE_HOST = "http://127.0.0.1:8000/assets/"
#%%

import os
import pandas as pd
import numpy as np
import re
import mplfinance as mpf


df = pd.read_csv('3_7.csv').dropna(axis='index', how='any', subset=['開盤價','最高價','最低價','收盤價'])


df.drop(columns='Unnamed: 0', inplace=True)
df = df[[True if i.isdigit() else False for i in df['開盤價'].values ]]
df = df[[True if i.isdigit() else False for i in df['到期月份(週別)'].values ]]
# [f(x) if condition else g(x) for x in sequence]
df.head()

#%%

def ThirdWed(year):
    year = int(year)
    check = 0
    for i in range(1,32):
        if datetime.date(year, 1, i).isoweekday() ==3:
            check+=1
        if check==3:
            break 
    return  datetime.date(year, 1, i)

#%%

df['deathline'] = [int(str(i)[4:6]) for i in df['到期月份(週別)'].values ]
df['trade_month'] = [ int(re.findall(r'\d+', j)[1])+1 \
if datetime.date(int(re.findall(r'\d+', j)[0]),int(re.findall(r'\d+', j)[1]),int(re.findall(r'\d+', j)[2]))\
.__sub__(ThirdWed(int(re.findall(r'\d+', j)[0]))).days % 28 >(((int(re.findall(r'\d+', j)[1])-1)//3))*7\
     else int(re.findall(r'\d+', j)[1]) for j in df['交易日期'].values  ]


df_normal = df.query('(交易時段 == "一般")')
df_normal = df_normal[df['trade_month'] == df['deathline']]
df_normal.reset_index(drop=True, inplace=True)
df_normal.iloc[98]

#%%
# 轉換型態

def turn_int(name):
    df_normal[name] = np.array([int(i) for i in df_normal[name].values])
    print(df_normal[name].describe())
    return df_normal[name]

for i in ['開盤價','最高價','最低價','收盤價']:
    turn_int(i)



df_normal.head()


#%%
# 以日期為index
df_normal.index = df_normal['交易日期']

# 取adjClose至adjOpen的欄位資料
df_kline = df_normal.iloc[:,3:7]

df_kline.columns = ['Open','High','Low','Close']
# ['開盤價','最高價','最低價','收盤價']

# oclh
df_kline = df_kline[['Open','Close','Low','High',]]

# 抓取近20日的資料
df_adj_20d = df_kline.iloc[-20:,:]
df_adj_20d.head()
df_kline.tail()
# %%
df_kline.tail()
df_kline['Close'].values[99:104]


#%%
y_data = df_kline.values.tolist()

date_list = list(df_kline.index)

"""
 ['chalk',
'dark',
'essos',
'infographic',
'light',
'macarons',
'purple-passion',
'roma',
'romantic',
'shine',
'vintage',
'walden',
'westeros',
'white',
'wonderland']
"""
kline = \
(   Kline(
    init_opts=opts.InitOpts(
        width='800px', 
        height='600px', 
        bg_color='black',
        page_title = "網頁標題",
        theme='chalk',
                            )
        )
        
    .set_global_opts()
    .add_xaxis(date_list)
    .add_yaxis(
        '日K', 
        # '', 
        y_data
               )
    .set_global_opts
    (
        # 標題
        title_opts=opts.TitleOpts(
            title="主標題", 
            # subtitle='我是副標題',
            # pos_left='center',
            # pos_top='10%',
            title_textstyle_opts=opts.TextStyleOpts(
                                        # color='red',
                                                    ),
                                            # 副标题样式
            subtitle_textstyle_opts=opts.TextStyleOpts(
                                        # color='green',
                                                        ),
                                ),
        
        # 圖例
        legend_opts=opts.LegendOpts(
            is_show=True,
            pos_left='20%',
            pos_bottom='90%',
            # orient='vertical',
            # item_gap=100,
            textstyle_opts=opts.TextStyleOpts(color='green'),

            # 可选'circle', 'rect', 'roundRect', 'triangle', 'diamond', 'pin', 'arrow', 'none'
            # legend_icon='circle',
                                    ),
        

        # 互動提示框
        tooltip_opts=opts.TooltipOpts(
            is_show=True,
            trigger_on="mousemove|click",# 鼠标移动或者点击时触发
            axis_pointer_type = "cross",
            # background_color="green",
            # textstyle_opts=opts.TextStyleOpts(color='red'),

                                    ),
        

        xaxis_opts=opts.AxisOpts(
            type_='category',
            is_scale = True, 
            axisline_opts=opts.AxisLineOpts(
                #is_show=True,
                is_on_zero=False,
                linestyle_opts=opts.LineStyleOpts(
                    width=2, 
                    color='green'
                                                ),
                                            ),

                                ),
        yaxis_opts=opts.AxisOpts(
            name='',
            is_scale = True, 

            name_textstyle_opts=opts.TextStyleOpts(
                    # color='red'
                                                    ),

            axisline_opts=opts.AxisLineOpts(
                is_show=True,
                # symbol='arrow',
                is_on_zero=False,
                linestyle_opts=opts.LineStyleOpts(
                    width=2, 
                    color='green',           
                                                )
                
                                            ),
            
            axistick_opts=opts.AxisTickOpts(
                is_show=False
                                            ),
            
                                ),
            

            # visualmap_opts=opts.VisualMapOpts(
            # is_show=False,
            # min_=16000, 
            # max_=17800,    
            # range_color=['white','red',],
            # orient='vertical',
            # pos_right='0%',
            # pos_bottom='0%',
            # # pos_top='50%',
            
            # item_height = 500, 
            # border_width = 0,
            # # is_piecewise=True,

            #                               ),

            

            # 縮放
        datazoom_opts=opts.DataZoomOpts(
            is_show=True,
            is_realtime = True, 
            range_start=60,
            range_end=80, 
            # orient="vertical",
                                        ),


    )
    .set_series_opts
    (
        # itemstyle_opts=opts.ItemStyleOpts(color='green')
        
        
    )

)

kline.render('./templates/dayK.html')


kline.render_notebook()



# %%

"""成交量"""
date_list = list(df_kline.index)

y_data = df_normal['成交量'].values.tolist()
Volume = (Bar(
     init_opts=opts.InitOpts(
         width='800px', 
        height='400px',
        theme='chalk',
                            )

            )
       .add_xaxis(date_list)
       .add_yaxis('', y_data)
       .set_global_opts(
            xaxis_opts=opts.AxisOpts(
            type_='category',
            is_scale = True, 
            axisline_opts=opts.AxisLineOpts(
                #is_show=True,
                is_on_zero=False,
                linestyle_opts=opts.LineStyleOpts(
                    width=2, 
                    color='green'
                                                ),
                                            ),

                                ),
        yaxis_opts=opts.AxisOpts(
            name='',
            is_scale = True, 

            name_textstyle_opts=opts.TextStyleOpts(
                    # color='red'
                                                    ),

            axisline_opts=opts.AxisLineOpts(
                is_show=True,
                # symbol='arrow',
                is_on_zero=False,
                linestyle_opts=opts.LineStyleOpts(
                    width=2, 
                    color='green',           
                                                )
                
                                            ),
                                ),
            datazoom_opts=opts.DataZoomOpts(
                is_show=True,
                is_realtime = True, 
                range_start=60,
                range_end=80, 
                # orient="vertical",
                                        ),   
                        
                        )
        .set_series_opts(label_opts=opts.LabelOpts(is_show=False,
                                        # 标签的位置。可选
                                        # 'top'，'left'，'right'，'bottom'，'inside'，'insideLeft'，'insideRight'
                                        # 'insideTop'，'insideBottom'， 'insideTopLeft'，'insideBottomLeft'
                                        # 'insideTopRight'，'insideBottomRight'
                                    #    position='inside',
                                        )
                        )
        
      )

Volume.render('./templates/Volume.html')
Volume.render_notebook()


# %%

def avg(num):
    result = []
    for i in range(1,len(df_kline['Close'].values)+1):
        if  i-num >=0:
            result += ['{:.1f}'.format(df_kline['Close'].values[i-num:i].mean())]
        else:
            result += [df_kline['Close'].values[i]]
        # print((i-num,i))
    return np.array(result)        

# print(avg(10))


def drawavg(num):
    date_list = list(df_kline.index)

    df_kline[f'{num}avg'] = avg(num)
    line = (Line()
        .add_xaxis(date_list)
        .add_yaxis(f'{num}日均線', df_kline[f'{num}avg'].values.tolist())
        .set_global_opts(
            xaxis_opts=opts.AxisOpts(
                # type_='category',
                is_scale = True, 
                                        ),
                yaxis_opts=opts.AxisOpts(
                # type_='category',
                is_scale = True, 
                                        ),
                        )
        .set_series_opts(label_opts=opts.LabelOpts(is_show=False,
                                               # 标签的位置。可选
                                               # 'top'，'left'，'right'，'bottom'，'inside'，'insideLeft'，'insideRight'
                                               # 'insideTop'，'insideBottom'， 'insideTopLeft'，'insideBottomLeft'
                                               # 'insideTopRight'，'insideBottomRight'
                                            #    position='inside',
                                               )
                        )    
    )
    line.render_notebook()
    overlap = kline.overlap(line)
    overlap.render('./templates/dayK.html')
    return overlap

for i in [5,20,60]:
    overlap = drawavg(i)
overlap.render('./templates/K&MA.html')

overlap.render_notebook()
#%%
grid = (Grid( init_opts=opts.InitOpts(
        width='1200px', 
        height='1000px', 
        bg_color='black',
                                    )
            )

        .add(overlap,grid_opts=opts.GridOpts(pos_top="75%"))
        .add(Volume,grid_opts=opts.GridOpts(pos_bottom="30%"))
       
        )

grid.render('./templates/dayK.html')

grid.render_notebook()
#%%

