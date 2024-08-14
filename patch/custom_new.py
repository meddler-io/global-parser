import json
from django.db import models
from django.core.serializers import serialize
import asyncio
import datetime
import traceback
from bson import json_util
from django.db import transaction
from django.core.management import execute_from_command_line

from django.utils import timezone
import os
import dojo_patch
from dojo.tools import factory
from nats.aio.client import Client as NATS
import requests

from dojo.importers.default_importer import DefaultImporter as Importer
from dojo.importers.default_reimporter import DefaultReImporter as ReImporter
from dojo.models import Development_Environment, Finding, Test, Engagement, Product, Product_Type, User, Dojo_User, Test_Type

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure


class JobStatus():
    INITIALIZED = "initialized"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    UNKNOWN = "unknown"


def parse_message(sample_message):

    print(sample_message)
    db_config = sample_message["config"]
    data = sample_message["data"]

    print(
        db_config["host"],
        db_config["username"],
        db_config["password"],
    )

    mongo_client = MongoClient(

        db_config["host"],
        db_config["port"],

        username=db_config["username"],
        password=db_config["password"],
        authSource=db_config["database"],
        #    authMechanism='SCRAM-SHA-1',

    )

    mongo_client = mongo_client[db_config["database"]][db_config["collection"]]

    print("mongo_client", mongo_client)
    return mongo_client, data


def export_feeds_to_db():

    MONGO_HOST = "localhost:27017"
    client = MongoClient(MONGO_HOST,
                         # username=MONGO_USER,
                         # password=MONGO_PASSWORD,
                         # authSource=MONGO_AUTH_SOIRCE,
                         # authMechanism='SCRAM-SHA-1',
                         connect=True
                         )

    MONGO_DB = client["dummy_db"]
    MONGO_COLLECTION = MONGO_DB["fummy_collection"]

    MONGO_COLLECTION.insert_one({"hello": "world"})

    # Define message handler


def hit_webhook(endpoint, data={}):
    try:
        requests.post(endpoint, json = data).content
    except:
        traceback.print_exc()
        pass

# msg.data.decode


def core(msg):

    db_ref, task_msg = parse_message(msg)

    webhook_init, webhook_completed, webhook_failed = None, None, None

    try:

        webhooks = task_msg["webhooks"]
        if JobStatus.PROCESSING in webhooks:
            webhook_init = webhooks[JobStatus.PROCESSING]
        if JobStatus.COMPLETED in webhooks:
            webhook_completed = webhooks[JobStatus.COMPLETED]
        if JobStatus.FAILED in webhooks:
            webhook_failed = webhooks[JobStatus.FAILED]
    except:
        None

    print(webhook_init, webhook_completed, webhook_failed)

    hit_webhook(webhook_init)
    # return

    # return

    try:

        findings = singleton_task(task_msg)
        meta_data = task_msg["meta_data"]
        for finding in findings:
            finding.update(meta_data)
            db_ref.insert_one(finding)

        hit_webhook(webhook_completed)
    except:
        hit_webhook(webhook_failed)


def flushDb():
    execute_from_command_line(["", "flush", "--no-input"])


async def message_handler(msg , sub):


    await sub.unsubscribe()
    print("Subscription paused")

    try:
        flushDb()
        result  = json_util.loads(msg.data.decode())
        print(result)
        # core(result)
    except:
        # traceback.print_exc()
        # raise Exception("COnnection lost")
        pass
    
    await msg.ack()  # Acknowledge the message after processing
    print("Ackoeledged")

    # print(        f"Received a message on '{msg.subject}': {msg.data.decode()}")


async def main():
    # Initialize NATS client
    nc = NATS()

    try:
        NATS_CONNECTION_STRING = os.getenv("NATS_CONNECTION_STRING")
        print("NAtS_CONNECTION_STRING", NATS_CONNECTION_STRING)
        # Connect to NATS server
        await nc.connect(NATS_CONNECTION_STRING)

        print("Connnected")

        # Subscribe to the "activity-parse" subject with a durable name

        js = nc.jetstream()

        # Persist messages on 'foo's subject.
        await js.add_stream(name="activity-parse", subjects=["activity-parse"])
        
        
        async def subscribe():
            global sub
            sub = await js.subscribe(
                "activity-parse",
                durable="activity-parse",
                cb=wrapped_message_handler,
                # ack_wait=7200 , # Setting to 2 hours as an example
                manual_ack=True  # Settin
                
            )
            print("Subscription resumed")
            
        # Create a subscription with a message handler that pauses after receiving a message
        async def wrapped_message_handler(msg):
            global sub
            await message_handler(msg, sub)
            
            # Resubscribe to continue receiving messages after the current one is processed
            print("subscribing")
            await subscribe()
            print("subscribe")
        

        # Start the initial subscription
        await subscribe()


        # Keep the event loop running
        while True:
            await asyncio.sleep(1)

    except Exception as e:
        print(f"Error in main loop: {e}")
    finally:
        # Clean up resources
        await nc.close()


sample_message = {
    "config": {
        "action": "updated",
        "auth_source": None,
        "collection": "activity_findings",
        "database": "meddler_app_661d5b5ce847a315c2b3b04d",
        "host": "192.168.29.194",
        "password": "test",
        "port": 27017,
        "username": "test"
    },
    "data": {
        "_id": {
            "$oid": "6668a2ef4dee1cad43d752fa"
        },
        "config": [
            {
                "collection": "_test_collection",
                "database": "meddler_app_661d5b5ce847a315c2b3b04d"
            }
        ],
        "engagement_id": {
            "$oid": "6660dd153bb6b047bc26fc25"
        },
        "files": [
            {
                "filename": "TimesPrime_Polling_Service.xml",
                "url": "/minio-vapt/6668a264c1db33d797e144f0?response-content-disposition=attachment%3B%20filename%3DTimesPrime_Polling_Service.xml&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=uaaGAF0jnXVHa7KV5eOa%2F20240612%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20240612T123654Z&X-Amz-Expires=604800&X-Amz-SignedHeaders=host&X-Amz-Signature=e8ec6bd6c27ad11a1485409970315fa83953f324f1a35ce969766a96624a7d1e"
            }
        ],
        "meta_data": {
            "activity_id": {
                "$oid": "6668a2ef4dee1cad43d752fa"
            },
            "enagement_id": {
                "$oid": "6660dd153bb6b047bc26fc25"
            },
            "tags": [
                "hello"
            ]
        },
        "parser": {
            "id": "Checkmarx Scan detailed",
            "type": "dojo"
        },
        "tags": [
            "hello"
        ]
    },
    "status": True
}


def serialize_model(model_instance):
    # Get all field names of the model
    fields = [field.name for field in model_instance._meta.get_fields()]

    # Exclude fields that are foreign keys
    exclude_fields = [field.name for field in model_instance._meta.get_fields(
    ) if isinstance(field, models.ForeignKey)]

    # Determine fields to include
    include_fields = [field for field in fields if field not in exclude_fields]

    # Serialize the model instance to JSON, including only the determined fields
    json_data = serialize('json', [model_instance], fields=include_fields)

    return json_data

    # Run the event loop
    # asyncio.run(main())


def singleton_task(message):

    parser_id = message["parser"]["id"]
    report_files = message["files"]

    parser_ref = factory.PARSERS[parser_id]

    # Curently Only handling one file. Can be extended
    for file in report_files[:1]:
        print("__filefile__")
        INPUT_PATH = os.path.join(dojo_patch.INPUT_DIRECTORY, file["filename"])
        OUTPUT_PATH = os.path.join(
            dojo_patch.OUTPUT_DIRECTORY, file["filename"])

        download_url = "https://s3.meddler.io" + file["url"]

        response = requests.get(download_url, stream=True)
        with open(INPUT_PATH, "wb") as _file:
            for chunk in response.iter_content(chunk_size=1024):
                _file.write(chunk)

        print("file_content")
        # print(open(INPUT_PATH).readlines())

        print("INPUT_PATH", INPUT_PATH)
        print("OUTPUT_PATH", OUTPUT_PATH)

        print(parser_ref.get_findings)

        # _test = Test(   engagement = Engagement("test", product=Product("")) ,   test_type= Test_Type(  name="test") )
        # _test.save()

        # dojo_patch.parseReport(parser_id , None , dojo_patch.OUTPUT_PATH , INPUT_PATH, {})

        # print_function_names(parser_ref)

        FINDINGS = None

        try:
            with transaction.atomic():
                scan_type = parser_id
                user, _ = User.objects.get_or_create(username="meddler")
                product_type, _ = Product_Type.objects.get_or_create(
                    name=parser_id)
                print("product_type", product_type, _)
                environment, _ = Development_Environment.objects.get_or_create(
                    name="Development")
                print("environment", environment, _)

                product, _ = Product.objects.get_or_create(
                    name=parser_id,
                    prod_type=product_type,
                )

                engagement, _ = Engagement.objects.get_or_create(
                    name=parser_id,
                    product=product,
                    target_start=timezone.now(),
                    target_end=timezone.now(),
                )

                engagement.save()
                print("engagement", engagement, _)

                import_options = {
                    "user": user,
                    "lead": user,
                    "scan_date": None,
                    "environment": environment,
                    "active": True,
                    "verified": False,
                    "engagement": engagement,
                    "scan_type": scan_type,
                }
                importer = Importer(**import_options)
                print("importer", importer)

                with open(INPUT_PATH,  "rb") as scan:
                    # print("scan", scan)
                    lead = None
                    scan_date = timezone.make_aware(
                        datetime.datetime.now(), timezone.get_default_timezone())

                    test, _, len_new_findings, len_closed_findings, _, _, _ = importer.process_scan(
                        scan)

                    message = f' Current: {parser_id} processed a total of {len_new_findings} findings' + \
                        ' and closed %d findings' % (len_closed_findings)
                    print(message)

                findings = Finding.objects.filter(test=test).order_by('id')

                FINDINGS = dojo_patch.csv_export(findings, {})

                # matchCriteria = json_util.loads(json_util.dumps(extra_attributes))

                # print("FINDINGS", FINDINGS)

            # findings = parser_ref.get_findings( open(INPUT_PATH)  , _test  )

        except Exception as e:
            # traceback.print_exc()
            # Handle the IntegrityError here
            print(f"An error occurred: {e}")

        return FINDINGS


test_message = {
    "config": {
        "action": "updated",
        "auth_source": "meddler_app_661d5b5ce847a315c2b3b04d",
        "collection": "activity_findings",
        "database": "meddler_app_661d5b5ce847a315c2b3b04d",
        "host": "192.168.29.194",
        "password": "test",
        "port": 27017,
        "username": "test"
    },
    "data": {
        "_id": {
            "$oid": "6668a2ef4dee1cad43d752fa"
        },
        "config": [
            {
                "collection": "_test_collection",
                "database": "meddler_app_661d5b5ce847a315c2b3b04d"
            }
        ],
        "engagement_id": {
            "$oid": "6660dd153bb6b047bc26fc25"
        },
        "files": [
            {
                "filename": "TimesPrime_Polling_Service.xml",
                "url": "/minio-vapt/6668a264c1db33d797e144f0?response-content-disposition=attachment%3B%20filename%3DTimesPrime_Polling_Service.xml&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=uaaGAF0jnXVHa7KV5eOa%2F20240612%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20240612T125120Z&X-Amz-Expires=604800&X-Amz-SignedHeaders=host&X-Amz-Signature=38acda49eb2d0c89444886d45700fa8e3ea1a996384d5ec2dce47490bc39ec71"
            }
        ],
        "meta_data": {
            "activity_id": {
                "$oid": "6668a2ef4dee1cad43d752fa"
            },
            "engagement_id": {
                "$oid": "6660dd153bb6b047bc26fc25"
            },
            "job_id": {
                "$oid": "666999c8db5bebeff39a58c5"
            },
            "tags": [
                "hello"
            ]
        },
        "parser": {
            "id": "Checkmarx Scan detailed",
            "type": "dojo"
        },
        "tags": [
            "hello"
        ]
    },
    "status": True
}


if __name__ == '__main__':
    # entry()

    # export_feeds_to_db()

    # Prod
    asyncio.run(main())

    # Testing
    # msg = json_util.loads( json.dumps( test_message) )
    # core(msg)
