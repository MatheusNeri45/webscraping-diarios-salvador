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
    search_date = datetime.today()
    response = crawler_specific_day(search_date=search_date)
    return response

def crawler_specific_day(search_date:date):
    response = data_extraction(search_date=search_date)
    return response


def crawler_interval(date_start: date, date_finish:date):
    current_date = date_start
    log_insertion = []
    while current_date <= date_finish:
        response = crawler_specific_day(current_date)
        log_insertion.append(response)
        current_date=current_date+timedelta(days=1)
    return log_insertion

        

def data_extraction(search_date:date):
    pdf_date, new_search_date = pdf_date_url(search_date)
    url = f"http://www.dom.salvador.ba.gov.br/index.php?filterTitle=&filterDateFrom={new_search_date}&filterDateTo={new_search_date}&option=com_dmarticlesfilter&view=articles&Itemid=3&userSearch=1&limstart=0"
    month_name = month_dict[str(pdf_date.month).zfill(2)]
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    tag = soup("div",class_="dmarticlesfilter_results_title")
    
    try:
        info = str(tag[0])

    except:
        return{
            "status":"PDF not downloaded",
            "message": "Internal error."
        }
    else: 
        dom_name_regex = re.compile('DOM+-+([0-9]*)')
        dom_name = dom_name_regex.search(info).group()
        dom_name = 'dom'+dom_name[dom_name.find("-")::]
        to_search = {"dom_info": dom_name}
        finding = db['salvador'].find_one(to_search)

        if finding and finding["status"] == "downloaded":
            print('DOM already exists in the DB')
            return {
                    "status": "PDF downloaded",
                    "message": 'DOM already exists in the DB with full information'
                }
        else:
            year = pdf_date.year
            day = str(pdf_date.day).zfill(2)
            month = str(pdf_date.month).zfill(2)
            link = f'http://www.dom.salvador.ba.gov.br/images/stories/pdf/{year}/{month_name}/{dom_name}-{day}-{month}-{year}.pdf'
            response = requests.get(link)
            pdf_bytes = BytesIO(response.content)
            try:
                pdf = PDF(pdf_bytes)
                
            except:
                return {
                    "status": "PDF not downloaded",
                    "message": f"Error PDF function, check link: {link}"
                }

            else:
                document = {
                    "dom_info": f"{dom_name}-{day}-{month}-{year}",
                    "date": search_date.strftime("%d-%m-%Y"),
                    "page_count": pdf.page_count,
                    "page_content": pdf.pages[1::],
                    "full_summary": pdf.summary,
                    "status": "downloaded"
                }
                message = insert_one_dom_db(document)
                return {
                    "status": "PDF downloaded",
                    "message": message
                }

def is_holiday(date:date):
    return date in holidays


def pdf_date_url(search_date: date):
    weekday = search_date.weekday()
    pdf_date=search_date
    match weekday:
        case 0:
            if(is_holiday(search_date)):
                if(is_holiday(search_date - timedelta(days=3))):
                    pdf_date = search_date - timedelta(days=3)
                else:
                    pdf_date = search_date - timedelta(days=2)
                search_date += timedelta(days=1)
            else:
                if(is_holiday(search_date - timedelta(days=3))):
                    pdf_date = search_date - timedelta(days=3)
                else:
                    pdf_date = search_date - timedelta(days=2)             
        
        case 1:
            if is_holiday(search_date):
                pdf_date = search_date
                search_date += timedelta(days=1)
            else:
                if(is_holiday(search_date - timedelta(days=1))):
                    if(is_holiday(search_date - timedelta(days=4))):
                        pdf_date = search_date - timedelta(days=4)
                    else:
                        pdf_date = search_date - timedelta(days=3)
                else:
                    pdf_date = search_date

        case 2|3:
            if is_holiday(search_date):
                pdf_date = search_date
                search_date += timedelta(days=1)
            else:
                if(is_holiday(search_date - timedelta(days=1))):
                    pdf_date = search_date - timedelta(days=1)
                else:
                    pdf_date = search_date

        case 4:
            if is_holiday(search_date):
                pdf_date = search_date
                if is_holiday(search_date+timedelta(days=1)):
                    search_date += timedelta(days=4)
                else:
                    search_date += timedelta(days=1)
            else:
                if(is_holiday(search_date - timedelta(days=1))):
                    pdf_date = search_date - timedelta(days=1)
                else:
                    pdf_date = search_date

        case 5:
            if(is_holiday(search_date - timedelta(days=1))):
                pdf_date = search_date - timedelta(days=1)
                if is_holiday(search_date+timedelta(days=2)):
                    search_date += timedelta(days=3)
                else:
                    search_date += timedelta(days=2)
            else:
                pdf_date = search_date
                if is_holiday(search_date+timedelta(days=2)):
                    search_date += timedelta(days=3)
                else:
                    search_date += timedelta(days=2)      

        case 6:
            if(is_holiday(search_date - timedelta(days=2))):
                pdf_date = search_date - timedelta(days=2)
                if is_holiday(search_date+timedelta(days=1)):
                    search_date += timedelta(days=2)
                else:
                    search_date += timedelta(days=1)
            else:
                pdf_date = search_date - timedelta(days=1)
                if is_holiday(search_date+timedelta(days=1)):
                    search_date += timedelta(days=2)
                else:
                    search_date += timedelta(days=1)
    return pdf_date, search_date
             