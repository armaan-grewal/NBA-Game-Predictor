
# %%
import os
import pandas as pd
from bs4 import BeautifulSoup
from io import StringIO


# %%
def parse_html(box_score):
    with open(box_score) as file:
        html = file.read()

        soup = BeautifulSoup(html, "html.parser")
        #returns list of all text with header, and decompose removes it
        [s.decompose() for s in soup.select("tr.over_header")] #     
        [s.decompose() for s in soup.select("tr.thead")]       #removes the reserve line in box score
        return soup


# %%
def read_line_score(soup):

    #turn the soup into a string (take out of b.s), then process table that has id line_score
    line_score = pd.read_html(StringIO(str(soup)), attrs = {"id": "line_score"})[0] #StringIO required - pandas needs file-like object, not raw HTML string

    #name and clean the table
    cols = list(line_score.columns)
    cols[0] = "team"
    cols[-1] = "total"
    line_score.columns = cols

    line_score = line_score[["team", "total"]] #remove the quarterly numbers

    return line_score


# %%
def read_stats(soup, team, stats):
    #read the stats using panda and specific game id
    df = pd.read_html(StringIO(str(soup)), attrs= {"id": f"box-{team}-game-{stats}"}, index_col=0)[0]

    #if there is strings in box score, make it a null number
    df = df.apply(pd.to_numeric, errors="coerce")

    return df


# %%
def read_season(soup):
    #select by id
    nav = soup.select("#bottom_nav_container")[0]
    #get the link
    hrefs = [a["href"] for a in nav.find_all("a")]

    #last part of link, split at the _, get the first element
    season = os.path.basename(hrefs[1]).split("_")[0]
    return season

def main():

    # %%
    SCORE_DIR = "data/scores"

    # %%
    box_scores = os.listdir(SCORE_DIR)

    # %%
    box_scores = [os.path.join(SCORE_DIR, file) for file in box_scores if file.endswith(".html")]


    # %%
    base_cols = None
    games = []
    for box_score in box_scores:
        #using parse_html, open the directory and return html
        soup = parse_html(box_score)
        
        #get the table of game score
        line_score = read_line_score(soup)
        teams = list(line_score["team"])
        
        summaries = [] 
        for team in teams:
            basic = read_stats(soup, team, "basic")
            advanced = read_stats(soup, team, "advanced")
        
            #take the last row of basic and advanced and concatinate it in one single row for machine learning reading purposes
            total = pd.concat([basic.iloc[-1,:], advanced.iloc[-1,:]])
            total.index = total.index.str.lower()
        
        
            #get the max stat of each category and structure it the same as above 
            maxes = pd.concat([basic.iloc[:-1,:].max(), advanced.iloc[:-1,:].max()])
            maxes.index = maxes.index.str.lower() + "_max"
        
            summary = pd.concat([total, maxes])
        
            if base_cols is None:
                #remove duplicates from stats in both basic and advanced, keep first occurance of duplicates
                base_cols = list(summary.index.drop_duplicates(keep="first"))
                #remove bpm stat
                base_cols = [b for b in base_cols if "bpm" not in b]
        
            #only keep index's that are in base_cols 
            summary = summary[base_cols]
        
            #combine both teams summary into list
            summaries.append(summary)
            
        #merge both teams summaries into one to make it into one dataframe
        full_sum = pd.concat(summaries, axis=1).T
        
        #concat game score
        game = pd.concat([full_sum, line_score], axis = 1)
        
        #home vs away team
        game["home"] = [0,1]
        
        #make first row the second, for opponents row
        game_opp = game.iloc[::-1].reset_index()
        
        game_opp.columns += "_opp"
        
        full_game = pd.concat([game, game_opp], axis =1)
        
        #get year of game
        full_game["season"] = read_season(soup)
        
        #first 8 charectors gives the date
        full_game["date"] = os.path.basename(box_score)[:8]
        full_game["date"] = pd.to_datetime(full_game["date"], format="%Y%m%d")
        
        #who won specified by true/false
        full_game["won"] = full_game["total"] > full_game["total_opp"]
        games.append(full_game)
        

        if len(games) %100 == 0:
            print(f"{len(games)}/{len(box_scores)}")

    # %%
    games_df = pd.concat(games, ignore_index = True)

    # %%
    #games_df

    # %%
    games_df.to_csv("nba_games.csv")

    # %%


if __name__ == "__main__":
    main()
