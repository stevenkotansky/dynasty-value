import pandas as pd
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from sklearn.preprocessing import MinMaxScaler

def get_jb_trade_values(printval=True):
    if printval==True:
        print()
        print()
        print("Scraping Justin Boone Trade Values")
    def fetch_dynasty_tables(url: str, starting_page="QB", filename_prefix="Dynasty_Trade_Value"):

        pages_to_process = ["QB", "RB", "WR", "TE", "Draft Picks"]
        current_page = starting_page

        # Get the HTML content from the URL
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes

        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')

        title = soup.find("h1").text
        if printval==True:
            print(f"Scraping Rankings from {title} \n{url}")

        # Find the first table in the HTML
        table = soup.find('table')

        # Convert the HTML table to a Pandas DataFrame
        df = pd.read_html(str(table))[0]

        # Drop and Rename Columns
        if current_page in ["QB", "Draft Picks"]:
            df = df.drop(columns=['2QB'])
            df = df.rename(columns={"1QB":"Trade Value"})
        elif current_page in ["RB", "WR"]:
            df = df.rename(columns={"PPR":"Trade Value"})
        elif current_page in ["TE"]:
            df = df.drop(columns=["TE Prem."])
            df = df.rename(columns={"PPR":"Trade Value"})

        # Find the <time> element and get the datetime attribute
        time_element = soup.find('time', datetime=True)
        if time_element:
            datetime_value = time_element['datetime']
            # Parse the datetime string
            dt = datetime.strptime(datetime_value, "%Y-%m-%dT%H:%M:%S.%fZ")

            # Convert to desired format
            datetime_value = dt.strftime("%m-%d-%Y_%I:%M%p")
        else:
            datetime_value = None


        dict_of_tables = {"QB": None, "RB": None, "WR": None, "TE": None, "Draft Picks": None}

        dict_of_tables[starting_page] = df

        
        if current_page==starting_page:
            # Find all <a> elements with the data-in-app-uri attribute and extract their text and href values
            links = {a.get_text(): a['href'] for a in soup.find_all('a', {'data-in-app-uri': True})}
            # drop current page from list of pages to process
            pages_to_process.remove(current_page)
        
        # loop through remaining pages
        for page in pages_to_process:
            current_page = page
            # move to the next page in the list
            url = links[page]
            # Get the HTML content from the URL
            response = requests.get(url)
            response.raise_for_status()  # Raise an error for bad status codes

            # Parse the HTML content
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find the first table in the HTML
            table = soup.find('table')

            # Convert the HTML table to a Pandas DataFrame
            df = pd.read_html(str(table))[0]

            # Drop and Rename Columns
            if current_page in ["QB", "Draft Picks"]:
                df = df.drop(columns=['2QB'])
                df = df.rename(columns={"1QB":"Trade Value", "Rk":"RK"})
            elif current_page in ["RB", "WR"]:
                df = df.rename(columns={"PPR":"Trade Value", "Rk":"RK"})
            elif current_page in ["TE"]:
                df = df.drop(columns=["TE Prem."])
                df = df.rename(columns={"PPR":"Trade Value", "Rk":"RK"})

            # append current df to dict
            dict_of_tables[page] = df

        dict_of_dfs = dict_of_tables

        # save outfiles
        # dict_of_dfs["QB"].to_csv(f"outfiles/QB_{filename_prefix}_{datetime_value}.csv", index=False)
        # dict_of_dfs["RB"].to_csv(f"outfiles/RB_{filename_prefix}_{datetime_value}.csv", index=False)
        # dict_of_dfs["WR"].to_csv(f"outfiles/WR_{filename_prefix}_{datetime_value}.csv", index=False)
        # dict_of_dfs["TE"].to_csv(f"outfiles/TE_{filename_prefix}_{datetime_value}.csv", index=False)
        combined_df = pd.concat([dict_of_dfs["QB"], dict_of_dfs["RB"]], ignore_index=True, axis=0)
        combined_df = pd.concat([combined_df, dict_of_dfs["WR"]], ignore_index=True, axis=0)
        combined_df = pd.concat([combined_df, dict_of_dfs["TE"]], ignore_index=True, axis=0)
        combined_df = combined_df.drop(columns=["RK"])
        combined_df = combined_df.sort_values(by="Trade Value", ascending=False)
        combined_df = combined_df.rename(columns={"Trade Value": "JB Trade Value"})

        # min-max scaler to normalize trade values
        scaler = MinMaxScaler()
        
        combined_df['JB_normalized'] = scaler.fit_transform(combined_df[['JB Trade Value']])
        combined_df['JB_normalized'] = (combined_df['JB_normalized']*100).astype(int)

        combined_df.to_csv(f"jb/outfiles/dynasty/players_{filename_prefix}_{datetime_value}.csv", index=False)
        dict_of_dfs["Draft Picks"].to_csv(f"jb/outfiles/dynasty/Draft_Picks_{filename_prefix}_{datetime_value}.csv", index=False)





        return dict_of_tables, datetime_value, filename_prefix, combined_df

    # Get most recent dynasty rankgs
    url = "https://www.thescore.com/nfl/news/2934869/fantasy-dynasty-trade-value-chart-july-edition"
    dict_of_dfs, datetime_value, filename_prefix, combined_df = fetch_dynasty_tables(url, starting_page="QB", filename_prefix="Dynasty_Trade_Value")
    if printval==True:
        print("Finished scraping Justin Boone trade values")

    # need to stack the dfs all into one and adjust JB pick value/names, then make normalized values, then value checker for buys and sells

    return combined_df


def get_jb_redraft(printval=True):
    if printval==True:
        print()
        print()
        print("Scraping Justin Boone Redraft Values")
    def fetch_redraft_tables(url: str):

        # Get the HTML content from the URL
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes

        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')

        title = soup.find("h1").text
        if printval==True:
            print(f"Scraping Rankings from {title} \n{url}")

        # Find the first table in the HTML
        table = soup.find('table')

        # Convert the HTML table to a Pandas DataFrame
        df = pd.read_html(str(table))[0]

        # Find the <time> element and get the datetime attribute
        time_element = soup.find('time', datetime=True)
        if time_element:
            datetime_value = time_element['datetime']
            # Parse the datetime string
            dt = datetime.strptime(datetime_value, "%Y-%m-%dT%H:%M:%S.%fZ")

            # Convert to desired format
            datetime_value = dt.strftime("%m-%d-%Y_%I:%M%p")
        else:
            datetime_value = None
        
        # save outfiles
        redraft_rankings_df = df

        redraft_rankings_df.to_csv(f"jb/outfiles/redraft/players_redraft_rankings_{datetime_value}.csv", index=False)


        return redraft_rankings_df

    # Get most recent redraft rankgs
    url = "https://www.thescore.com/nflfan/news/2817340/fantasy-2024-rankings-top-250-updated"
    redraft_rankings_df = fetch_redraft_tables(url)
    if printval==True:
        print("Finished scraping Justin Boone redraft trade values")

    # need to stack the dfs all into one and adjust JB pick value/names, then make normalized values, then value checker for buys and sells

    return redraft_rankings_df