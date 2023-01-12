import nfl_data_py as nfl
from producers import RecordEvent, ScheduleEvent

class Consumer:
    def consume(self, event):
        pass

class ScheduleConsumer(Consumer):
    def consume(self, event):
        season_df = nfl.import_schedules([2021])
        season_df = season_df.loc[season_df["gameday"] == event.date]
        season_df = season_df[["game_id", "gameday", "gametime"]]
        return season_df

class RecordConsumer(Consumer):
    def consume(self, event):
        #TODO logic
        return