class ScheduleBroker:
    def check(self):
        f = open("data/events.txt")
        for event in f:
            print(event)

sb = ScheduleBroker()
sb.check()