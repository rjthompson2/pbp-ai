from logic.events import Event, RecordEvent, ScheduleEvent

class TestEvents:
    def test_event(self):
        event = Event()
        assert event != None
        assert event.status == "Incomplete"
        assert event.to_txt() != None or event.to_txt() != ""

    def test_record_event(self):
        event = RecordEvent("game_name", "date", "time")
        assert event != None
        assert event.status == "Incomplete"
        assert event.to_txt() != None or event.to_txt() != ""

    def test_schedule_event(self):
        event = ScheduleEvent()
        assert event != None
        assert event.status == "Incomplete"
        assert event.date != None
        assert event.to_txt() != None or event.to_txt() != ""
