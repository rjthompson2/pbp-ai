# import nfl_data_py as nfl
# season_df = nfl.import_schedules([2022])
# print(season_df)
# season = season_df.loc[season_df["gameday"] > "2023-01-10"]
# season = season[["game_id", "gameday", "gametime"]]
# print(season)
# print(season_df.columns)

class Event:
    status = "Incomplete"
    data:str
    def __init__(self, data):
        self.data = data

    def to_txt(self):
        return self.__class__.__name__ + " " + str(vars(self))

event = Event("test")
print(event.to_txt())
event.status = "Complete"
print(event.to_txt())