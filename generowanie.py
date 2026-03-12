import requests
import json
import time
import re
import os
import argparse

def cleanhtml(raw_html):
  cleantext = re.sub(CLEANR, '', raw_html)
  return cleantext

def sprawdz_obraz(url):
    try:
        r = requests.get(url, stream=True, timeout=5)
        return r.status_code == 200
    except:
        return False

def generuj_wideo(url_obrazka, tytul, tresc, podtytul):
    payload = {
        "test": True, #zmiana z true na false
        "caption": False,
        "title": "TEST",
        "variables": {
            "image_": {
                "name": "image_",
                "type": "image",
                "properties": {
                "url": url_obrazka,
                "fit": "none"
                }
            },
            "title_": {
                "name": "title_",
                "type": "text",
                "properties": {
                "content": tytul
                }
            },
            "script1": {
                "name": "script1",
                "type": "text",
                "properties": {
                "content": tresc
                }
            },
            "subtitle_": {
                "name": "subtitle_",
                "type": "text",
                "properties": {
                "content": podtytul
                }
            },
            "background_": {
                "name": "background_",
                "type": "character",
                "properties": {
                "character_id": "Annie_Casual_Standing_Front_2_public",
                "type": "avatar"
                }
            }
        }
    }
    response = requests.post(template_url, json=payload, headers=headers)
    return response

def run(_id):
    endpoint = f"https://londynek.net/api/get-data?hash=F8047E46311596755B6AE4B09C54D346B2DD712F&limit=1&sql_where=and%20ja.jdnews_id%3D{_id}&select_fields=news_content,movie_p,movie,headline,headline_en,title,title_en"
    
    response = requests.get(endpoint)
    
    if response.status_code == 200:
        dane = response.json()
        print("dane przypiasne")
    else:
        print("Błąd pobierania danych:", response.text)
        exit()
    print("a")
    # print(dane)
    print("a")    

    # przypisanie do 'dane'

    # dostęp do elementu:
    # 1. ['data'][0] -> element listy data
    # 2. ['images'][1] -> element listy image
    # 3. ['file_name'] -> wartość klucza
    # dane['data'][0]['images'][1]['file_name']

    # zmiana url i file_name
    for event in dane['data']:
        for image in event['images']:
            # image['url'] = "images/jdevents/"
            image_url = image['url'].replace('/image/', '/images/')
            temp = "https://assets.aws.londynek.net/" + image_url + image['file_name']
            image['file_name'] = temp
            # print(image['file_name']) 

        obraz_url = dane['data'][0]['images'][1]['file_name']


    if not sprawdz_obraz(obraz_url):
        print("Obraz nie działa, używam placeholdera")
        obraz_url = "https://assets.aws.londynek.net/images/jdevents/443651-202601200908-lg.jpg"

    # print(dane['data'][0]['images'][1]['url']) 

    dane_do_filmu = {
        "obraz": obraz_url or ":)",
        "tytul": dane['data'][0]['title'] or ":)",
        "skrypt": dane['data'][0]['headline'] + ". " + cleanhtml(dane['data'][0]['news_content'])[:1850] or ":)",
        "podtytul": dane['data'][0]['title_en'] or ":)"
    }
    for klucz, wartosc in dane_do_filmu.items():
        print(f"{klucz}: {wartosc}")

    # dane_do_filmu = {
    #         "obraz": dane['data'][0]['images'][0]['file_name'],
    #         "tytul": dane['data'][0]['ev_title_pl'],
    #         "skrypt": dane['data'][0]['ev_headline_pl'] + ". " + cleanhtml(dane['data'][0]['ev_text_pl']),
    #         "podtytul": dane['data'][0]['city_name_pl']
    #     }

    # for element in dane_do_filmu:
    #     print(element)

# Generowanie


    wynik = generuj_wideo(dane_do_filmu['obraz'], dane_do_filmu["tytul"], dane_do_filmu["skrypt"], dane_do_filmu["podtytul"])

    print(wynik)
    if wynik.status_code == 200:
        id_filmu = wynik.json()["data"]["video_id"]
        print(f"Sukces! ID: {id_filmu}")
    else:
        print(f"Błąd: {wynik.text}")
    time.sleep(5)
    print("okejokej");

    return wynik.json()

CLEANR = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')

# from dotenv import load_dotenv

# load_dotenv()

# API_KEY = os.getenv("API_KEY")

API_KEY="sk_V2_hgu_kU5JDbSMR60_Bs8HKzcAThK2C2gXZCqdVtOMznxnVwRQ"

parser = argparse.ArgumentParser(
    description="Generator wideo na podstawie ID artykułu."
)

parser.add_argument(
    "--id",
    type=int,
    required=True,
    help="ID artykułu (np. 12345)"
)

args = parser.parse_args()

_id = args.id
print("Podane ID:", _id)

TEMPLATE_ID = "581f6d97e1224c38bf3bad1567e13c2f"

template_url = f"https://api.heygen.com/v2/template/{TEMPLATE_ID}/generate"

headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "x-api-key": API_KEY
}


if __name__ == "__main__":
    args = parser.parse_args()
    print("Podane ID:", args.id)

    wynik = run(args.id)
    print(wynik)