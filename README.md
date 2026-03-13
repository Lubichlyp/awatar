# awatar

Prosty projekt do generowania wideo avatara na podstawie ID artykułu z API `londynek.net`, z użyciem szablonu w HeyGen.

## Jak to działa

1. Skrypt pobiera dane artykułu po `news_id` z endpointu Londynek.
2. Buduje URL obrazu i sprawdza, czy obraz jest dostępny.
3. (Domyślnie) robi `dry-run` walidując `template_id`, `avatar_id` i opcjonalnie `voice_id` przez API HeyGen.
4. Składa payload (obraz, tytuł, skrypt, podtytuł) do szablonu HeyGen.
5. Wysyła żądanie `POST` do API HeyGen i zwraca wynik generowania.

Główna logika: `generowanie.py`  
Proste API HTTP (FastAPI): `server.py`

## Wymagania

- Python 3.11+ (zalecane)
- Dostęp do internetu
- Klucz API HeyGen

## Instalacja

```bash
python -m venv venv
source venv/bin/activate
pip install requests fastapi uvicorn python-dotenv beautifulsoup4 jinja2 python-multipart
```

## Windows 11 (różnice)

Na Windows najczęściej używa się `py` zamiast `python` oraz innej ścieżki aktywacji `venv`.

PowerShell:

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install requests fastapi uvicorn python-dotenv beautifulsoup4 jinja2 python-multipart
```

CMD:

```cmd
py -m venv venv
venv\Scripts\activate.bat
pip install requests fastapi uvicorn python-dotenv beautifulsoup4 jinja2 python-multipart
```

Uruchomienie skryptu i API na Windows:

```powershell
py generowanie.py --id 12345
uvicorn server:app --reload
```

Jeśli `uvicorn` nie jest widoczny w `PATH`, użyj:

```powershell
py -m uvicorn server:app --reload
```

## Konfiguracja

W projekcie istnieje plik `.env` z:

```env
API_KEY=...
TEMPLATE_ID=...
AVATAR_ID=...
# opcjonalnie:
# VOICE_ID=...
# HEYGEN_TEST_MODE=true
# HEYGEN_WEBHOOK_URL=https://twoja-domena.pl/webhook/heygen
```

`generowanie.py` wczytuje klucz z `.env` przez `python-dotenv`.

## Uruchomienie z linii poleceń

```bash
python generowanie.py --id 12345
```

Gdzie `12345` to ID artykułu (`news_id`).

Opcje budżetowe:

- `--dry-run` / `--no-dry-run` - walidacja ID przez API HeyGen przed generowaniem
- `--short-test` / `--no-short-test` - krótki skrypt testowy z pierwszego wybranego akapitu

Przykłady:

```bash
# Bezpieczny tryb domyślny
python generowanie.py --id 12345

# Produkcyjnie (bez dry-run i z pełnym tekstem)
python generowanie.py --id 12345 --no-dry-run --no-short-test
```

## Uruchomienie API (FastAPI)

```bash
uvicorn server:app --reload
```

Endpointy:

- `GET /` - informacja o API
- `GET /app` - strona WWW z formularzem do skanowania URL i wyboru treści/obrazów
- `POST /scan` - skanuje wskazany URL i zwraca skompresowaną listę tekstów + obrazy do wyboru
- `POST /preview-web` - buduje i pokazuje payload JSON do akceptacji
- `POST /generate-web` - wysyła zatwierdzony payload do HeyGen
- `POST /webhook/heygen` - endpoint odbierający webhooki statusów materiałów z HeyGen
- `GET /webhook/heygen/events` - podgląd ostatnich zapisanych webhooków (debug)
- `GET /generuj/{news_id}` - uruchamia generowanie dla podanego `news_id`
  - query parametry: `dry_run` (domyślnie `true`), `short_test` (domyślnie `true`)

Przykład:

```bash
curl http://127.0.0.1:8000/generuj/12345
```

Pełny tekst bez dry-run:

```bash
curl "http://127.0.0.1:8000/generuj/12345?dry_run=false&short_test=false"
```

Przykład wejścia przez przeglądarkę:

```text
http://127.0.0.1:8000/app
```

## Uwagi

- Dla niedostępnego obrazu używany jest placeholder.
- Przed automatyzacją (np. pętlą `for`) przetestuj nietypowe requesty ręcznie w Postmanie lub Insomnii.
- W UI webowym generowanie jest dwuetapowe: podgląd payloadu, potem ręczne wysłanie do HeyGen.
- W UI webowym można zaznaczyć wiele obrazów. Obrazy z `logo` trafiają na górę listy, ale payload jako obraz główny preferuje zdjęcie nie-logo.
- Jeśli URL logo został już użyty w `variables` (np. zmienna `logo`), nie jest powielany w `selected_images`.
- W UI webowym awatar wybierany jest z listy pobieranej z API HeyGen (`/v2/avatars`).
- W UI webowym szablon wybierany jest z listy pobieranej z API HeyGen (`/v2/templates`).
- W UI webowym jest edytowalne pole `textarea` na skrypt: checkboxy tekstów zasilają je automatycznie, ale możesz ręcznie edytować i dopisać własną treść.
- Niektóre template'y mają pola stałe (bez edytowalnych zmiennych `text/image/character`) - wtedy część danych z formularza może nie być użyta przez sam template.
- Webhook nie jest dołączany do payloadu przy renderach inicjowanych ze stron `localhost`/`127.0.0.1`.
- Dodatkowo backend wymusza usunięcie `callback_url` dla żądań przychodzących na lokalny host (tryb developerski).
- Ostatni wygenerowany payload zapisywany jest do `data_settings/lat-payload.json`.
