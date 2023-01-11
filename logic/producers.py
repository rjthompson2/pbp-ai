from logic.events import ScheduleEvent, RecordEvent

class RecordProducer:
    def produce(self, season_df):
        f = open("../data/events.txt")
        for season in season_df:
            f.write(RecordEvent(season["game_id"], season["gameday"], season["gametime"]))
        

class ScheduleProducer:
    def produce(self):
        f = open("../data/events.txt")
        event = ScheduleEvent()
        f.write(event)