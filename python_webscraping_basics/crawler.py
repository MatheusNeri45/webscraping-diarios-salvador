from datetime import date, datetime, timedelta
import re
from io import *
import requests
from bs4 import BeautifulSoup
from .pdf_class import PDF
from .db_operations import insert_one_dom_db
from pymongo import MongoClient
import holidays

client: MongoClient = MongoClient()
db = client['diaries']
collection = db["salvador"]

holidays = holidays.country_holidays("BR","BA")
month_dict = {
    "01": "janeiro",
    "02": "fevereiro",
    "03": "março",
    "04": "abril",
    "05": "maio",
    "06": "junho",
    "07": "julho",
    "08": "agosto",
    "09": "setembro",
    "10": "outubro",
    "11": "novembro",
    "12": "dezembro"
}

def crawler_today():
    today = datetime.today().strftime('%Y-%m-%d')
    crawler_specific_day(date)


def crawler_specific_day(date:date):
     
    url = f"http://www.dom.salvador.ba.gov.br/index.php?filterTitle=&filterDateFrom={date}&filterDateTo={date}&option=com_dmarticlesfilter&view=articles&Itemid=3&userSearch=1&limstart=0"
    print(date)
    if is_weekend(date):
        return {
            "status": "PDF not downloaded",
            "message": f'{date} is on the weekend and the DOM will be available on the next day.'
                }
    elif is_holiday(date):
        return {
            "status": "PDF not downloaded",
            "message": f'{date} is a holiday and the DOM will be available on the next day.'
                }
    
    elif (is_monday(date) and not(is_holiday(date))):
        saturday_date = date - timedelta(days=2)
        data_extraction(url, saturday_date)     

    else:
        data_extraction(url, date)
    

def crawler_interval(date_start:date, date_finish:date):
         
    url = f"http://www.dom.salvador.ba.gov.br/index.php?filterTitle=&filterDateFrom={date_start}&filterDateTo={date_finish}&option=com_dmarticlesfilter&view=articles&Itemid=3&userSearch=1&limstart=0&limitstart=1"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    pagenav = str(soup("a", class_="pagenav")[-1])
    limit_start_regex = re.compile('limitstart=([0-9]*)')
    limit_start = limit_start_regex.search(pagenav).group()
    limit_start = int(limit_start[limit_start.find("=")+1::])
    end_pagination = 1

    while end_pagination<=limit_start+1:

        url = f"http://www.dom.salvador.ba.gov.br/index.php?filterTitle=&filterDateFrom={date_start}&filterDateTo={date_finish}&option=com_dmarticlesfilter&view=articles&Itemid=3&userSearch=1&limstart=0&limitstart={end_pagination}"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        print("Soup creation done!")
        results = soup("div",class_="dmarticlesfilter_results_title")

        for result in results:
            data_extraction_interval(result)
        end_pagination+=10
 

def data_extraction_interval(result):
    try:
        info = str(result)
    except:
        print("Problem with the soup/holiday/no dom in the interval")
        return{
            "status": "PDF not downloaded",
            "message": "There is no DOM for this interval"
        }

    else:
        dom_name_regex = re.compile('DOM+-+([0-9]*)')
        dom_date_regex = re.compile('([0-9]{4})+-+([0-9]{2})+-+([0-9]{2})')

        dom_name = dom_name_regex.search(info).group()
        dom_date = dom_date_regex.search(info).group()

        year = dom_date[:4]
        month = dom_date[5:7]
        day = dom_date[8:10]
        date = date(year, month, day)
        dom_name = 'dom'+dom_name[dom_name.find("-")::]
        
        url = f"http://www.dom.salvador.ba.gov.br/index.php?filterTitle=&filterDateFrom={date}&filterDateTo={date}&option=com_dmarticlesfilter&view=articles&Itemid=3&userSearch=1&limstart=0"
        if ((is_monday(date)) and not(is_holiday(date))):
            saturday_date = date - timedelta(days=2)
            data_extraction(url, saturday_date)     
        elif is_holiday(date):
                        return {
                    "status": "PDF not downloaded",
                    "message": f'{date} is a holiday.'
                }
        else:
            data_extraction(url, date)
        


def data_extraction(url:str, date:date):
    month_name = month_dict[str(date.month).zfill(2)]
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    print("Soup creation done!")
    tag = soup("div",class_="dmarticlesfilter_results_title")
    
    try:
        info = str(tag[0])
    except:
        print("Soup problem")
        return{
            "status":"PDF not downloaded",
            "message": "Internal error"
        }
    else: 
        dom_name_regex = re.compile('DOM+-+([0-9]*)')
        dom_name = dom_name_regex.search(info).group()
        dom_name = 'dom'+dom_name[dom_name.find("-")::]
        to_search = {"_id": dom_name}
        finding = db['salvador'].find_one(to_search)
        year = date.year
        day = str(date.day).zfill(2)
        month = str(date.month).zfill(2)

        if finding and finding["status"] == "downloaded":
            print('DOM already exists in the DB')
            return {
                    "status": "PDF downloaded",
                    "message": 'DOM already exists in the DB with full information'
                }

        elif finding and finding["status"] == "error_downloading":
            print('The DOM was NOT inserted because it already exists and it is marked as an error DOM')
            return {
                    "status": "PDF not downloaded",
                    "message": 'The DOM was NOT inserted because it already exists and it is marked as an error DOM'
                }


        else:
            link = f'http://www.dom.salvador.ba.gov.br/images/stories/pdf/{year}/{month_name}/{dom_name}-{day}-{month}-{year}.pdf'
            print(link)
            response = requests.get(link)
            pdf_bytes = BytesIO(response.content)
            try:
                pdf = PDF(pdf_bytes)
                
            except:
                document = {
                "dom_info": f"{dom_name}-{day}-{month}-{year}",
                "status": "error_downloading",
                }
                insert_one_dom_db(document, flag="no_pdf")
                return {
                    "status": "PDF not downloaded",
                    "message": "DOM added to DB with status marked as error_downloading"
                }

            else:
                document = {
                    "dom_info": f"{dom_name}-{day}-{month}-{year}",
                    "page_count": pdf.page_count,
                    "page_content": pdf.pages[1::],
                    "full_summary": pdf.summary,
                    "status": "downloaded"
                }
                insert_one_dom_db(document, flag="ok")
                return {
                    "status": "PDF downloaded",
                    "message": "Data added to DB and DOM marked as Downloaded"
                }


def is_monday(date: date):
    date_weekday = date.weekday()
    if(date_weekday==0):
        return True
    else:
        return False   

def is_weekend(date:date):
    date_weekday = date.weekday()
    if(date_weekday==5)|(date_weekday==6):
        return True
    else:
        return False

def is_holiday(date:date):
    if date in holidays:
        return True
    else:
        return False
