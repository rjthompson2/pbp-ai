import nfl_data_py as nfl
from producers import RecordEvent, ScheduleEvent

class ScheduleConsumer:
    def consume(self, schedule_event):
        season_df = nfl.import_schedules([2021])
        season_df = season_df.loc[season_df["gameday"] == schedule_event.date]
        season_df = season_df[["game_id", "gameday", "gametime"]]
        return season_df

class RecordConsumer:
    def consume(self, record_event):
        #TODO logic
        return