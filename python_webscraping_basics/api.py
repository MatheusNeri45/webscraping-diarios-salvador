from fastapi import FastAPI
from .crawler import *
from .db_operations import read_one_file_dom_db
app = FastAPI()
url = "http://www.dom.salvador.ba.gov.br/"

@app.get("/diaries/get_files")
def read_dom():
    read_one_file_dom_db()

@app.get("/diaries/today_crawler")
def get_today_diary():
    response_body = crawler_today()
    return response_body
@app.get("/diaries/specific_day_crawler")
def get_specific_diary(date:date):
    response_body = crawler_specific_day(date)
    return response_body
   
@app.get("/diaries/interval_day_crawler")
def get_date_pdf_file(date_start: date, date_finish: date):
    response_body = crawler_interval(date_start, date_finish)
    return response_body