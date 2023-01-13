from events import ScheduleEvent, RecordEvent
import asyncio

class RecordProducer:
    def produce(self, season_df):
        yield (RecordEvent(season["game_id"], season["gameday"], season["gametime"]) for season in season_df)
        

class ScheduleProducer:
    def produce(self):
        yield ScheduleEvent()