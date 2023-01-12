
import asyncio
from consumers import Consumer
from events import RecordEvent

class Broker:
    async def listen(self, event, consumer):
        #TODO get event somehow
        loop = asyncio.get_event_loop()
        future = asyncio.Future()
        asyncio.ensure_future(consumer.consume(event), future)
        try:
            loop.run_until_complete(future)
            print(future.result())
        finally:
            loop.close()