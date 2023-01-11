import datetime

class Event:
    status = "Incomplete"
    def to_txt(self):
        return self.__class__.__name__ + " " + str(vars(self)) + "\n"

class ScheduleEvent(Event):
    date:str
    def __init__(self):
        self.date = datetime.date.today()

class RecordEvent(Event):
    game_name:str
    date:str
    time:str
    def __init__(self, game_name, date, time):
        self.game_name = game_name
        self.date = date
        self.time = time