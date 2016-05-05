from pymongo import MongoClient

client = MongoClient()
db = client.test
cursor = db. .find()