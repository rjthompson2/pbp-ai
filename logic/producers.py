class RecordProducer:
    def produce(self, season_df):
        events = []
        for season in season_df:
            events += [RecordEvent(season["game_id"], season["gameday"], season["gametime"])]
        #TODO add events to the event txt file