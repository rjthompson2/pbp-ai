# import asyncio
# from producers import RecordProducer

# loop = asyncio.get_event_loop()
# loop.run_until_complete(RecordProducer())
# loop.close()

# import nfl_data_py as nfl
# import datetime

# season_df = nfl.import_schedules([2021])
# season_df = season_df.loc[season_df["gameday"] <= str(datetime.date.today())]
# season_df = season_df[["game_id", "gameday", "gametime"]]
# print(season_df)

#RecordEvent("game_name", "2022-01-23", "18:30")

from brokers import Broker
from events import ScheduleEvent
from consumers import ScheduleConsumer
broker = Broker()
broker.listen(event=ScheduleEvent(), consumer=ScheduleConsumer())