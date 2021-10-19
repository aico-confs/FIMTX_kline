import pandas as pd
import numpy as np
import datetime
import re
import zipfile
import os
import codecs
import urllib.request as r
import bs4

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
        
        self.date = [i.replace('/', '-') for i in date_list()]
        
        
        
    
    def download(self, Date , del_zip=True):
        
        
        Date = '-'.join(['{:0>2}'.format(str(i)) for i in  re.findall(r'\d*',str(Date) )if i ])
        if Date in self.date:
            Date = Date.replace('-', '_')
            file_name = 'Daily_'+f'{Date}.zip'
        else:

            raise ValueError(f'{Date}  該日期不存在資料可以下載')
        first = datetime.datetime.now()
        url = f'https://www.taifex.com.tw/file/taifex/Dailydownload/DailydownloadCSV/{file_name}'
        """下載檔案"""
        request=r.Request(url,  headers={
        "user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36"
             } )
        with r.urlopen(request) as response:
            TradingData=response.read()
        with open(f"/app/{file_name}", 'wb') as f:
            f.write(TradingData)
            print('zip檔OK了')
        
        destination = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath('__file__'))))
        print(f'正在下載{Date}的資料至當前目錄：'+'\n', '「'+destination+'」')
        # print('!!!!===================!!!!!!')
        # path = '/app'
        # for filename in os.listdir(path):
        #     print(filename)
        # print('!!!!===================!!!!!!')
        check = True

        zip_path = destination+'/'+f"{file_name}"
        print(zip_path)
        while check:
            if os.path.isfile(zip_path):
                check = False
            else:
                if (datetime.datetime.now()-first).seconds>60:
                    print(f'已經等待{datetime.datetime.now()-first}秒')
                    print('提示：可點擊以下連結直接下載')
                    print(url)
                    check = False
                    raise RuntimeError('逾時太長，已取消下載')

        """解壓縮"""
        zf = zipfile.ZipFile(zip_path, 'r')
        zf.extractall()
        zf.close()
        
        """建立路徑"""
        path = []
        Rawpath = destination+'/TradingData'+'/RawData'
        MTXpath = destination+'/TradingData'+'/MTX'
        path +=[Rawpath,MTXpath]
        print(path)
        for i in path:
            if not os.path.isdir(i):  
                os.makedirs(i, exist_ok =True)
        file_name = file_name.replace('.zip', '.csv')
        """轉碼、移除空格"""
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
        """存資料"""
        data_name = file_name.replace('_', '-')
        # data_name = file_name.replace('_', '-').replace('2021', '')
        df.to_csv(Rawpath+'/'+data_name.replace('Daily', 'Raw'), encoding='utf-8')
        search = 'MTX'
        MTX_df= df.query('商品代號 == @search')
        MTX_df.to_csv(MTXpath+'/'+data_name.replace('Daily', 'MTX'), encoding='utf-8')
        print('DATASET MTX路徑：',MTXpath+'/'+data_name.replace('Daily', 'MTX'))
        """刪掉原本的檔案"""
        if del_zip:
            try:
                os.remove(destination+'/'+file_name)
                os.remove(zip_path)
            except OSError as e:
                print(zip_path)
                print(f"OS的Error:{ e.strerror}")

    def __len__(self):
        return  len(self.date)
    
    def __getitem__(self, item):
        return self.date[item]

    def __str__(self) -> str:
        return str(self.date)
    def date_df(self):
        result = self.date
            
        return pd.DataFrame({
            'Date':result
        })
