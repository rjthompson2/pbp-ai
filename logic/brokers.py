import asyncio
from consumers import Consumer
from events import RecordEvent

class Broker:
    def listen(self, events, consumer):
        loop = asyncio.get_event_loop()
        for event in events:
            task = loop.create_task(consumer.consume(event))
        loop.run_until_complete(task)
        return task.result()