from dojo import __version__

print("version", __version__)
import requests
import json
import traceback
from dojo_patch import entryPoint , enlistToolParser, getAllToolParser
from db import UpdateStatus


import pika
import os
from pika.exchange_type import ExchangeType


WEBHOOK_PARSER_FEEDS = os.getenv('WEBHOOK_PARSER_FEEDS', False)



TEST_DRIVE = os.getenv('TEST_DRIVE', True)
if not TEST_DRIVE == False :
    TEST_DRIVE = True

HOST = os.getenv('RABBITMQ_HOST', 'localhost')
USER = os.getenv('RABBITMQ_USER', 'guest')
PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'guest')



DEFAULT_TOPIC = 'DEVSECOPS_PARSER'

# 
EXCHANGE = DEFAULT_TOPIC
EXCHANGE_TYPE = ExchangeType.topic
QUEUE = DEFAULT_TOPIC
ROUTING_KEY = DEFAULT_TOPIC



# 

SAMPLE_MESSAGE = {

    "action": {
        "updateDb": True,
        "db_name": "dummy_db",
        
        "operation": "CREATE_NEW" ,
        "filter": "ALL",
        "upload": True,
        "upload_url": "",
        "overwrite_extra_attributes": False,
        "parser_type": "bundle", #Bundle , Scan
        "extra_attributes": {
            "applicationId": {"$oid": "6126098d72e6fcac53c2085d"},
            "buildId": {"$oid": "617ff2ff2f23cea39642c853"},
            "businessId": {"$oid": "5e0dbac209caf2fedfd310f6"},
            "platformId": {"$oid": "5e0dd2a6ae21f272971db085"},
            "projectId": {"$oid": "5e26b9d7557f3d8c94e426ef"},


        },
            },
    "data": {

        "previous": {
            "file":{
            "name": "test_shubham.zip",
            },
            # "download_url":  "http://172.24.42.87:9000/adtech---mediawire/test_first.zip?Content-Disposition=attachment%3B%20filename%3D%22test_first.zip%22&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAIOSFODNN7MINIO%2F20211111%2F%2Fs3%2Faws4_request&X-Amz-Date=20211111T113923Z&X-Amz-Expires=432000&X-Amz-SignedHeaders=host&X-Amz-Signature=aac03e6feacabe0c42f188856e335aec0b146f468afdc366b91e10f5bbf89ade",
            "download_url": "https://drive.google.com/uc?id=1EF7eWhgF23LNOMQP03y_p1wZvcmrPCky&export=download",


            # "download_url": "http://172.24.42.87:9000/adtech---mediawire/report.zip?Content-Disposition=attachment%3B%20filename%3D%22report.zip%22&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAIOSFODNN7MINIO%2F20211110%2F%2Fs3%2Faws4_request&X-Amz-Date=20211110T191930Z&X-Amz-Expires=432000&X-Amz-SignedHeaders=host&X-Amz-Signature=1e9f2e18c69ba02725564c03d3fe6ce76963a593808990ecd19f90a1862c445b",
            # "download_url": "http://172.24.42.87:9000/adtech---mediawire/Archive.zip?Content-Disposition=attachment%3B%20filename%3D%22Archive.zip%22&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAIOSFODNN7MINIO%2F20211110%2F%2Fs3%2Faws4_request&X-Amz-Date=20211110T174606Z&X-Amz-Expires=432000&X-Amz-SignedHeaders=host&X-Amz-Signature=e93de2a94ff0c0195caf4564b554b10b29fa451f31bdb85db0fc5c3a51ff16fe",
            # "download_url": "http://172.24.42.87:9000/adtech---mediawire/Dependency%20Check%20Scan.xml?Content-Disposition=attachment%3B%20filename%3D%22Dependency%20Check%20Scan.xml%22&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAIOSFODNN7MINIO%2F20211110%2F%2Fs3%2Faws4_request&X-Amz-Date=20211110T180344Z&X-Amz-Expires=432000&X-Amz-SignedHeaders=host&X-Amz-Signature=47669c76a7920545137a8ca6113f83989d1161d334f061fb6422c203b61de4f2",
            "applicationId": {"$oid": "6126098d72e6fcac53c2085d"},
            "applicationName": "Web Application",
            "buildNo": "162",
            "businessId": {"$oid": "5e0dbac209caf2fedfd310f6"},
            "businessName": "Security Test business",
            "error_msg": "Expecting value: line 1 column 1 (char 0)",
            "jenkinsJob": "test_job",
            "platformId": {"$oid": "5e0dd2a6ae21f272971db085"},
            "platformName": "Web Application",
            "projectId": {"$oid": "5e26b9d7557f3d8c94e426ef"},
            "projectName": "Test Prakhar",
            "status": "SUCCESS" ,
            "_id": {"$oid": "617ff2ff2f23cea39642c851"},
        },
        "current": {
            "file":{
            "name": "test_shubham.zip",
            },
            # "download_url":  "http://172.24.42.87:9000/adtech---mediawire/test_first.zip?Content-Disposition=attachment%3B%20filename%3D%22test_first.zip%22&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAIOSFODNN7MINIO%2F20211111%2F%2Fs3%2Faws4_request&X-Amz-Date=20211111T113923Z&X-Amz-Expires=432000&X-Amz-SignedHeaders=host&X-Amz-Signature=aac03e6feacabe0c42f188856e335aec0b146f468afdc366b91e10f5bbf89ade",
            "download_url": "https://drive.google.com/uc?id=1EF7eWhgF23LNOMQP03y_p1wZvcmrPCky&export=download",


            # "download_url": "https://hawki.indiatimes.com/minio/testbucket/5e0dbb0709caf2fedfd310f8/5e2966b8557f3d8c94e42706/5e0dd2a6ae21f272971db085/5fd9d91331a6a8556c11b34a/62c47f3576801ad131a93161/amass.zip?response-content-disposition=attachment%3B%20filename%3Damass.zip&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAIOSFODNN7MINIO%2F20220706%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20220706T140258Z&X-Amz-Expires=604800&X-Amz-SignedHeaders=host&X-Amz-Signature=d243530819b7c267a014c94f98a84082a8ba8a43a73a99981f43aaa5fed3cee7",
            # "download_url": "http://172.24.42.87:9000/adtech---mediawire/report.zip?Content-Disposition=attachment%3B%20filename%3D%22report.zip%22&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAIOSFODNN7MINIO%2F20211110%2F%2Fs3%2Faws4_request&X-Amz-Date=20211110T191930Z&X-Amz-Expires=432000&X-Amz-SignedHeaders=host&X-Amz-Signature=1e9f2e18c69ba02725564c03d3fe6ce76963a593808990ecd19f90a1862c445b",
            # "download_url": "http://172.24.42.87:9000/adtech---mediawire/Archive.zip?Content-Disposition=attachment%3B%20filename%3D%22Archive.zip%22&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAIOSFODNN7MINIO%2F20211110%2F%2Fs3%2Faws4_request&X-Amz-Date=20211110T174606Z&X-Amz-Expires=432000&X-Amz-SignedHeaders=host&X-Amz-Signature=e93de2a94ff0c0195caf4564b554b10b29fa451f31bdb85db0fc5c3a51ff16fe",
            # "download_url": "http://172.24.42.87:9000/adtech---mediawire/Dependency%20Check%20Scan.xml?Content-Disposition=attachment%3B%20filename%3D%22Dependency%20Check%20Scan.xml%22&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAIOSFODNN7MINIO%2F20211110%2F%2Fs3%2Faws4_request&X-Amz-Date=20211110T180344Z&X-Amz-Expires=432000&X-Amz-SignedHeaders=host&X-Amz-Signature=47669c76a7920545137a8ca6113f83989d1161d334f061fb6422c203b61de4f2",
            "applicationId": {"$oid": "6126098d72e6fcac53c2085d"},
            "applicationName": "Web Application",
            "buildNo": "162",
            "businessId": {"$oid": "5e0dbac209caf2fedfd310f6"},
            "businessName": "Security Test business",
            "error_msg": "Expecting value: line 1 column 1 (char 0)",
            "jenkinsJob": "test_job",
            "platformId": {"$oid": "5e0dd2a6ae21f272971db085"},
            "platformName": "Web Application",
            "projectId": {"$oid": "5e26b9d7557f3d8c94e426ef"},
            "projectName": "Test Prakhar",
            "status": "SUCCESS" ,
            "_id": {"$oid": "617ff2ff2f23cea39642c851"},
        }
    }


}


def sendMsg(channel):
    channel.basic_publish(exchange='',
                         routing_key=QUEUE,
                         body=json.dumps( SAMPLE_MESSAGE ),
                         properties=pika.BasicProperties(content_type='text/plain',
                                                         delivery_mode=1
                                                         ),
                         mandatory=True)


def initializeRabbitMq():


    credentials = pika.PlainCredentials(USER, PASSWORD)
    params = pika.ConnectionParameters(HOST,5672, '/',credentials)
    connection = pika.BlockingConnection(parameters=params)
    channel = connection.channel()



    channel.exchange_declare(EXCHANGE, EXCHANGE_TYPE)
    channel.queue_declare(queue=QUEUE, durable=False)
    channel.basic_qos(prefetch_count=1)
    return channel, connection




def parseMessage(message: str):
    # print("Parsing Message", message)
    try:
        entryPoint(message)
    except:
        traceback.print_exc()
        pass

def startConsumer():
    print("startConsumer", QUEUE)
    if TEST_DRIVE:
        return parseMessage(SAMPLE_MESSAGE)
    else:
        channel, connection = initializeRabbitMq()
        print("initializeRabbitMq", channel, connection)

        # sendMsg(channel)
        # sendMsg(channel)
        for method_frame, properties, body in channel.consume( queue=QUEUE):
            # Display the message parts
            print(method_frame)
            # print(properties)
            print("*************")
            print(body)
            print("*************")

            # Acknowledge the message
            channel.basic_ack(method_frame.delivery_tag)
            connection.close()
            parseMessage(body)



if __name__ == "__main__":
    print("ready to rock and toll")
    # print(enlistToolParser())
    # channel, connection = initializeRabbitMq()
    # sendMsg(channel)
    # sendMsg(channel)
    # sendMsg(channel)
    # sendMsg(channel)
    # sendMsg(channel)
    # sendMsg(channel)
    # sendMsg(channel)
    # connection.close()
    # _ = json.dumps(SAMPLE_MESSAGE)
    # parseMessage(_)
    # exit()

    # Undo Here

    startConsumer( )


    
    
    pass

    dojo_parser_data = []
    for parser_name ,parser in getAllToolParser():
        scan_types = parser.get_scan_types()
        
        scan_type_details = {}
        for scan_type in scan_types:
            scan_type_details[scan_type] = {
                "title": parser.get_label_for_scan_types( scan_type ),
                "description": parser.get_description_for_scan_types( scan_type ),
            }
            

        parset_details = {
            "id": parser_name,
            "name": parser_name,
            "title": parser.get_label_for_scan_types( parser_name ),
            "description": parser.get_description_for_scan_types( parser_name ),
            "version": __version__
            
        }
        
        dojo_parser_data.append(parset_details)
        
    
    print("parset_details", dojo_parser_data)
    webhook_response = requests.post(WEBHOOK_PARSER_FEEDS , json= {"version": __version__ , "details" : dojo_parser_data } ).json()
    print("webhook_response", webhook_response)

    # Uncomment below
    # while True:
        # startConsumer( )
        # break

    # !Undo Here

    



    

