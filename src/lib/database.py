import pymongo

db = None
with open("db_connection.txt", "r") as db_info:
    connection_info = db_info.readline()
    db = pymongo.MongoClient(connection_info)["stockbot_2021"]