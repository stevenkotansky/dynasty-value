import pandas as pd
from requests import get
from bs4 import BeautifulSoup
from datetime import datetime
from os import path
from sklearn.preprocessing import MinMaxScaler


def get_ktc_trade_values(printval=True, mobile=False):
    if printval==True:
        print()
        print("Scraping KTC trade values")
    #get trade values from KTC website
    #can optionally specify superflex/non-SF (sf by default)
    #can optionally include draft pick values (included by default)

    def getTradeValues(superflex=True, include_picks=True, pagenum=int, rookies=False):
        if rookies==True:
            url = "https://keeptradecut.com/dynasty-rankings/rookie-rankings"
        else:
            url = f'https://keeptradecut.com/dynasty-rankings?page={pagenum}&filters=QB|WR|RB|TE'
        if include_picks:
            url = url + '|RDP'
        if not superflex:
            url = url + '&format=1'
        players = BeautifulSoup(get(url).text, features='lxml').select('div[id=rankings-page-rankings] > div')
        player_list = []
        for player in players:
            e = player.select('div[class=player-name] > p > a')[0]
            pid = e.get('href').split('/')[-1]
            name = e.text.strip()
            try:
                team = player.select('div[class=player-name] > p > span[class=player-team]')[0].text.strip()
            except:
                team = None
            position = player.select('p[class=position]')[0].text.strip()[:2]
            position = 'PICK' if position == 'PI' else position
            try:
                age = player.select('div[class=position-team] > p')[1].text.strip()[:2]
            except:
                age = None
            val = int(player.select('div[class=value]')[0].text.strip())
            val_colname = 'SF Value' if superflex else 'Non-SF Value'
            player_list.append({'PlayerID':pid,'Name':name,'Team':team,'Position':position,'Age':age,val_colname:val})
        return pd.DataFrame(player_list)

    #combine dataframes with superflex/non-sf values into single dataframe
    def combineTradeValues(sf_df, nonsf_df):
        merged_df = pd.merge(sf_df, nonsf_df, how='outer', on='PlayerID', suffixes=('_sf','_nonsf'))
        for col in ['Name','Team','Position','Age']:
            merged_df[col] = merged_df[col + '_sf'].fillna(merged_df[col + '_nonsf'])
        return merged_df[['PlayerID','Name','Team','Position','Age','SF Value','Non-SF Value']]

    #specify csv file name
    base_path = '/Users/steven/Library/CloudStorage/OneDrive-Personal/Documents/2024/fantasy_coding/dynasty-value/ktc/outfiles/'
    date_str = datetime.now().strftime('%Y%m%d')
    csv_path = base_path + 'all_players/ktc_' + date_str + '.csv'
    list_of_page_dfs = []
    #get superflex and non-superflex values
    sf_df = getTradeValues(superflex=True)
    nonsf_df = getTradeValues(superflex=False)

    for pagenum in range(0,10):
        list_of_page_dfs.append(getTradeValues(superflex=False, pagenum=pagenum, rookies=False))

    # merge pages into one
    full_df = pd.concat(list_of_page_dfs, ignore_index=True,axis=0)

    # drop duplicate player rows
    full_df = full_df.drop_duplicates(subset=["Name"], keep="last")

    # rename columns for later merging/comparing with JB
    full_df = full_df.drop(columns=["PlayerID"])
    full_df = full_df.rename(columns={"Name":"Player", "Non-SF Value":"KTC Trade Value"})

    # create normalized column
    # min-max scaler to normalize trade values
    scaler = MinMaxScaler()
    
    full_df['KTC_normalized'] = scaler.fit_transform(full_df[['KTC Trade Value']])
    full_df['KTC_normalized'] = (full_df['KTC_normalized']*100).astype(int)

    
    # save full thing to csv
    if mobile==False:
        full_df.to_csv(csv_path, index=False)


    #get rookie rankings
    base_path = '/Users/steven/Library/CloudStorage/OneDrive-Personal/Documents/2024/fantasy_coding/dynasty-value/ktc/outfiles/'
    date_str = datetime.now().strftime('%Y%m%d')
    csv_path = base_path + 'rookies/ktc_rookies_' + date_str + '.csv'
    #check if values already downloaded today
    if not path.exists(csv_path):
        #get superflex and non-superflex values
        rookie_df = getTradeValues(superflex=True, pagenum=0, rookies=True, include_picks=False)

        # save full thing to csv
        if mobile==False:
            rookie_df.to_csv(csv_path, index=False)

    if printval==True:
        print("Finished getting KTC trade values")
    return full_df