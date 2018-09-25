import requests
import pandas as pd
from bs4 import BeautifulSoup
from quantUrls import quanturls

def appendDFToCSV_void(df, csvFilePath, sep=","):
    import os
    if not os.path.isfile(csvFilePath):
        df.to_csv(csvFilePath, mode='a', encoding='utf-8', index=False, sep=sep)
    elif len(df.columns) != len(pd.read_csv(csvFilePath, nrows=1, sep=sep).columns):
        raise Exception("Columns do not match!! Dataframe has " + str(len(df.columns)) + " columns. CSV file has " + str(len(pd.read_csv(csvFilePath, nrows=1, sep=sep).columns)) + " columns.")
  #  elif not (df.columns == pd.read_csv(csvFilePath, nrows=1, sep=sep).columns).all():
  #      raise Exception("Columns and column order of dataframe and csv file do not match!!")
    else:
        df.to_csv(csvFilePath, mode='a', encoding='utf-8', index=False, sep=sep, header=False)
   
def floatReturn(df):
    # Convert to float if possible
    for col in df:
        try:
            df[col] = df[col].astype(float)
        except ValueError:
            pass
    
    return df

class HTMLTableParser:
    
    def is_nhl_player(self,td_value):
        return len(td_value) > 0

    def is_nhl_league(self,td_value):
        return td_value == 'NHL'

    def parse_url(self, url, draftyear):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'lxml')
        return [(index,self.parse_html_table(table, draftyear))\
                for index, table in enumerate(soup.find_all('table', class_="draft_tbl"))]  

    def parse_det_url(self, url, playerName):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'lxml')
        return [(index,self.parse_html_table_det(table, playerName))\
                for index, table in enumerate(soup.find_all('table', id="r_stats"))]  

    def parse_html_table(self, table, draftyear):
        n_columns = 0
        n_rows=0
        column_names = []

        # Find number of rows and columns
        # we also find the column titles if we can
        for row in table.find_all('tr'):
            
            # Determine the number of rows in the table
            td_tags = row.find_all('td')
            if len(td_tags) > 0:
                if n_columns == 0:
                    # Set the number of columns for our table
                    n_columns = len(td_tags) + 1
                try:
                    if self.is_nhl_player(td_tags[6].get_text()):
                        n_rows+=1
                except:
                    print("Games played elemnt is not found")                
                    
            # Handle column names if we find them
            th_tags = row.find_all('th') 
            if len(th_tags) > 0 and len(column_names) == 0:
                column_names.append('Draft Year')
                for th in th_tags:
                    column_names.append(th.get_text())

        # Safeguard on Column Titles
        if len(column_names) > 0 and len(column_names) != n_columns:
            raise Exception("Column titles do not match the number of columns")

        columns = column_names if len(column_names) > 0 else range(0,n_columns)
        df = pd.DataFrame(columns = columns,
                            index= range(0,n_rows))
        row_marker = 0
        for row in table.find_all('tr'):
            column_marker = 0
            columns = row.find_all('td')
            
            try:
                if self.is_nhl_player(columns[6].get_text()):

                    for column in columns:
                        colText = column.get_text()
                        if column_marker == 3:
                            try:
                                link = 'https://www.quanthockey.com' + columns[2].find('a').get('href')
                                hpDet = HTMLTableParser()
                                alltables = hpDet.parse_det_url(link,colText)
                                dfDet = pd.DataFrame()
                                for table in alltables:
                                    dfDet = dfDet.append(table[1])
                                if columns[5].get_text() == 'G':
                                    appendDFToCSV_void(dfDet,'./data/QuantHockeyGoalieDet.csv')
                                else:
                                    appendDFToCSV_void(dfDet,'./data/QuantHockeySkaterDet.csv')
                            except:
                                #Only check for Player Name link for details
                                pass

                        if column_marker == 0:
                            df.iat[row_marker,0] = draftyear
                            df.iat[row_marker,1] = colText
                            column_marker = 1
                        else:
                            if column_marker == 2 and len(colText) < 1:
                                try:
                                    colText = columns[1].find('img').get('src')
                                except:
                                    colText = ''
                            df.iat[row_marker,column_marker] = colText

                        column_marker += 1
                    
                    if len(columns) > 0:
                        row_marker += 1
            except:
                #print("Games played elemnt is not found")                
                pass

        # Convert to float if possible
        return floatReturn(df)

    def parse_html_table_det(self, table, playerName):
        n_columns = 0
        n_rows=0
        column_names = []

        # Find number of rows and columns
        # we also find the column titles if we can
        for row in table.find_all('tr'):
            
            # Determine the number of rows in the table
            td_tags = row.find_all('td')
            if len(td_tags) > 0:
                try:
                    if self.is_nhl_league(td_tags[3].get_text()):
                        n_rows+=1
                        if n_columns == 0:
                            # Set the number of columns for our table
                            n_columns = len(td_tags) + 1
                except:
                    #Not NHL stat
                    pass                    

            # Handle column names if we find them
            th_tags = row.find_all('th') 
            if len(th_tags) > 0 and len(column_names) == 0:
                column_names.append('Name')
                for th in th_tags:
                    column_names.append(th.get_text())

        # Safeguard on Column Titles
        if len(column_names) > 0 and len(column_names) != n_columns:
            raise Exception("Column titles do not match the number of columns")

        columns = column_names if len(column_names) > 0 else range(0,n_columns)
        df = pd.DataFrame(columns = columns,
                            index= range(0,n_rows))
        row_marker = 0

        for row in table.find_all('tr'):
            column_marker = 0
            columns = row.find_all('td')

            try:
                if self.is_nhl_league(columns[3].get_text()):
                    for column in columns:
                        colText = column.get_text()
                        if column_marker == 0:
                            df.iat[row_marker,0] = playerName
                            df.iat[row_marker,1] = colText
                            column_marker = 1
                        else:
                            df.iat[row_marker,column_marker] = colText

                        column_marker += 1
                    
                    if len(columns) > 0:
                        row_marker += 1
            except:
                #print("Non NHL stats")                
                pass

        # Convert to float if possible
        return floatReturn(df)
        

for i in quanturls:
    hp = HTMLTableParser()
    alltables = hp.parse_url(i['url'],i['year'])
    print("Import stats for: "+str(i['year']))

    df = pd.DataFrame()
    for table in alltables:
        df = df.append(table[1])

    appendDFToCSV_void(df,'./data/QuantHockeyHead.csv')

