# coding: utf-8
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
from typing import Union


"""
時刻K線圖：
https://www.taifex.com.tw/cht/3/dlFutPrevious30DaysSalesData

每天日K查詢：
https://www.taifex.com.tw/cht/3/dlFutDailyMarketView
https://mis.taifex.com.tw/futures/RegularSession/EquityIndices/FuturesDomestic/

"""
def ThirdWed(year):
    year = int(year)
    check = 0
    for i in range(1,32):
        if datetime.date(year, 1, i).isoweekday() ==3:
            check+=1
        if check==3:
            break 
    return  datetime.date(year, 1, i)

def read(file_path):
    my_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath('__file__'))))
    path = os.path.join(my_path, file_path)

    # with open(path, 'r', encoding='UTF-8', errors='ignore') as f:
    with codecs.open(path,'rU','Big5') as doc:
        return pd.read_csv(doc, encoding='utf8', error_bad_lines=False)
def date_list( url='https://www.taifex.com.tw/cht/3/dlFutPrevious30DaysSalesData'):
        request=r.Request(url,  headers={
        "user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36"
             }  )

        with r.urlopen(request) as response:
            TradingData=response.read().decode("utf-8")
        # print(TradingData)
        root=bs4.BeautifulSoup(TradingData, "html.parser")
        # table=root.find_all("tr",class_="color")
        table=root.find_all("tr")
        answer = []
        for excats in table:
            for excat in list(excats.children):
                if excat.string != None:
                    if len(excat.string)==10:
                        answer+=[excat.string]

        return answer
    
class InvestDataset():
    def __init__(self) -> None:
        self.date = date_list()
        
    
    def download(self, Date , del_zip=True):
        
        first = datetime.datetime.now()
        Date = '/'.join(['{:0>2}'.format(str(i)) for i in  re.findall(r'\d*',str(Date) )if i ])
        if Date in self.date:
            Date = Date.replace('/', '_')
            file_name = 'Daily_'+f'{Date}.zip'
        else:

            raise ValueError(f'{Date}  該日期不存在')
        
        url = f'https://www.taifex.com.tw/file/taifex/Dailydownload/DailydownloadCSV/{file_name}'
        request=r.Request(url,  headers={
        "user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36"
             } )
        with r.urlopen(request) as response:
            TradingData=response.read()
        with open(f"{file_name}.zip", 'wb') as f:
            f.write(TradingData)
        
        destination = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath('__file__'))))
        print(f'正在下載{Date}的資料至當前目錄：'+'\n', '「'+destination+'」')
        check = True
        active = True
        zip_path = destination+'\\'+f"{file_name}.zip"
        while check:
            if os.path.isfile(zip_path):
                check = False
            else:
                if (datetime.datetime.now()-first).seconds%10>8:
                    print(f'已經等待{datetime.datetime.now()-first}秒')
                    print('提示：可點擊以下連結直接下載')
                    print(url)
                    if input('請問要繼續等嗎?(y/N)').strip().lower() == 'y':
                        continue
                    else:
                        check = False
                        active = False
                        break
                continue
        if active == False:
            raise RuntimeError('已取消下載')
        zf = zipfile.ZipFile(zip_path, 'r')
        zf.extractall()
        zf.close()
        file_name = file_name.replace('.zip', '.csv')

        """轉碼、移除空格"""
        path = []
        Rawpath = destination+'\\TradingData'+'\\RawData'
        MTXpath = destination+'\\TradingData'+'\\MTX'
        path +=[Rawpath,MTXpath]
        for i in path:
            if not os.path.isdir(i):  
                os.makedirs(i, exist_ok =True)
        df = read(file_name)
        for i in df.columns:
            try:
                df[i] = np.array([str(i).strip() for i in df[i].values ])
            except Exception as e:
                print(e)
                try:
                    df[i] = np.array([int(i) for i in df[i].values ])
                except:
                    pass

        data_name = file_name.replace('_', '').replace('2021', '')
        df.to_csv(Rawpath+'\\'+data_name.replace('Daily', 'Raw'), encoding='utf-8')
        search = 'MTX'
        MTX_df= df.query('商品代號 == @search')
        MTX_df.to_csv(MTXpath+'\\'+data_name.replace('Daily', 'MTX'), encoding='utf-8')


        os.remove(destination+'\\'+file_name)
        if del_zip:
            try:
                os.remove(zip_path)
            except OSError as e:
                print(zip_path)
                print(f"OS的Error:{ e.strerror}")

    def __len__(self):
        return  len(self.date)
    
    def __getitem__(self, item):
        return self.date[item]

    def date_df(self):
        result = self.date
            
        return pd.DataFrame({
            'Date':result
        })
        
        

class month_analysis():
    def __init__(self, month:Union[str, int], year:Union[str, int] = 2021) :
        self.month = '{:0>2}'.format(month)
        self.year = year
        self.date = calendar.monthcalendar(year, month)
        if not os.path.isdir(f'./TradingData/dayk/{self.month}.csv'):  
            raise FileNotFoundError('必須先download()至指定資料夾，才能啟用模型功能')

    
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
        print(values)
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
#%%
        # 只看小型台指早盤
        df['deathline'] = [int(str(i)[4:6]) for i in df['到期月份(週別)'].values ]
        df['trade_month'] = [ int(re.findall(r'\d+', j)[1])+1 \
        if datetime.date(int(re.findall(r'\d+', j)[0]),int(re.findall(r'\d+', j)[1]),int(re.findall(r'\d+', j)[2]))\
        .__sub__(ThirdWed(int(re.findall(r'\d+', j)[0]))).days % 28 >(((int(re.findall(r'\d+', j)[1])-1)//3))*7\
            else int(re.findall(r'\d+', j)[1]) for j in df['交易日期'].values  ]

        df_normal = df.query('(交易時段 == "一般")')
        df_normal = df_normal[df['trade_month'] == df['deathline']]
        df_normal.reset_index(drop=True, inplace=True)
            
#%%
        # 轉換型態

        def turn_int(name):
            df_normal[name] = np.array([int(i) for i in df_normal[name].values])
            # print(df_08_normal[name].describe())
            return df_normal[name]

        for i in ['開盤價','最高價','最低價','收盤價']:
            turn_int(i)


        df_normal['交易日期'] = pd.to_datetime(df_normal['交易日期'],format = '%Y-%m-%d')
        df_normal.head()


    #%%
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
        # %%
        # oclh

        mpf.plot(df_adj_20d,type=type)