import os
import zipfile
import re
import pandas as pd
import numpy as np
import datetime
import codecs
import urllib.request as r
import urllib.parse
import bs4
import calendar 



import mplfinance as mpf
from pyecharts.charts import *
from pyecharts.components import Table
from pyecharts import options as opts
from pyecharts.commons.utils import JsCode
from pyecharts.globals import CurrentConfig
CurrentConfig.ONLINE_HOST = "https://cdn.kesci.com/lib/pyecharts_assets/"
# CurrentConfig.ONLINE_HOST = "http://127.0.0.1:8000/assets/"

from typing import Union
from sklearn.neighbors import NearestNeighbors
from scipy.sparse import csr_matrix
from sklearn.cluster import KMeans
def ThirdWed(year, month):
    year = int(year)
    check = 0
    for i in range(1,32):
        if datetime.date(year, month, i).isoweekday() ==3:
            check+=1
        if check==3:
            break 
    return  datetime.date(year, month, i)
def read(file_path):
    my_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath('__file__'))))
    path = os.path.join(my_path, file_path)

    # with open(path, 'r', encoding='UTF-8', errors='ignore') as f:
    with codecs.open(path,'rU','Big5') as doc:
        return pd.read_csv(doc, encoding='utf8', error_bad_lines=False)





class month_analysis():

    def __init__(self, month:Union[str, int], year:Union[str, int] = 2021) :
        self.month = '{:0>2}'.format(month)
        self.year = year
        self.date = calendar.monthcalendar(year, month)

        try:
            pd.read_csv(f'./TradingData/dayk/{self.month}.csv')
        except FileNotFoundError: 
            print ('必須先download()至指定資料夾，才能啟用模型功能')
        else:
            self.path = f'./TradingData/dayk/{self.month}.csv'


    
    def download(self):
        url = 'https://www.taifex.com.tw/cht/3/dlFutDataDown'
        final = -1
        start = 0
        while not self.date[-1][final]:
            final +=-1
        while not self.date[0][start]:
            start += 1
        values = {
        'down_type': '1',
        'commodity_id': 'MTX',
        'commodity_id2':'', 
        'queryStartDate': f'{self.year}/{self.month}/{self.date[0][start]}',
        'queryEndDate': f'{self.year}/{self.month}/{self.date[-1][final]}'
        }
        # print(values)
        data = urllib.parse.urlencode(values)
        data = data.encode('ascii')
        request=r.Request(url,  headers={
        "user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36"
             } ,data=data)
        with r.urlopen(request) as response:
            TradingData=response.read()
        destination = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath('__file__'))))
        # file_name = f"{'~'.join(list(values.values())[-2:])}.csv".replace('/','')
        file_name = f'{self.month}.csv'
        file_path = destination+'\\TradingData'+'\\dayk'
        if not os.path.isdir(file_path):  
            os.makedirs(file_path, exist_ok =True)
        with open(file_path+'\\'+file_name, 'wb') as f:
            f.write(TradingData)
        df = read(file_path+'\\'+file_name)
        for i in df.columns:
            try:
                df[i] = np.array([str(i).strip() for i in df[i].values])
            except TypeError:
                pass
        df.to_csv(file_path+'\\'+file_name)
    
    def chart(self, type:str='candle'):
        """
        type = 'ohlc', 'candle','line'
        """
        try:
            df = pd.read_csv(f'./TradingData/dayk/{self.month}.csv')
        except FileNotFoundError:
            raise FileNotFoundError('必須先下載至指定資料夾，才能繪製圖表')
        

        for i in range(len(df.columns)-1, -1, -1):
            try:
                df[list(df.columns)[i]] = df[list(df.columns)[i-1]]
            except Exception as e:
                print(e)
            if i == 0:
                df.drop(columns=list(df.columns)[i], inplace=True)
        df = df[[True if i.isdigit() else False for i in df['開盤價'].values ]]
        df = df[[True if i.isdigit() else False for i in df['到期月份(週別)'].values ]]
        # print(df.head())
        # 只看小型台指早盤
        df['deathline'] = [int(str(i)[4:6]) for i in df['到期月份(週別)'].values ]
        df['trade_month'] = [ int(re.findall(r'\d+', j)[1])+1 \
        if datetime.date(int(re.findall(r'\d+', j)[0]),int(re.findall(r'\d+', j)[1]),int(re.findall(r'\d+', j)[2]))\
        .__sub__(ThirdWed(int(re.findall(r'\d+', j)[0]))).days % 28 >(((int(re.findall(r'\d+', j)[1])-1)//3))*7\
            else int(re.findall(r'\d+', j)[1]) for j in df['交易日期'].values  ]

        df_normal = df.query('(交易時段 == "一般")')
        df_normal = df_normal[df['trade_month'] == df['deathline']]
        df_normal.reset_index(drop=True, inplace=True)

        # 轉換型態

        def turn_int(name):
            df_normal[name] = np.array([int(i) for i in df_normal[name].values])
            # print(df_08_normal[name].describe())
            return df_normal[name]

        for i in ['開盤價','最高價','最低價','收盤價']:
            turn_int(i)


        df_normal['交易日期'] = pd.to_datetime(df_normal['交易日期'],format = '%Y-%m-%d')
        df_normal.head()

        # 以日期為index
        # df_08_normal.index = df_08_normal['交易日期']
        df_normal.index = pd.DatetimeIndex(df_normal['交易日期'])

        # 取adjClose至adjOpen的欄位資料
        df_kline = df_normal.iloc[:,3:7]

        # 更改columns的名稱，以讓mplfinance看得懂
        df_kline.columns = ['Open','High','Low','Close']
        # ['開盤價','最高價','最低價','收盤價']

        # 抓取近20日的資料
        df_adj_20d = df_kline.iloc[-20:,:]
        df_adj_20d.head()
        df_kline.head()
        # oclh

        mpf.plot(df_adj_20d,type=type)
    def html(self, df, filename='work'):
        

        try:
            df.drop(columns='Unnamed: 0', inplace=True)
        except:
            pass
        
        df = df.dropna(axis='index', how='any', subset=['開盤價','最高價','最低價','收盤價'])


        # df.drop(columns='Unnamed: 0', inplace=True)
        df = df[[True if i.isdigit() else False for i in df['開盤價'].values ]]
        df = df[[True if i.isdigit() else False for i in df['到期月份(週別)'].values ]]
        # [f(x) if condition else g(x) for x in sequence]
    


        df['deathline'] = [int(str(i)[4:6]) for i in df['到期月份(週別)'].values ]
        df['trade_month'] = [ 
        int(re.findall(r'\d+', j)[1])+1 \
        if datetime.date(int(re.findall(r'\d+', j)[0]),int(re.findall(r'\d+', j)[1]),int(re.findall(r'\d+', j)[2]))\
        .__sub__(ThirdWed(int(re.findall(r'\d+', j)[0]),month=int(re.findall(r'\d+', j)[1]) ), ).days  >0\

        else int(re.findall(r'\d+', j)[1]) 

        for j in df['交易日期'].values  ]
        df.iloc[149:159]
        #%%

        # df['trade_month'] == df['deathline']
        df[df['trade_month'] == df['deathline']].iloc[23:29]

        #%%
        df_normal = df[df['trade_month'] == df['deathline']]
        # %%
        df_normal = df_normal.query('(交易時段 == "一般")')
        df_normal.reset_index(drop=True, inplace=True)
        

        #%%
        # 轉換型態

        def turn_int(name):
            df_normal[name] = np.array([int(i) for i in df_normal[name].values])
            # print(df_normal[name].describe())
            return df_normal[name]

        for i in ['開盤價','最高價','最低價','收盤價']:
            turn_int(i)



        


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

        # kline.render('./templates/dayK.html')


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

        # Volume.render('./templates/Volume.html')
        Volume.render_notebook()


        # %%

        def avg(num):
            result = []
            for i in range(0,len(df_kline['Close'].values)):
                if  i-num >=0:
                    result += ['{:.1f}'.format(df_kline['Close'].values[i-num:i].mean())]
                else:
                    # print(i)
                    # print(num)
                    # print(df_kline['Close'].values[i])
                    result += [df_kline['Close'].values[i]]
                # print((i,num))
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
            overlap = kline.overlap(line)
            # overlap.render('./templates/dayK.html')
            return overlap

        for i in [5,20,60]:
            overlap = drawavg(i)
        overlap.render(f'./templates/{filename}.html')

        return overlap.render_notebook()
    def __add__(self, other):
        all = []
        try:
            all = [pd.read_csv(self.path)]+[ pd.read_csv(other.path)]
        except UnicodeDecodeError:
            print(UnicodeDecodeError)
            all = [read(self.path)] + [read(other.path)]

        final= pd.concat(all)


        for i in range(len(final.columns)-1, -1, -1):
            try:
                final[list(final.columns)[i]] = final[list(final.columns)[i-1]]
            except Exception as e:
                print(e)
            if i == 0:
                final.drop(columns=list(final.columns)[i], inplace=True)
        return final

