
# coding: utf-8
import os
import zipfile
import shutil
import re
import pandas as pd
import numpy as np
import datetime
import codecs
import urllib.request as r
import urllib.parse
import bs4
import calendar 
from FIMTX.Dataset import InvestDataset


import mplfinance as mpf
from pyecharts.charts import *
from pyecharts.components import Table
from pyecharts import options as opts
from pyecharts.commons.utils import JsCode
from pyecharts.globals import CurrentConfig
# CurrentConfig.ONLINE_HOST = "https://cdn.kesci.com/lib/pyecharts_assets/"
# CurrentConfig.ONLINE_HOST = "http://127.0.0.1:8000/assets/"

from typing import Union

from pyecharts.options.charts_options import GraphicItem, GraphicShapeOpts


def ThirdWed(year, month):
    year = int(year)
    check = 0
    for i in range(1,32):
        if datetime.date(year, month, i).isoweekday() ==3:
            check+=1
        if check==3:
            break 
    return  datetime.date(year, month, i)






def kl_format(file_path,Date, frequency=5):
    try:
        print('kl_format的檔案路徑：',file_path)
        df = pd.read_csv(file_path, encoding='utf-8').drop(columns='Unnamed: 0')[['成交日期','到期月份(週別)','成交時間','成交價格']]
    except:
        raise ValueError(f'{Date}  該日期不存在{file_path}')
    df = df[[True if str(i).isdigit() else False for i in df['到期月份(週別)'] ]]
    
    df['交易日期'] = [str(i)[:4]+'/'+str(i)[4:6]+'/'+str(i)[6:] for i in df['成交日期'].values]
    """篩選契約時段"""

    # print(df.head())
    # 只看小型台指早盤
    df['deathline'] = [int(str(i)[4:6]) for i in df['到期月份(週別)'].values ]
    df['trade_month'] = [ 
        int(re.findall(r'\d+', j)[1])+1 \
        if datetime.date(int(re.findall(r'\d+', j)[0]),int(re.findall(r'\d+', j)[1]),int(re.findall(r'\d+', j)[2]))\
        .__sub__(ThirdWed(int(re.findall(r'\d+', j)[0]),month=int(re.findall(r'\d+', j)[1]) ), ).days  >0\

        else int(re.findall(r'\d+', j)[1]) 

        for j in df['交易日期'].values  ]
    df = df[df['trade_month'] == df['deathline']]
    
    df.reset_index(drop=True, inplace=True)
    df.drop(columns='交易日期', inplace=True)
    """以時間當成INDEX"""
    # df['成交日期'] = pd.to_datetime(df['成交日期'],format = '%Y-%m-%d')
    df['成交時間'] = [ '{:0>6}'.format(str(i)) for i  in df['成交時間']  ]
    df['成交日期'] = [str(i) for i in df['成交日期']]
    df['成交精確時間'] = pd.to_datetime(df['成交日期']+df['成交時間'],format = '%Y%m%d%H%M%S')
    df.index = pd.DatetimeIndex(df['成交精確時間'])

    """分K分群"""                    
            
    key = 0
    check = datetime.datetime(
        df['成交精確時間'][0].year, 
        df['成交精確時間'][0].month,
        df['成交精確時間'][0].day,
        15, 0, 0)
    #  df['成交精確時間'][0]
    result = []

    for i in range(0,len(df['成交精確時間'].values)):
        time = df['成交精確時間'][i]-datetime.timedelta(seconds=df['成交精確時間'][i].second)
        
        if check!=time+datetime.timedelta(seconds=60*(frequency-time.minute%frequency)):

            check= time+datetime.timedelta(seconds=60*(frequency-time.minute%frequency))
            key+=1
            # debug+=[i]
        result+=[key]
    df['第幾根K棒'] = result    

    """格式化"""

    """時間"""
    format_final = (df.groupby(by=['第幾根K棒'])
    ['成交精確時間'].max()
    .reset_index()
    .rename(columns = {'成交精確時間': '結束時間'})
                    )
    format_final['結束時間'] = [datetime.time(i.hour,i.minute,i.second)for i in format_final['結束時間']]

    format_start = (df.groupby(by=['第幾根K棒'])
            ['成交精確時間'].min()
            .reset_index()
            .rename(columns = {'成交精確時間': '開始時間'})
    )
    format_start['開始時間'] = [datetime.time(i.hour,i.minute,i.second)for i in format_start['開始時間']]

    format_YMD = (df.groupby(by=['第幾根K棒'])
            ['成交精確時間'].min()
            .reset_index()
            .rename(columns = {'成交精確時間': '交易日期'})
    )
    format_YMD['交易日期'] = [datetime.date(i.year,i.month,i.day)for i in format_YMD['交易日期']]

    """時間欄位合併"""
    format_date = format_start.merge(format_final,
    left_on = '第幾根K棒', right_on = '第幾根K棒', )
    format_date = format_date.merge(format_YMD,
    left_on = '第幾根K棒', right_on = '第幾根K棒', how='left')


    """價錢"""
    format_h = (df.groupby(by=['第幾根K棒'])
            ['成交價格'].max()
            .reset_index()
            .rename(columns = {'成交價格': '最高價'})
    )
    format_l = (df.groupby(by=['第幾根K棒'])
            ['成交價格'].min()
            .reset_index()
            .rename(columns = {'成交價格': '最低價'})    
    )
    format_hl = format_h.merge(format_l,
    left_on = '第幾根K棒', right_on = '第幾根K棒', )

    #%%

    format_hl['開盤價'] = [df.query('(第幾根K棒 == @i)')['成交價格'][0] for i in range(1,len(format_hl['第幾根K棒'])+1)]
    format_hl['收盤價'] = [df.query('(第幾根K棒 == @i)')['成交價格'][-1] for i in range(1,len(format_hl['第幾根K棒'])+1)]
    format_ohlc = format_hl[['第幾根K棒','開盤價','最高價', '最低價', '收盤價']]
    """價錢欄位合併"""
    
    kl_format=format_ohlc.merge(format_date,
    left_on = '第幾根K棒', right_on = '第幾根K棒', how='left')
    np.save(f'/app/MTXFinalData/Format/{Date}', kl_format)
    return kl_format  
def press_table(kl_format, Date):
    df = kl_format.set_index('第幾根K棒', drop=True).reset_index()
    train_df = df[["開盤價","最高價","最低價","收盤價", ]]

    """整理出現過的價格"""
    price = []
    train_df = df[["開盤價","最高價","最低價","收盤價", ]]
    train_df = df[["開盤價","最高價","最低價","收盤價", ]]

    for i in [train_df[i].values.tolist() for i in train_df.columns]:
        price+=i

    """計算每個的價格交易的次數"""

    press_table = pd.Series(sorted(price)).value_counts().reset_index().rename(columns={'index':'price'}).set_index('price', drop=True)
    press_table['次數'] = press_table[0].values
    press_table.drop(columns=0, inplace=True)
    press_table.reset_index(inplace=True)
    np.save(f'/app/MTXFinalData/PressTable/{Date}', press_table)
    return press_table


def all_price_date(price):
    tables = pd.DataFrame()
    related_date = []
    data = InvestDataset()
    for i in data:
        b = PressLine(i)
        max = b.kl_format[['開盤價', '最高價', '最低價', '收盤價']].max().max()
        min = b.kl_format[['開盤價', '最高價', '最低價', '收盤價']].min().min()
        if price<max and price>min:
            related_date += [i]
            tables = tables.append(b.press_table).sort_values(by=['price'],ascending=True).reset_index(drop=True)
    if not related_date:
        raise ValueError('沒有符合這個點位的日期')
    tables = tables.groupby(['price']).sum().reset_index()
    return (tables,related_date)
def global_search_press(search_price ):
        press_table, related_date = all_price_date(search_price)
        press_table = press_table.sort_values(by=['price'], ascending=True)
        x_data =[str(i) for i in  press_table['price'].values]
        y_data = [int(i) for i in press_table['次數'].values]
        file_name = str(search_price)

        # bar = (Bar(
        line = (Line(
            init_opts=opts.InitOpts(
        width='100vw', 
        height='100vh', 
        bg_color='black',
        page_title = file_name+'壓力圖',
        theme='chalk',
                            )
        )
       .add_xaxis(x_data)
       .add_yaxis('', y_data)
       .set_global_opts(

            title_opts=opts.TitleOpts(
                    title='點位：'+str(search_price)+'的搜尋結果', 
                    subtitle=str(related_date),
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

            tooltip_opts=opts.TooltipOpts(
                    is_show=True,
                    trigger_on="mousemove|click",# 鼠标移动或者点击时触发
                    axis_pointer_type = "cross",
                    # background_color="green",
                    # textstyle_opts=opts.TextStyleOpts(color='red'),

                                            ),
            datazoom_opts=opts.DataZoomOpts(
                    is_show=True,
                    is_realtime = True, 
                    range_start=60,
                    range_end=80, 
                    # orient="vertical",
                                                ),
            graphic_opts=
        [opts.GraphicGroup
            (   
                graphic_item=opts.GraphicItem(
                    #    rotation=JsCode("Math.PI / 4"),
                    #    bounding="raw",
                    #    right=110,
                    #    bottom=110,
                    #    z=100,
                    width='100vw',
                    height='100vh',
                                            ),
                children=[
                    opts.GraphicRect(
                        graphic_item=opts.GraphicItem(
                            # left="center", top="center", z=2
                            width='100vw',
                            height='100vh',
                                                    ),
                        graphic_shape_opts=opts.GraphicShapeOpts(
                            width='100vw',
                            height='100vh',
                                                                ),
                        # graphic_basicstyle_opts=opts.GraphicBasicStyleOpts(
                            # fill="rgba(0,0,0,0.3)"
                                                                        # ),
                                    ),
                    # opts.GraphicText(
                    #     graphic_item=opts.GraphicItem(
                    #         left="center", top="center", z=2
                    #                                     ),
                    #     graphic_textstyle_opts=opts.GraphicTextStyleOpts(
                    #         text='',
                    #         font="bold 26px Microsoft YaHei",
                    #         graphic_basicstyle_opts=opts.GraphicBasicStyleOpts(
                    #             fill="#fff"
                    #                                                             ),
                    #                                                     ),
                    #                 ),
                    
                    opts.GraphicImage(
                        graphic_item=opts.GraphicItem(
                            width='100vw',
                            height='100vh',
                                            ),
                        graphic_imagestyle_opts=opts.GraphicImageStyleOpts(
                            width='100vh',
                            height='100vw',
                        )
                    )
                        
                    
                        ],
            )
        ],

                        )
      )
        line.render(f'./templates/{file_name}press.html')
        # return line.render_notebook()
        return line
    


















class PressLine():
    def __init__(self, Date, update = False) -> None:
        now_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath('__file__'))))
        folder_path = now_path+'/TradingData'+'/MTX'   
        self.Date = '-'.join(['{:0>2}'.format(str(i)) for i in  re.findall(r'\d*',str(Date) )if i ])
        self.file_path = folder_path+'/'+'MTX-'+self.Date+'.csv'
        path =['/app/MTXFinalData/Format','/app/MTXFinalData/PressTable']
        for i in path:
            if not os.path.isdir(i):  
                    os.makedirs(i, exist_ok =True)
        print('判斷：',f'/app/MTXFinalData/Format/{self.Date}.npy')
        print(os.path.isfile(f'/app/MTXFinalData/Format/{self.Date}.npy'))
        print(not update)
        if os.path.isfile(f'/app/MTXFinalData/Format/{self.Date}.npy') and not update:
            
            self.kl_format = pd.DataFrame(np.load(f'/app/MTXFinalData/Format/{self.Date}.npy', allow_pickle=True), columns=['第幾根K棒', '開盤價', '最高價', '最低價', '收盤價', '開始時間', '結束時間', '交易日期'])
            self.press_table = pd.DataFrame(np.load(f'/app/MTXFinalData/PressTable/{self.Date}.npy', allow_pickle=True), columns=['price', '次數'])

        else:
            print("更新中")
            data = InvestDataset()
            data.download(self.Date)
            self.kl_format = kl_format(self.file_path, self.Date, frequency=5)
            self.press_table = press_table(self.kl_format, self.Date)
        
        dirPath = 'TradingData'
        try:
            shutil.rmtree(dirPath)
        except:
            pass

    def price_info(self, search_price):
        o = self.kl_format.query('開盤價 == @search_price')['第幾根K棒'].values.tolist()
        h = self.kl_format.query('最高價 == @search_price')['第幾根K棒'].values.tolist()
        l = self.kl_format.query('最低價 == @search_price')['第幾根K棒'].values.tolist()
        c = self.kl_format.query('收盤價 == @search_price')['第幾根K棒'].values.tolist()
        # all = o.append(h).append(l).append(c).reset_index(drop=True)
        # all = all.sort_values(by=['第幾根K棒'],ascending=True).reset_index(drop=True)
        search = np.unique(o+h+l+c)
        result = pd.DataFrame()
        for i in search:
            result = result.append(self.kl_format.query('第幾根K棒 == @i'))
        result = result.sort_values(by=['第幾根K棒'],ascending=True).reset_index(drop=True)
        return result
    
    def price_region(self):
        pass

    def local_search_press(self, search_price, n=5):
        
        press_table = self.press_table.sort_values(by=['price'],ascending=False).reset_index(drop=True)
        """排出搜尋價格上下n點的檔位壓力"""
        search_price = search_price
        mid_index = press_table.query('price == @search_price').index[0]
        print(mid_index)
        mid_index = mid_index if mid_index >=5 else 5
        return press_table.iloc[mid_index-n:mid_index+n,]

    def global_search_press(self, press_table=None,search_price = None, n=5 ):
        # press_table = self.press_table.sort_values(by=['次數'], ascending=False)
        if press_table:
            press_table = press_table.sort_values(by=['price'], ascending=True)
        else:
            press_table = self.press_table.sort_values(by=['price'], ascending=True)
        # print(press_table.sort_values(by=['次數'], ascending=False)[:top])
        x_data =[str(i) for i in  press_table['price'].values]
        y_data = [int(i) for i in press_table['次數'].values]
        file_name = self.Date

        # bar = (Bar(
        line = (Line(
            init_opts=opts.InitOpts(
        width='100vw', 
        height='100vh', 
        bg_color='black',
        page_title = file_name+'壓力圖',
        theme='chalk',
                            )
        )
       .add_xaxis(x_data)
       .add_yaxis('', y_data)
       .set_global_opts(

            title_opts=opts.TitleOpts(
                    title='此圖最後更新時間：'+self.Date+'  '+str(self.kl_format['結束時間'].iloc[-1]), 
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

            tooltip_opts=opts.TooltipOpts(
                    is_show=True,
                    trigger_on="mousemove|click",# 鼠标移动或者点击时触发
                    axis_pointer_type = "cross",
                    # background_color="green",
                    # textstyle_opts=opts.TextStyleOpts(color='red'),

                                            ),
            datazoom_opts=opts.DataZoomOpts(
                    is_show=True,
                    is_realtime = True, 
                    range_start=60,
                    range_end=80, 
                    # orient="vertical",
                                                ),
            graphic_opts=
        [opts.GraphicGroup
            (   
                graphic_item=opts.GraphicItem(
                    #    rotation=JsCode("Math.PI / 4"),
                    #    bounding="raw",
                    #    right=110,
                    #    bottom=110,
                    #    z=100,
                    width='100vw',
                    height='100vh',
                                            ),
                children=[
                    opts.GraphicRect(
                        graphic_item=opts.GraphicItem(
                            # left="center", top="center", z=2
                            width='100vw',
                            height='100vh',
                                                    ),
                        graphic_shape_opts=opts.GraphicShapeOpts(
                            width='100vw',
                            height='100vh',
                                                                ),
                        # graphic_basicstyle_opts=opts.GraphicBasicStyleOpts(
                            # fill="rgba(0,0,0,0.3)"
                                                                        # ),
                                    ),
                    # opts.GraphicText(
                    #     graphic_item=opts.GraphicItem(
                    #         left="center", top="center", z=2
                    #                                     ),
                    #     graphic_textstyle_opts=opts.GraphicTextStyleOpts(
                    #         text='',
                    #         font="bold 26px Microsoft YaHei",
                    #         graphic_basicstyle_opts=opts.GraphicBasicStyleOpts(
                    #             fill="#fff"
                    #                                                             ),
                    #                                                     ),
                    #                 ),
                    
                    opts.GraphicImage(
                        graphic_item=opts.GraphicItem(
                            width='100vw',
                            height='100vh',
                                            ),
                        graphic_imagestyle_opts=opts.GraphicImageStyleOpts(
                            width='100vh',
                            height='100vw',
                        )
                    )
                        
                    
                        ],
            )
        ],

                        )
      )
        # line.render(f'./templates/{file_name}press.html')
        # return line.render_notebook()
        return line
    

    def wash(self):
        pass

    def __str__(self) -> str:
        return self.file_path
    
    # def __add__(self, other):
    #     return self.press_table.append(other.press_table.append, ignore_index=True,).reset_index(drop=True)
        

