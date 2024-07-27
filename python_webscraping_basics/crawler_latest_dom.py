from .pdf_class import PDF
import re
from io import *
import requests
from bs4 import BeautifulSoup

def crawler_latest_dom(url):
    [dom_name, pdf_bytes] = retrieve_pdf(url)
    pdf = PDF(pdf_bytes)
    dom_name_reversed = dom_name[::-1]
    text_year_reversed = dom_name_reversed[0:4]
    text_month_reversed = dom_name_reversed[5:7]
    text_day_reversed = dom_name_reversed[8:10]
    text_year = int(text_year_reversed[::-1])
    text_month = int(text_month_reversed[::-1])
    text_day = int(text_day_reversed[::-1])

    document = {
        "text_year": text_year,
        "text_month": text_month,
        "text_day": text_day,
        "dom_name": dom_name,
        "page_count": pdf.page_count,
        "page_content": pdf.pages[1::],
        "full_summary": pdf.summary,
    }

    return dom_name, document

# from pdf_to_str import pdf2txt

def retrieve_pdf(url:str):
    #Criando a soup
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    print("Soup creation done!")
    #Encontrando a tag onde está o arquivo pdf
    link_regex = re.compile('http://www.dom.salvador.ba.gov.br/images/stories/pdf/+([0-9]{4})+/+([a-z]*)+/+dom+-+([0-9]*)+-+([0-9]{2})+-+([0-9]{2})+-+([0-9]{4})+.+pdf')
    dom_name_regex = re.compile('dom+-+([0-9]*)+-+([0-9]{2})+-+([0-9]{2})+-+([0-9]{4})')
    print("RegEx done!")
    tag = soup.find_all('a', {'href': link_regex})
    #Passando o link do arquivo para uma lista de links
    links: list[str] = [tags['href'] for tags in tag]
    first_link: str = links[0]
    print(first_link)
    dom_name = dom_name_regex.search(first_link).group()
    print("Diary name done")
    response = requests.get(first_link)
    pdf_bytes = BytesIO(response.content)
    print("PDF file wrote!")
    # pdf_string: str = pdf2txt(content)
    # print("PDF string retrieved!")
    return dom_name, pdf_bytes
