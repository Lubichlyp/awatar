import requests
import json
import time
import re
import os

from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")

# regex
CLEANR = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')

def cleanhtml(raw_html):
  cleantext = re.sub(CLEANR, '', raw_html)
  return cleantext

_id = 3520672
endpoint = f"https://londynek.net/api/get-data?hash=F8047E46311596755B6AE4B09C54D346B2DD712F&limit=1&sql_where=and%20ja.jdnews_id%3D{_id}&select_fields=news_content,movie_p,movie,headline,headline_en,title,title_en"

TEMPLATE_ID = "581f6d97e1224c38bf3bad1567e13c2f"

template_url = f"https://api.heygen.com/v2/template/{TEMPLATE_ID}/generate"

# przypisanie do 'dane'

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

# dane = {
#   "object": "events",
#   "type": "list",
#   "package": "events",
#   "data": [
#     {
#       "ev_id": 5030649,
#       "images": [
#         {
#           "file_name": "443042-202601131036-lg.png",
#           "id": 443042,
#           "url": "/image/jdevents",
#           "alt": ""
#         },
#         {
#           "file_name": "443651-202601200908-lg.jpg",
#           "id": 443651,
#           "url": "/image/jdevents",
#           "alt": ""
#         },
#         {
#           "file_name": "443653-202601200914-lg.jpg",
#           "id": 443653,
#           "url": "/image/jdevents",
#           "alt": ""
#         }
#       ],
#       "city_name_pl": "Aberdeen",
#       "ev_title_pl": "Polish-Scottish Mini Festival 2026 ",
#       "ev_headline_pl": "Polish-Scottish Mini Festival powraca w 2026 roku z bogatym programem artystycznym, łączącym muzykę, film, taniec i sztukę wizualną. Organizowany przez Polish Association Aberdeen, festiwal zaprasza mieszkańców całej Szkocji oraz gości z innych regionów UK do poznania polskiej i szkockiej kultury.",
#       "ev_text_pl": "\u003Cp style=\"text-align: center;\"\u003E\r\n\t\u003Cem\u003EPolish-Scottish Mini Festival 2026 &ndash; Nine Years of Cultural Dialogue in Aberdeen\u003Cbr /\u003E\r\n\tMusic &bull; Cinema &bull; Dance &bull; Visual Arts\u003C/em\u003E\u003C/p\u003E\r\n\u003Cp style=\"text-align: center;\"\u003E\r\n\t\u003Cstrong\u003EWydarzenia kluczowe:\u003C/strong\u003E\u003C/p\u003E\r\n\u003Cp style=\"text-align: center;\"\u003E\r\n\t\u003Cstrong\u003E12 stycznia &ndash; 13 lutego 2025:\u003C/strong\u003E \u003Cstrong\u003EWystawa &quot;Photographic Plates of Memory &ndash; Labyrinths&quot;\u003C/strong\u003E&nbsp;Mariana Kołodzieja w Aberdeen Central Library.\u003C/p\u003E\r\n\u003Cp style=\"text-align: center;\"\u003E\r\n\t\u003Cstrong\u003E26 stycznia 2025,\u003C/strong\u003E godz. 18:00: \u003Cstrong\u003ETowarzyszące spotkanie (exhibition talk).\u003C/strong\u003E\u003C/p\u003E\r\n\u003Cp style=\"text-align: center;\"\u003E\r\n\t\u003Cstrong\u003E31 stycznia 2026,\u003C/strong\u003E godz. 18:00: \u003Cstrong\u003EPolish-Scottish Ceilidh,\u003C/strong\u003E Pittodrie Stadium &ndash; wsp&oacute;lna zabawa taneczna przy polskich i szkockich rytmach, tradycyjne potrawy i muzyka zespołu Danse MaCabre.\u003Cbr /\u003E\r\n\t\u003Cstrong\u003E\u003Ca href=\"https://www.eventbrite.co.uk/e/polish-scottish-ceilidh-tickets-1653031294099\"\u003EBilety: &pound;11&ndash;&pound;22\u003C/a\u003E\u003C/strong\u003E\u003C/p\u003E\r\n\u003Cp style=\"text-align: center;\"\u003E\r\n\t\u003Cstrong\u003E6 lutego 2026,\u003C/strong\u003E godz. 19:30: \u003Cstrong\u003EKoncert Mechanicy Shanty &amp; Polish-Scottish Song Group, \u003C/strong\u003ENewton Dee Phoenix Centre &ndash; połączenie szant, folku i tradycji morskich obu kraj&oacute;w.\u003Cbr /\u003E\r\n\t\u003Cstrong\u003E\u003Ca href=\"https://www.eventbrite.co.uk/e/polish-scottish-mini-festival-2026-mechanicy-shanty-tickets-1697729638049\"\u003EBilety:&nbsp;&pound;17\u003C/a\u003E\u003C/strong\u003E\u003C/p\u003E\r\n\u003Cp style=\"text-align: center;\"\u003E\r\n\t\u003Cstrong\u003E13 lutego 2026,\u003C/strong\u003E godz. 19:30: \u003Cstrong\u003EWeljar &amp; Circle of Embers,\u003C/strong\u003E Unit 51 &ndash; muzyka folku i ambientu, pokaz tańca i światła LED.\u003Cbr /\u003E\r\n\t\u003Cstrong\u003E\u003Ca href=\"https://www.eventbrite.co.uk/e/polish-scottish-mini-festival-2026-weljar-tickets-1735585245189\"\u003EBilety:&nbsp;&pound;17\u003C/a\u003E\u003C/strong\u003E\u003C/p\u003E\r\n\u003Cp style=\"text-align: center;\"\u003E\r\n\t\u003Cstrong\u003E26&ndash;28 lutego 2026: Weekend Polish Cinema z IFF BellaTOFIFEST, gość specjalny Wojciech Smarzowski\u003C/strong\u003E &ndash; pokazy filmowe i sesje Q&amp;A z reżyserem.\u003C/p\u003E\r\n\u003Cp style=\"text-align: center;\"\u003E\r\n\t\u003Cstrong\u003E7 marca 2026\u003C/strong\u003E, godz. 19:30:\u003Cstrong\u003E Paulina Przybysz &amp; Estuary Trio, \u003C/strong\u003ELemon Tree &ndash; połączenie soulu, R&amp;B, jazzu i elektroniki.\u003Cbr /\u003E\r\n\t\u003Cstrong\u003E\u003Ca href=\"https://www.aberdeenperformingarts.com/whats-on/polish-scottish-mini-festival-2026-aberdeen-jazz-festival-paulina-przybysz-and-estuary-trio/\"\u003EBilety:&nbsp;&pound;25\u003C/a\u003E\u003C/strong\u003E\u003C/p\u003E\r\n\u003Cp style=\"text-align: center;\"\u003E\r\n\t\u003Cstrong\u003E13 września 2026,\u003C/strong\u003E godz. 18:00: \u003Cstrong\u003EKoncert Kazika Staszewskiego,\u003C/strong\u003E Lemon Tree &ndash; ikona polskiej muzyki alternatywnej, artysta znany z krytycznych i wielopokoleniowych tekst&oacute;w.\u003C/p\u003E\r\n\u003Cp style=\"text-align: center;\"\u003E\r\n\t\u003Cstrong\u003E\u003Ca href=\"https://www.aberdeenperformingarts.com/whats-on/polish-scottish-mini-festival-2026-kazik/\"\u003EBilety:&nbsp;&pound;45\u003C/a\u003E\u003C/strong\u003E\u003C/p\u003E\r\n\u003Cp style=\"text-align: center;\"\u003E\r\n\tFestiwal to wyjątkowa okazja, aby w Aberdeen spotkać polską i szkocką kulturę, wziąć udział w wydarzeniach muzycznych, tanecznych, filmowych i artystycznych oraz celebrować wieloletnią wsp&oacute;łpracę obu społeczności.\u003C/p\u003E\r\n"
#     }
#   ],
#   "has_more": "false"
# }


# dostęp do elementu:
# 1. ['data'][0] -> element listy data
# 2. ['images'][1] -> element listy image
# 3. ['file_name'] -> wartość klucza
# dane['data'][0]['images'][1]['file_name']

# zmiana url i file_name

for event in dane['data']:
    for image in event['images']:
        image['url'] = "images/jdevents/"
        temp = "https://assets.aws.londynek.net/" + image['url'] + image['file_name']
        image['file_name'] = temp
        # print(image['file_name']) 

# print(dane['data'][0]['images'][1]['url']) 

def sprawdz_obraz(url):
    try:
        r = requests.get(url, stream=True, timeout=5)
        return r.status_code == 200
    except:
        return False


headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "x-api-key": API_KEY
}

def sprawdz_obraz(url):
    try:
        r = requests.head(url, timeout=5)
        return r.status_code == 200
    except:
        return False
    
obraz_url = dane['data'][0]['images'][1]['file_name']

if not sprawdz_obraz(obraz_url):
    print("Obraz nie działa, używam placeholdera")
    obraz_url = "https://assets.aws.londynek.net/images/jdevents/443651-202601200908-lg.jpg"


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


#  funkcja do generowania filmu

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


