# %%
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit    #TimeSeriesSplit is for cross-validation
from sklearn.feature_selection import SequentialFeatureSelector 
from sklearn.linear_model import RidgeClassifier      #machine learning model

pd.options.mode.chained_assignment = None


# %%
df = pd.read_csv("nba_games.csv", index_col=0)

# %%
#sort by date and reset the index after
df = df.sort_values("date")
df = df.reset_index(drop = True)

# %%
#delete identicle columns
del df["mp.1"]
del df["mp_opp.1"]
del df["index_opp"]


# %%
#function to show how team did the next game
def add_target(team):
    team = team.copy()  
    #target column will be how the team did next game
    team["target"] = team["won"].shift(-1)    
    return team

#split dataframe grouped by teams, pass each team into the add_target funciton
df = df.groupby("team", group_keys = False).apply(add_target)
df = df.copy()  # re-allocates memory efficiently

# %%
#replace all null values (last game of szn) with 2
df.loc[pd.isnull(df["target"]), "target"] = 2

# %%
#turn true and false into 0 and 1
df["target"] = df["target"].astype(int, errors="ignore")

# %%
#celtics shot 0 free throws one game resulting in ft% as null, set that as 0
df.loc[pd.isnull(df["ft%"]), "ft%"] = 0.0
df.loc[pd.isnull(df["ft%_max"]), "ft%_max"] = 0.0
df.loc[pd.isnull(df["ft%_opp"]), "ft%_opp"] = 0.0
df.loc[pd.isnull(df["ft%_max_opp"]), "ft%_max_opp"] = 0.0


# %%
#remove all nulls
nulls = pd.isnull(df)

# %%
nulls = nulls.sum()

# %%
nulls = nulls[nulls>0]

# %%
#keep all columns that is not in the nulls variable and assign to valid_cols
valid_cols = df.columns[~df.columns.isin(nulls.index)]

# %%
df = df[valid_cols].copy()


rr = RidgeClassifier(alpha =1)
split = TimeSeriesSplit(n_splits=3)

#pass 30/142 columns first, at end we will find the 30 best stats to use in the model
sfs = SequentialFeatureSelector(rr, n_features_to_select = 30, direction = "forward", cv = split)

# %%
remove_cols = ["season", "date", "won", "target", "team_opp", "team"] 

# %%
#select all columns except the ones in the remove_cols
selected_cols = df.columns[~df.columns.isin(remove_cols)]

# %%
from sklearn.preprocessing import MinMaxScaler
#rescale the stats from 0 to 1 for better performance of ridgeselector
scaler = MinMaxScaler()
df[selected_cols] = scaler.fit_transform(df[selected_cols])

# %%
#df[selected_cols]

# %%
sfs.fit(df[selected_cols], df["target"])

# %%
#if feature selector thinks the column should be used in model, this returns True
predictors = list(selected_cols[sfs.get_support()])


# %%
#for getting past seasons to predict future seasons
def backtest(data, model, predictors, start = 2, step = 1):
    all_predictions = []
    seasons = sorted(data["season"].unique())

    #start at the second indexed season in seasons
    for i in range(start, len(seasons), step):
        #get season number
        season = seasons[i]

        #get all seaons that come before current season
        train = data[data["season"] < season]
        #current season
        test = data[data["season"] == season]

        #train and predict based on target
        model.fit(train[predictors], train["target"])
        
        #this returns numpy array so convert it into panda series
        preds = model.predict(test[predictors])
        preds = pd.Series(preds, index =test.index)

        #combine the predictions and the real result
        combined = pd.concat([test["target"], preds], axis = 1)
        combined.columns = ["actual", "prediction"]


        all_predictions.append(combined)
    return pd.concat(all_predictions)


        


# %%

# %%
df_rolling = df[list(selected_cols) + ["won", "team", "season"]]


# %%
def find_team_averages(team):
    #get last 10 games using pandas rolling method and find the mean, seperate the numeric and non-numeric
    numeric = team.select_dtypes(include=["number"]).rolling(10).mean()
    non_numeric = team.select_dtypes(exclude=["number"])
    
    #put them back together
    return pd.concat([numeric, non_numeric], axis=1)

#only use rolling averages from that specific season
df_rolling = df_rolling.groupby(["team", "season"], group_keys=False).apply(find_team_averages)


# %%
df_rolling = df_rolling.drop(columns = ["team"])

#rename the rolling average columns for conca
rolling_cols = [f"{col}_10" for col in df_rolling.columns]
df_rolling.columns = rolling_cols

#update df
df = pd.concat([df, df_rolling], axis = 1)

# %%
#drop the rows with NA (first 10 games of season) 
df = df.dropna()

# %%
df["won_10"] = df["won_10"].astype(int)


# %%
#give model knowledge about next games 
def shift_col(team, col_name):
    #take next rows value and shift it back
    next_col = team[col_name].shift(-1)
    return next_col

def add_col(df, col_name): 
    #group by team, and send that team and column into the shift_col funciton
    return df.groupby("team", group_keys=False).apply(lambda x: shift_col(x, col_name))

#find if next game is home or not
df["home_next"] = add_col(df, "home")

#find teams next opponent
df["team_opp_next"] = add_col(df, "team_opp")

df["date_next"] = add_col (df, "date")

# %%
df = df.copy()

# %%
#df

# %%
#merge the current teams info, and the teams next opponents info together
#merge all the teams rolling columns, with their next opponent as well
full = df.merge(df[rolling_cols + ["team_opp_next", "date_next", "team"]], 
                left_on = ["team", "date_next"], 
                right_on = ["team_opp_next", "date_next"])




# %%
#full

# %%
full[["team_x","team_opp_next_x", "team_y", "team_opp_next_y", "date_next"]]

# %%

# %%
#columns we dont need
remove_cols = list(full.columns[full.dtypes == "object"]) + remove_cols

# %%
#everything except for the removed columns
selected_cols = full.columns[~full.columns.isin(remove_cols)]

# %%
#give the sfs the selected columns and use it to find the best stats to predict the target
sfs.fit(full[selected_cols], full["target"])

# %%
#which columns were selected
predictors = list(selected_cols[sfs.get_support()])

# %%
#predictors

# %%
predictions = backtest(full, rr, predictors)
#

# %%
from sklearn.metrics import accuracy_score
predictions = predictions[predictions["actual"] != 2]

# %%
#get accuracy after enhancing 
score = accuracy_score(predictions["actual"], predictions["prediction"])

print(predictions)

print("ACCURACY: ",score*100,"%")
