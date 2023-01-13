import asyncio
import nfl_data_py as nfl
from producers import RecordEvent, ScheduleEvent

class Consumer:
    async def consume(self, event):
        pass

class ScheduleConsumer(Consumer):
    async def consume(self, event):
        season_df = nfl.import_schedules([2022])
        season_df = season_df.loc[season_df["gameday"] == str(event.date)]
        # season_df = season_df.loc[season_df["gameday"] >= str(event.date)]
        season_df = season_df[["game_id", "gameday", "gametime"]]
        return season_df

class RecordConsumer(Consumer):
    async def consume(self, event):
        #TODO logic
        print("TBD")
        return