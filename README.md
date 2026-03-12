# awatar

Prosty projekt do generowania wideo avatara na podstawie ID artykułu z API `londynek.net`, z użyciem szablonu w HeyGen.

## Jak to działa

1. Skrypt pobiera dane artykułu po `news_id` z endpointu Londynek.
2. Buduje URL obrazu i sprawdza, czy obraz jest dostępny.
3. Składa payload (obraz, tytuł, skrypt, podtytuł) do szablonu HeyGen.
4. Wysyła żądanie `POST` do API HeyGen i zwraca wynik generowania.

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
pip install requests fastapi uvicorn python-dotenv
```

## Windows 11 (różnice)

Na Windows najczęściej używa się `py` zamiast `python` oraz innej ścieżki aktywacji `venv`.

PowerShell:

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install requests fastapi uvicorn python-dotenv
```

CMD:

```cmd
py -m venv venv
venv\Scripts\activate.bat
pip install requests fastapi uvicorn python-dotenv
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
```

`generowanie.py` wczytuje klucz z `.env` przez `python-dotenv`.

## Uruchomienie z linii poleceń

```bash
python generowanie.py --id 12345
```

Gdzie `12345` to ID artykułu (`news_id`).

## Uruchomienie API (FastAPI)

```bash
uvicorn server:app --reload
```

Endpointy:

- `GET /` - informacja o API
- `GET /generuj/{news_id}` - uruchamia generowanie dla podanego `news_id`

Przykład:

```bash
curl http://127.0.0.1:8000/generuj/12345
```

## Uwagi

- Dla niedostępnego obrazu używany jest placeholder.
