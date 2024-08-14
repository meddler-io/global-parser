
import os
from time import sleep
import lib
import traceback
from bson import json_util
from asgiref.sync import sync_to_async
import os

is_prod = os.getenv("prod", None)

if not is_prod == None:
    subject = "activity-parse-prod"
else:
    subject = "activity-parse-dev"

print("environment", subject)

NATS_CONNECTION_STRING = os.getenv("NATS_CONNECTION_STRING")
        

import asyncio

import nats



async def main():
    nc = await nats.connect(NATS_CONNECTION_STRING)

    # Create JetStream context.
    js = nc.jetstream()





    await js.add_stream(name=subject, subjects=[ subject ])


    # Create single push based subscriber that is durable across restarts.
    sub = await js.subscribe(subject, durable=subject , manual_ack=True, ordered_consumer=True)
    while True:
        print("Waiting")
        try:
            msg = await sub.next_msg( timeout=10 )
            await msg.ack()
            print(" msg", msg)
            # sleep(20)
            


            await sync_to_async( lib.flushDb )()
            result  = json_util.loads(msg.data.decode())
            print(result)
            await sync_to_async( lib.core )(result)
            
            # await lib.core(result)
        except Exception as  er:
            # traceback.print_exc()
            print("Handled gracefully", er, subject, NATS_CONNECTION_STRING)
            

        

    # Create deliver group that will be have load balanced messages.


if __name__ == '__main__':
    asyncio.run(main())
