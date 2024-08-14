from pymongo import MongoClient
import traceback
from pymongo.errors import ConnectionFailure
import os

# 
MONGO_HOST=os.getenv('MONGO_HOST', 'mongodb://hawkireg.indiatimes2.com')
MONGO_PORT=int(os.getenv('MONGO_PORT', 27017))
MONGO_USER=(os.getenv('MONGO_USER', None))
MONGO_PASSWORD=(os.getenv('MONGO_PASSWORD', None))
MONGO_AUTH_SOIRCE=(os.getenv('MONGO_AUTH_SOIRCE', None))

DB_NAME = os.getenv('DB_NAME', 'meddler')
FINDINGS_COLLECTION_NAME = os.getenv('OLLECTION_NAME', 'test_devsecops_findings')
BUILDS_COLLECTION_NAME = os.getenv('BUILDS_COLLECTION_NAME', 'devsecops')


# 
MONGO_DB = None
MONGO_COLLECTION = None
MONGO_BUILD_COLLECTION = None

def setDb(db_name):
    global DB_NAME
    DB_NAME = db_name
    print("setDb", DB_NAME)
    initDb()

def initDb():
    global MONGO_COLLECTION, MONGO_BUILD_COLLECTION
    print("Initializing DB")


  
        
    client = MongoClient(  MONGO_HOST,
                            username=MONGO_USER,
                            password=MONGO_PASSWORD,
                            authSource=MONGO_AUTH_SOIRCE,
                            authMechanism='SCRAM-SHA-1',
                            connect=True)

    try:
        # The ismaster command is cheap and does not require auth.
        # print("Connected to Mongo", MONGO_HOST, MONGO_USER, MONGO_PASSWORD, MONGO_AUTH_SOIRCE)
        client.admin.command('ismaster')
        print("Connected to Mongo")
    except ConnectionFailure :
        traceback.print_exc()
        print("Mongo Looks to be down")
    global MONGO_DB
    MONGO_DB = client[DB_NAME]
    MONGO_COLLECTION = MONGO_DB[FINDINGS_COLLECTION_NAME]
    MONGO_BUILD_COLLECTION = MONGO_DB[BUILDS_COLLECTION_NAME]
    

    return MONGO_COLLECTION

def UpdateStatus(matchCriteria: dict, updatedAttributes: dict):
    global MONGO_BUILD_COLLECTION
    updateResult =  MONGO_BUILD_COLLECTION.update_one(matchCriteria, updatedAttributes)
    print("*************updateResult************")
    print(matchCriteria)
    print(updatedAttributes)
    print(updateResult)
    print("*************updateResult************")
    


def BulkInsert(findings, matchCriteria: dict):
    buildId = matchCriteria["buildId"]
    del matchCriteria["buildId"]

    for finding in findings:
        matchCriteria["id"] = finding["id"]
        matchCriteria["found_by"] = finding["found_by"]
        # print("matchCriteria", matchCriteria)
        updateResult = getMongoRef().update_one( matchCriteria, { "$set": finding, "$addToSet": {"refrence_ids": buildId  } }  , upsert=True )
        # print("updateResult", updateResult.modified_count)
    # print("Inserting findings in DB: TOTAL", len(findings))
    # insertedIds = getMongoRef().insert_many(findings).inserted_ids
    # print("Inserted findings in DB: TOTAL", len(insertedIds))




def BulkFind(matchCriteria: dict):
    buildId = matchCriteria["buildId"]

    # print("matchCriteria", matchCriteria)
    result = getMongoRef().find(  {
        "refrence_ids": buildId
    } )

    return list(result)
        # print("updateResult", updateResult.modified_count)
    # print("Inserting findings in DB: TOTAL", len(findings))
    # insertedIds = getMongoRef().insert_many(findings).inserted_ids
    # print("Inserted findings in DB: TOTAL", len(insertedIds))


def getMongoRef():
    global MONGO_COLLECTION

    if  MONGO_COLLECTION == None:
        return initDb()
    else:
        return MONGO_COLLECTION


# initDb()
