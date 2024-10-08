import json
from django.db import models
from django.core.serializers import serialize
import asyncio
import datetime
import traceback
from bson import json_util
from django.db import transaction
from asgiref.sync import sync_to_async

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

# Output report writer
import csv
import os
from bson import json_util


import os
import argparse
import sys

def get_config():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Get config from arguments or environment variables.')
    
    # Define possible arguments
    parser.add_argument('--parser_id', type=str, help='Parser ID')
    parser.add_argument('--report_file', type=str, help='Path to the report file')
    parser.add_argument('--result_file', type=str, help='Path to the result file')

    
    
    # New argument to list supported parsers
    parser.add_argument('--info', nargs='?', const=True, type=str, help='Enlist all supported parsers')



    # Parse the arguments
    args = parser.parse_args()
    
    info_parsers = args.info 
    if info_parsers:
        
        dojo_patch.listParsers()
        sys.exit(0)

    # Fetch values from arguments or environment variables
    parser_id = args.parser_id or os.environ.get("parser_id")
    report_file = args.report_file or os.environ.get("parser._file")
    result_file = args.result_file or os.environ.get("parser_result")
    
    print( parser_id, report_file , result_file )
    print("+++++")

    # Check if all required values are present
    if not parser_id:
        print("parser_id is missing. Provide it either as an argument or set the 'parser_id' environment variable.")
        sys.exit(1)
    
    if not report_file:
        print("report_file is missing. Provide it either as an argument or set the 'parser_file' environment variable.")
        sys.exit(1)
    
    
    if not result_file:
        print("result_file is missing. Provide it either as an argument or set the 'parser_result' environment variable.")
        sys.exit(1)
    
    
    
    # Check if report_file exists
    if not os.path.isfile(report_file):
        print(f"The report file '{report_file}' does not exist. Please provide a valid path.")
        sys.exit(1)
        
    
    return parser_id, report_file, result_file


def flatten_dict(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def save_objects_to_file(objects, filename):
    ext = os.path.splitext(filename)[1].lower()

    if ext == '.csv':
        with open(filename, mode='w', newline='') as file:
            if len(objects) > 0:
                flat_objects = [flatten_dict(obj) for obj in objects]
                fieldnames = set()
                for obj in flat_objects:
                    fieldnames.update(obj.keys())
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(flat_objects)

    elif ext == '.json':
        with open(filename, mode='w') as file:
            file.write(json_util.dumps(objects, indent=4))

    elif ext == '.jsonl':
        with open(filename, mode='w') as file:
            for obj in objects:
                file.write(json_util.dumps(obj) + '\n')

    else:
        raise ValueError("Unsupported file extension: {}".format(ext))


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


def core(parser_id, report_file, result_file):

    # db_ref, task_msg = parse_message(msg)    
    findings = singleton_task(parser_id, report_file)
    save_objects_to_file(findings, result_file)
    


def flushDb():
    execute_from_command_line (["", "flush", "--no-input"] )
    # execute_from_command_line(["", "flush", "--no-input"])


def message_handler(parser_id, report_file, result_file):
    
    flushDb()
    core(parser_id, report_file, result_file)

def getDbSize(arg):
    db_path = os.environ.get("DD_DATABASE_NAME")
    file_size = os.path.getsize(db_path)
    file_size_mb = file_size / (1024 * 1024)  # Convert to MB
    print("db_size", arg,  file_size_mb , "MB", db_path)
    

def main(parser_id, report_file, result_file):
    message_handler(parser_id, report_file, result_file)




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


def singleton_task(parser_id, report_file):


    
    


    if parser_id not in factory.PARSERS:
        print("Invalid parser_id. No supported parsers found. Use --info to checko out the list of supported parsers.")
        sys.exit(1)



    FINDINGS = []

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

            with open(report_file,  "rb") as scan:
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
        pass


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




from django.core.management import execute_from_command_line
if __name__ == '__main__':
    
    parser_id, report_file, result_file = get_config()
    
    main(parser_id, report_file, result_file)
    flushDb()
