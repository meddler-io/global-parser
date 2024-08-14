
import django

FORCE_LOAD_INIT = True
from django.db import transaction

print("django.setup()")

def setEnv(key, val):
    val = str(val)
    os.environ[key] = val
    
    print("set env", key, val, os.getenv(key))
    return val


if __name__ == "__main__" or FORCE_LOAD_INIT:
    django.setup()

from django.core.management import execute_from_command_line
from dojo.models import Finding, Test, Engagement, Product, Product_Type, User, Development_Environment
from dojo import reports
from dojo import decorators
from django.forms.models import model_to_dict
from dojo.tools import factory
from django.utils import timezone
from dojo.importers.default_importer import DefaultImporter as Importer
from dojo.importers.default_reimporter import DefaultReImporter as ReImporter
# from dojo.importers.default_importer import DojoDefaultImporter as ReImporter
from typing import Dict, List
import zipfile
import os
import shutil
import json
import traceback
import datetime
from pathlib import Path
import requests
from bson import json_util
from urllib.parse import urlparse
import copy
from db import DB_NAME, BulkInsert, UpdateStatus, BulkFind, setDb
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string

DEFAULT_DB = DB_NAME


class TransitionState():
    FAILED = 0
    ENQUEUED = 1  # On Insertion in DB
    EXECUTION_ENQUEUED = 2  # Send to Tool Execiutor
    EXECUTION_STARTED = 3
    EXECUTION_FINISHED = 4
    EXECUTION_REPORT_DOWNLOADED = 5
    PARSING_ENQUEUED = 6
    PARSING_STARTED = 7
    PARSING_FINISHED = 8


# Patching decorator: we_want_async to ignore celery/async tasks and forcefully run in foreground
def we_want_to_force_sync(*args, func=None, **kwargs):
    return False


if __name__ == "__main__" or FORCE_LOAD_INIT:
    decorators.we_want_async = we_want_to_force_sync






def initGlobalVariables(config: dict):
    print("config", config.keys())
    global INPUT_FILENAME, INPUT_TOOLNAME, PREV_INPUT_FILENAME, OUTPUT_FILENAME, OUTPUT_FILEFORMAT
    INPUT_FILENAME = config.get("INPUT_FILENAME", INPUT_FILENAME)
    INPUT_TOOLNAME = Path(config.get("INPUT_FILENAME", INPUT_FILENAME)).stem
    INPUT_FILENAME = "current_" + INPUT_FILENAME
    PREV_INPUT_FILENAME = config.get(
        "PREV_INPUT_FILENAME", PREV_INPUT_FILENAME)
    PREV_INPUT_FILENAME = "previous_" + PREV_INPUT_FILENAME

    OUTPUT_FILENAME = config.get("OUTPUT_FILENAME", OUTPUT_FILENAME)
    OUTPUT_FILEFORMAT = config.get("OUTPUT_FILEFORMAT", OUTPUT_FILEFORMAT)

    global INPUT_PATH, PREV_INPUT_PATH, OUTPUT_PATH
    INPUT_PATH = os.path.join(INPUT_DIRECTORY, INPUT_FILENAME)
    PREV_INPUT_PATH = os.path.join(PREV_INPUT_DIRECTORY, PREV_INPUT_FILENAME)
    OUTPUT_PATH = os.path.join(OUTPUT_DIRECTORY, OUTPUT_FILENAME)

    print("INPUT_FILENAME", INPUT_FILENAME)
    print("PREV_INPUT_FILENAME", PREV_INPUT_FILENAME)
    print("OUTPUT_FILENAME", OUTPUT_FILENAME)
    print("OUTPUT_FILEFORMAT", OUTPUT_FILEFORMAT)
    print("INPUT_PATH", INPUT_PATH)
    print("PREV_INPUT_PATH", PREV_INPUT_PATH)

    global BUNDLE_PARSER
    BUNDLE_PARSER = config.get("BUNDLE_PARSER", True)
    print("BUNDLE_PARSER", BUNDLE_PARSER)


def flushDb():
    execute_from_command_line(["", "flush", "--no-input"])


if __name__ == "__main__" or FORCE_LOAD_INIT:
    # execute_from_command_line(["", "makemigrations", "dojo"])
    # execute_from_command_line(["", "migrate"])
    
    setEnv("DJANGO_SETTINGS_MODULE", "dojo.settings.settings")

    from django.core.management import execute_from_command_line
    
    flushDb()


def cleanFs(dir):
    print("dir" , dir)
    return
    for f in os.listdir(dir):
        path = os.path.join(dir, f)
        try:
            shutil.rmtree(path)
        except OSError:
            os.remove(path)


def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            print("Zipping", file)
            ziph.write(os.path.join(root, file),
                       file,
                       #    os.path.join(path, '..'))
                       )


def to_json(findings: List, extra_attributes: dict):
    result = []

    if len(findings) > 0:
        keys = findings[0]

    for _finding in findings[1:]:
        __finding = copy.deepcopy(extra_attributes)
        for k, v in zip(keys, _finding):
            __finding[k] = v
        __finding = json_util.loads(json_util.dumps(
            __finding,   sort_keys=True, default=str))
        result.append(__finding)

    return result


def csv_export(findings, extra_attributes: dict):
    print("csv_export()")
    FINDINGS = []
    first_row = True
    

    for finding in findings:
        if first_row:
            fields = []
            for key in dir(finding):
                if key not in get_excludes() and not callable(getattr(finding, key)) and not key.startswith('_'):
                    fields.append(key)
            fields.append('test')
            fields.append('found_by')
            fields.append('engagement_id')
            fields.append('engagement')
            fields.append('product_id')
            fields.append('product')
            fields.append('endpoints')

            FINDINGS.append(fields)
            first_row = False
        if not first_row:
            fields = []
            for key in dir(finding):
                if key not in get_excludes() and not callable(getattr(finding, key)) and not key.startswith('_'):
                    value = finding.__dict__.get(key)
                    if key in get_foreign_keys() and getattr(finding, key):
                        value = str(getattr(finding, key))
                    if value and isinstance(value, str):
                        # value = value.replace('\n', ' NEWLINE ').replace('\r', '')
                        value = value.split('\n')
                        value = [v.replace('"\r', '') for v in value]
                        value = list(filter(lambda x: x != '', value))
                        # for _v in value:
                        # _v  =   _v.replace('\r', '')
                        if len(value) == 1:
                            value = value[0]

                    fields.append(value)
            fields.append(finding.test.title)
            fields.append(finding.test.test_type.name)
            fields.append(finding.test.engagement.id)
            fields.append(finding.test.engagement.name)
            fields.append(finding.test.engagement.product.id)
            fields.append(finding.test.engagement.product.name)

            endpoint_value = []
            num_endpoints = 0
            for endpoint in finding.endpoints.all():
                endpoint_value.append(str(endpoint))

            fields.append(endpoint_value)
            FINDINGS.append(fields)

    FINDINGS = to_json(FINDINGS, extra_attributes)
    return FINDINGS


def get_foreign_keys():
    return reports.views.get_foreign_keys()


def get_excludes():
    return reports.views.get_excludes()


def sanity_checks():
    if not os.path.exists(INPUT_PATH):
        raise Exception("No such file found")


def enlistToolParser():
    return factory.PARSERS.keys()

def getAllToolParser():
    return factory.PARSERS.items()


def inject_custom_fields(finding: dict,  key, value):
    finding[key] = value


def parseReport( TOOL_PARSER, previous_input_file, output_file, current_input_file, extra_attributes):
    print("parseReport()", TOOL_PARSER)
    

    operation_type = "scan"

    if (TOOL_PARSER.lower().startswith("hawki_domain") ) or (TOOL_PARSER.lower().startswith("hawki domain") ) or (TOOL_PARSER.lower() == "domains" ) :
        operation_type = "recon"
        TOOL_PARSER = "Hawki Subdomain Recon"

    extra_attributes["operation_type"] = operation_type
    
    
    # Disable foreign key checks

    if not TOOL_PARSER in factory.PARSERS:
        _TOOL_PARSER = Path(INPUT_FILENAME).stem
        if _TOOL_PARSER in factory.PARSERS:
            TOOL_PARSER = _TOOL_PARSER
        else:
            # Put parser for domain data
            raise Exception("No such tool found", TOOL_PARSER)

    parser_id = TOOL_PARSER
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
    

    target_start = timezone.now()
    target_end = timezone.now()

    engagement, created = Engagement.objects.get_or_create(
        name=TOOL_PARSER,
        product=product,
        target_start=target_start,
        target_end=target_end
    )
    if created:
        engagement.save()

    lead = None
    scan_type = TOOL_PARSER
    # environment = Development_Environment
    environment, _ = Development_Environment.objects.get_or_create(
        name="Development")
    
    
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

    importer = Importer( **import_options   )

    # reimporter = ReImporter(engagement=engagement, environment=environment
    #                     ,scan_type=scan_type
    #                     )
    
    reimporter  = None
    scan_date = timezone.make_aware(datetime.datetime(
        2021, 9, 1), timezone.get_default_timezone())


    FINDINGS = []
        
    try:


        with open(current_input_file) as scan:            
            test, _, len_new_findings, len_closed_findings, _, _, _  = importer.process_scan(scan)

            message = f'{TOOL_PARSER} processed a total of {len_new_findings} findings' + \
                ' and closed %d findings' % (len_closed_findings)
            print(message)
            
            findings = Finding.objects.filter(test=test).order_by('id')
            FINDINGS = csv_export(findings, {})

            
    except Exception as err:
        traceback.print_exc()
        print("Current scan import report invalid", current_input_file, err)




    return FINDINGS
    
    return

    findings = Finding.objects.filter(test=test).order_by('id')
    FINDINGS = csv_export(findings, extra_attributes)
    matchCriteria = json_util.loads(json_util.dumps(extra_attributes))
    print("matchCriteria", matchCriteria)
    BulkInsert( FINDINGS, matchCriteria)

    print("OUTPUT_FILEFORMAT", OUTPUT_FILEFORMAT)
    if OUTPUT_FILEFORMAT == 'json':
        with open(output_file, "w") as f:
            json.dump(FINDINGS, f, indent=4, sort_keys=True, default=str)
    elif OUTPUT_FILEFORMAT == 'jsonl':
        with open(output_file, "w") as f:
            for finding in FINDINGS:
                f.write(json.dumps(finding,   sort_keys=True, default=str))
                if not FINDINGS[-1] == finding:
                    f.write("\n")

    return findings


def parsingJob( extra_attributes: dict):
    flushDb()
    
    global BUNDLE_PARSER
    print('parsingJob', BUNDLE_PARSER, extra_attributes)
    print('parsingJob', extra_attributes)

    cleanFs(PROCESS_DIRECTORY)
    cleanFs(OUTPUT_DIRECTORY)
    TOOL_PARSER = os.getenv("TOOL_PARSER")
    NO_ERROR = True
    TOOL_REPORTER = {

    }
    FINDINGS = list()
    # print(tool)
    if BUNDLE_PARSER:
        print('TOOL_PARSER BUNDLE', TOOL_PARSER,
              OUTPUT_PATH, INPUT_PATH, extra_attributes)

        print("Extracting", PREV_INPUT_PATH)

        PROCESS_PREVIOUS_PATH = os.path.join(PROCESS_DIRECTORY, "previous")
        PROCESS_CURRENT_PATH = os.path.join(PROCESS_DIRECTORY, "current")
        PROCESS_DIRECTORY_ZIP_OUTPUT = os.path.join(
            PROCESS_DIRECTORY, "zipoutput")

        Path(PROCESS_PREVIOUS_PATH).mkdir(parents=True, exist_ok=True)
        Path(PROCESS_CURRENT_PATH).mkdir(parents=True, exist_ok=True)
        Path(PROCESS_DIRECTORY_ZIP_OUTPUT).mkdir(parents=True, exist_ok=True)

        try:
            with zipfile.ZipFile(PREV_INPUT_PATH, 'r') as zip_ref:
                print("Extracting Previous", PROCESS_PREVIOUS_PATH)
                zip_ref.extractall(PROCESS_PREVIOUS_PATH)

        except:
            print("Failed to unzip", PREV_INPUT_PATH)

        try:
            with zipfile.ZipFile(INPUT_PATH, 'r') as zip_ref:
                print("Extracting Current", PROCESS_CURRENT_PATH)
                zip_ref.extractall(PROCESS_CURRENT_PATH)
        except:
            print("Failed to unzip", PREV_INPUT_PATH)

        unzipped_files = os.listdir(PROCESS_CURRENT_PATH)
        for unzipped_file in unzipped_files:
            unzipped_file_path = os.path.join(
                PROCESS_CURRENT_PATH, unzipped_file)
            _file_path = Path(unzipped_file_path)
            FILENAME = _file_path.stem
            FILEEXTENSION = _file_path.suffix
            FILEPATH = unzipped_file_path
            TOOL_PARSER = FILENAME
            if os.path.isfile(unzipped_file_path):

                PREVIOUS_FILEPATH = os.path.join(
                    PROCESS_PREVIOUS_PATH, _file_path.name)

                ZIP_ITEM_OUTPUT_PATH = os.path.join(
                    PROCESS_DIRECTORY_ZIP_OUTPUT, TOOL_PARSER + ".json")

                print('TOOL_PARSER', TOOL_PARSER, PREVIOUS_FILEPATH,
                      ZIP_ITEM_OUTPUT_PATH, FILEPATH)
                try:
                    findings = parseReport(
                        TOOL_PARSER, PREVIOUS_FILEPATH, ZIP_ITEM_OUTPUT_PATH, FILEPATH, extra_attributes)
                    FINDINGS += findings
                    TOOL_REPORTER[TOOL_PARSER] = True
                except:
                    traceback.print_exc()
                    try:
                        TOOL_REPORTER[TOOL_PARSER] = False

                    except:
                        pass

                    NO_ERROR = False

            flushDb()

        zipf = zipfile.ZipFile(OUTPUT_PATH, 'w', zipfile.ZIP_DEFLATED)
        zipdir(PROCESS_DIRECTORY_ZIP_OUTPUT, zipf)
        zipf.close()

        # parseReport(TOOL_PARSER, INPUT_PATH, OUTPUT_PATH, FILEPATH)
        pass
    else:
        RE_INPUT_PATH = os.path.join(INPUT_DIRECTORY, 're' + INPUT_FILENAME)
        TOOL_PARSER = INPUT_TOOLNAME
        print('TOOL_PARSER SCAN', TOOL_PARSER, INPUT_TOOLNAME,
              RE_INPUT_PATH, OUTPUT_PATH, INPUT_PATH, extra_attributes)
        try:
            findings = parseReport(
                TOOL_PARSER, RE_INPUT_PATH, OUTPUT_PATH, INPUT_PATH, extra_attributes)
            FINDINGS += findings
            TOOL_REPORTER[TOOL_PARSER] = True

        except:
            TOOL_REPORTER[TOOL_PARSER] = False
            NO_ERROR = False

    flushDb()
    cleanFs(PROCESS_DIRECTORY)

    return NO_ERROR, TOOL_REPORTER, FINDINGS

    if not NO_ERROR:
        raise Exception("Parsing all tools not finished successfully")


# https://hawki.indiatimes.com/minio/devsecops/5e0dbac209caf2fedfd310f6/5e26b9d7557f3d8c94e426ef/5e0dd2a6ae21f272971db085/6126098d72e6fcac53c2085d/158_reportpack.zip?response-content-disposition=attachment%3B%20filename%3D158_reportpack.zip&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAIOSFODNN7MINIO%2F20211105%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20211105T182449Z&X-Amz-Expires=604800&X-Amz-SignedHeaders=host&X-Amz-Signature=4d48cda16be3e987f26bc8fe20d81fac30ec864bffddd8224a35ccd48100ba3a
def syncIn(currentBuildUrl: str,  previousBuildUrl: str = None):
    global INPUT_PATH, PREV_INPUT_PATH

    if currentBuildUrl:
        print("Downloading currentBuildUrl",  currentBuildUrl, ">", INPUT_PATH)
        response = requests.get(currentBuildUrl, stream=True)
        _file = open(INPUT_PATH, "wb")
        for chunk in response.iter_content(chunk_size=1024):
            _file.write(chunk)

    if previousBuildUrl:
        print("Downloading previousBuildUrl",
              previousBuildUrl, ">", PREV_INPUT_PATH)
        response = requests.get(previousBuildUrl, stream=True)
        _file = open(PREV_INPUT_PATH, "wb")
        for chunk in response.iter_content(chunk_size=1024):
            _file.write(chunk)

    pass


def syncOut():
    pass

def entryPoint(message: str):
    print("entrypoint", message)
    message: dict = json.loads(message)

    action: dict = message.get("action",  {
        "updateDb": True,
        "operation": "CREATE_NEW",
        "filter": "ALL",
        "upload": True,
        "upload_url": "",
        "db_name": DEFAULT_DB,
        
    })
    dbName = action.get("db_name", DEFAULT_DB)
    setDb(dbName)
    updateDb = action.get("updateDb", True)
    operation = action.get("operation", "operation")
    filter = action.get("filter", "ALL")
    upload = action.get("upload", True)
    upload_report = action.get("upload_report", True)
    upload_url = action.get("upload_url", "")
    upload_report_url = action.get("upload_report_url", "")
    parser_type = action.get("parser_type", "bundle").lower()
    extra_attributes = action.get("extra_attributes", {})

    if not parser_type in ["bundle", "scan"]:
        parser_type = "bundle"

    data = message.get("data", {"previous": None, "current": None})
    previous_build = data.get("previous", {"_id": {"$oid": "",
                                                   "file":
                                                   {

                                                       "name": ""
                                                   },

                                                   "download_url": None

                                                   }})
    current_build = data.get("current", {"_id": {"$oid": "",
                                                 "file":
                                                 {

                                                     "name": ""
                                                 },

                                                 "download_url": None

                                                 }})

    extra_attributes["buildId"] = current_build.get("_id")
    extra_attributes["platformId"] = current_build.get("platformId")
    extra_attributes["applicationId"] = current_build.get("applicationId")
    extra_attributes["businessId"] = current_build.get("businessId")

    _filter_status = json_util.loads(json_util.dumps({
        "_id": current_build.get("_id"),
        "platformId": current_build.get("platformId"),
        "applicationId": current_build.get("applicationId"),
        "businessId": current_build.get("businessId"),
    }))

    _filter_update = json_util.loads(json_util.dumps(
        {"$set":
         {
             "state_parsing_started": True,
             "state_parsing_started_ts": datetime.datetime.utcnow(),
             "transition_state": TransitionState.PARSING_STARTED
         }
         }
    ))

    _filter_failed_update = json_util.loads(json_util.dumps(
        {"$set":
         {
             "state_parsing_completed": False,
             "state_parsing_started_ts": datetime.datetime.utcnow(),
             "transition_state": TransitionState.FAILED
         }
         }
    ))

    UpdateStatus( _filter_status, _filter_update)

    try:
        # print("updateDb", updateDb)
        # print("operation", operation)
        # print("filter", filter)
        # print("upload", upload)
        # print("upload_url", upload_url)
        # print("previous_build", previous_build)
        # print("current_build", current_build)

        # INPUT_PATH = os.path.join(INPUT_DIRECTORY, INPUT_FILENAME)
        # PREV_INPUT_PATH = os.path.join(PREV_INPUT_DIRECTORY, PREV_INPUT_FILENAME)

        inputFilename = current_build.get("file").get("name")
        inputPath = os.path.join(INPUT_DIRECTORY, inputFilename)

        if operation == "NEW":
            prevInputFilename = ""
        else:
            prevInputFilename = previous_build.get("file").get("name")

        if operation == "NEW":
            prevInputPath = ""
        else:
            prevInputPath = os.path.join(
                PREV_INPUT_DIRECTORY, prevInputFilename)

        current_download_url = current_build.get('download_url')

        if operation == "NEW":
            previous_download_url = None
        else:
            previous_download_url = previous_build.get('download_url')

        if inputFilename.lower().endswith(".zip"):
            parser_type = "bundle"
        else:
            parser_type = "scan"

        if parser_type == "bundle":
            output_extension = ".zip"
        else:
            output_extension = ".json"

        outputFilename = "result" + output_extension

        if parser_type == "bundle":
            bundleParser = True
        else:
            bundleParser = False

        config = {
            'INPUT_PATH': inputPath,
            'PREV_INPUT_PATH': prevInputPath,
            'INPUT_FILENAME': inputFilename,
            'PREV_INPUT_FILENAME': prevInputFilename,
            'OUTPUT_FILENAME': outputFilename,
            'OUTPUT_FILEFORMAT': "jsonl",
            "BUNDLE_PARSER": bundleParser
        }

        try:
            print("Initializing Global Variables")
            print(config)
            initGlobalVariables(
                config
            )
        except Exception as err:
            print("Exception", err)
            traceback.print_exc()
            pass

        try:
            syncIn(
                current_download_url,
                previous_download_url
            )
        except Exception as err:
            print("Exception", err)
            pass

        # return
        successfullyFinished, toolDetails, findings = parsingJob(
            extra_attributes)

        #

        report_generated = False
        try:
            _ = render_to_string('dojo/finding_pdf_report.html', {
                'report_name': 'Cyclops Report',
                # 'product': product,
                # 'engagement': engagement,
                # 'test': test,
                'findings': findings,
                # 'user': request.user,
                'team_name': "Whitehat (Times Internet Ltd.)",
                'title': 'Hawki: Security Risk Findings',
                'user_id': "whitehat"
            })
            # print("render_to_string", _)
            # print("upload_report_url", upload_report_url)
            # print("upload", upload_report)
            if upload_report:
                _ = bytes(_, 'utf-8')
                response = requests.put(upload_report_url, data=_)

            report_generated = True
            # print("report_generated" , report_generated)
        except:
            traceback.print_exc()
            print("Book mark")
            report_generated = False
            pass

        #

        _filter_update = json_util.loads(json_util.dumps(
            {"$set":
             {
                 "state_parsing_completed": successfullyFinished,
                 "tools_executed": toolDetails,
                 "state_parsing_completed_ts": datetime.datetime.utcnow(),
                 "transition_state": TransitionState.PARSING_FINISHED,
                 "report_generated": report_generated,
                 "extras": extra_attributes

             }
             }
        ))

        UpdateStatus(_filter_status, _filter_update)
    except:
        _filter_failed_update = json_util.loads(json_util.dumps(
            {"$set":
             {
                 "state_parsing_completed": False,
                 # "state_parsing_message": False ,
                 "state_parsing_started_ts": datetime.datetime.utcnow(),
                 "transition_state": TransitionState.FAILED
             }
             }
        ))
        traceback.print_exc()
        UpdateStatus(_filter_status, _filter_failed_update)

    # START: Generate a common PDF Report

    # print(_)

    # END

    # execute_from_command_line( [ "", "flush", "--no-input" ])

# print("boom", factory.get_api_scan_configuration_hints() )
for parser in enlistToolParser():
    print("parser.info", parser, factory.PARSERS[parser])
    
if __name__ == "!__main__":
    entryPoint()


def testFun( extra_attributes):
    

    

    PROCESS_DIRECTORY = os.getenv("PROCESS_DIRECTORY")
    OUTPUT_DIRECTORY = os.getenv("OUTPUT_DIRECTORY")
    TOOL_PARSER = os.getenv("TOOL_PARSER")

    
    

    cleanFs(PROCESS_DIRECTORY)
    cleanFs(OUTPUT_DIRECTORY)

    NO_ERROR = True
    TOOL_REPORTER = {

    }
    FINDINGS = list()

    RE_INPUT_PATH = os.path.join(INPUT_DIRECTORY, 're' + INPUT_FILENAME)


    try:
        
        
        print("parseReport",
            TOOL_PARSER, RE_INPUT_PATH, OUTPUT_PATH, INPUT_PATH, extra_attributes
              )
        with transaction.atomic():
            findings = parseReport(
                TOOL_PARSER, RE_INPUT_PATH, OUTPUT_PATH, INPUT_PATH, extra_attributes)
        FINDINGS += findings
        TOOL_REPORTER[TOOL_PARSER] = True

    except Exception as err:
        TOOL_REPORTER[TOOL_PARSER] = False
        NO_ERROR = False
        # traceback.print_exc()

    print("parseReports", findings)
    flushDb()
    cleanFs(PROCESS_DIRECTORY)

    return NO_ERROR, TOOL_REPORTER, FINDINGS


if __name__ == "__main__":
    
    TOOL_PARSER = "Checkmarx Scan detailed"
    
    setEnv("TOOL_PARSER", TOOL_PARSER)
    
    
    
    
    DEFAULT_OUTPUT_FILEFORMAT = 'json'

    INPUT_DIRECTORY = setEnv("INPUT_DIRECTORY", "/tmp")
    INPUT_FILENAME = setEnv("INPUT_FILENAME", "timesprime.xml")

    PREV_INPUT_DIRECTORY = setEnv("PREV_INPUT_DIRECTORY", INPUT_DIRECTORY)
    PREV_INPUT_FILENAME = setEnv("PREV_INPUT_FILENAME", "input.file")

    print(INPUT_DIRECTORY, INPUT_FILENAME)

    INPUT_PATH = os.path.join(INPUT_DIRECTORY, INPUT_FILENAME)
    PREV_INPUT_PATH = os.path.join(PREV_INPUT_DIRECTORY, PREV_INPUT_FILENAME)


    OUTPUT_DIRECTORY = setEnv("OUTPUT_DIRECTORY", "/tmp")
    PROCESS_DIRECTORY = setEnv("PROCESS_DIRECTORY", OUTPUT_DIRECTORY)
    OUTPUT_FILENAME = setEnv("OUTPUT_FILENAME",  "report.json")
    OUTPUT_FILEFORMAT = setEnv("OUTPUT_FILEFORMAT",  "json")

    DEFAULT_OUTPUT_FILEFORMAT = 'jsonl'
    
    if OUTPUT_FILEFORMAT not in ['json', 'jsonl']:
        OUTPUT_FILEFORMAT = DEFAULT_OUTPUT_FILEFORMAT

    OUTPUT_PATH = os.path.join(OUTPUT_DIRECTORY, OUTPUT_FILENAME)


    BUNDLE_PARSER = setEnv("BUNDLE_PARSER", "true")

    TOOL_PARSER = setEnv("TOOL_PARSER",TOOL_PARSER)
    

    
    result = testFun({"extra": {"key": "valye"} })
    print(result)