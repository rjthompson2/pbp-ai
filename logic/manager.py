from producers import *
from consumers import *
from brokers import *

def main():
    producer = ScheduleProducer()
    events = producer.produce()
    broker = Broker()
    df = broker.listen(events, ScheduleConsumer())

    if df.empty:
        print("Empty")
        return
    producer = RecordProducer()
    events = producer.produce(df)
    broker = Broker()
    df = broker.listen(events, RecordConsumer())

if __name__:
    main()