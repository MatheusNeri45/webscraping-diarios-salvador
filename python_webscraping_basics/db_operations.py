from pymongo import MongoClient
from json2html import *
from fastapi.responses import HTMLResponse

client: MongoClient = MongoClient()
db = client['diaries']
collection = db["salvador"]

def insert_one_dom_db(document):
    post_id = db['salvador'].insert_one(document).inserted_id
    return f'The DOM was inserted and the id on the DB is: {post_id}'
    
def read_one_file_dom_db(file_to_search=None):
    json_finding = collection.find_one()
    html_content: str = json2html.convert(json = json_finding)
    return HTMLResponse(content=html_content)
