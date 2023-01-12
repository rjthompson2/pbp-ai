from events import ScheduleEvent, RecordEvent
import asyncio

class RecordProducer:
    async def produce(self, season_df):
        for season in season_df:
            yield RecordEvent(season["game_id"], season["gameday"], season["gametime"])
        

class ScheduleProducer:
    async def produce(self):
        yield ScheduleEvent()