import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

import generowanie

app = FastAPI(title="Generator wideo")
templates = Jinja2Templates(directory="templates")
WEBHOOK_LOG = Path("webhooks/heygen_events.jsonl")


# Sprawdza, czy biezace zadanie pochodzi z lokalnego hosta.
def _request_is_localhost(request: Request) -> bool:
    host = (request.url.hostname or "").lower()
    return host in {"localhost", "127.0.0.1", "::1"}


# Laduje liste awatarow z fallbackiem do domyslnego wpisu.
def _load_avatars_safe() -> list[dict[str, str]]:
    try:
        avatars = generowanie.list_avatars()
        if avatars:
            return avatars
    except Exception:
        pass
    return [{"id": generowanie.AVATAR_ID, "name": generowanie.AVATAR_ID, "thumbnail": ""}]


# Zwraca minimalna domyslna liste awatarow dla UI.
def _default_avatars() -> list[dict[str, str]]:
    return [{"id": generowanie.AVATAR_ID, "name": generowanie.AVATAR_ID, "thumbnail": ""}]


# Laduje awatary z HeyGen i zwraca ewentualne ostrzezenie dla UI.
def _load_avatars_with_warning() -> tuple[list[dict[str, str]], str | None]:
    try:
        avatars = generowanie.list_avatars()
        if avatars:
            return avatars, None
        return (
            _default_avatars(),
            "Nie udało się pobrać listy awatarów z HeyGen. Wyświetlono awatar domyślny.",
        )
    except Exception as exc:
        return (
            _default_avatars(),
            f"Nie udało się pobrać listy awatarów z HeyGen: {exc}",
        )


# Laduje awatary z cache i zwraca ewentualne ostrzezenie dla UI.
def _load_cached_avatars_with_warning() -> tuple[list[dict[str, str]], str | None]:
    avatars = generowanie.read_cached_avatars()
    if avatars:
        return avatars, "Lista awatarów została wczytana z lokalnego cache."
    return _default_avatars(), "Brak lokalnego cache awatarów. Wyświetlono awatar domyślny."


# Laduje liste template'ow z fallbackiem do domyslnego wpisu.
def _load_templates_safe() -> list[dict[str, str]]:
    try:
        templates = generowanie.list_templates()
        if templates:
            return templates
    except Exception:
        pass
    return [{"id": generowanie.TEMPLATE_ID, "name": generowanie.TEMPLATE_ID}]


# Zwraca minimalna domyslna liste template'ow dla UI.
def _default_templates() -> list[dict[str, str]]:
    return [{"id": generowanie.TEMPLATE_ID, "name": generowanie.TEMPLATE_ID}]


# Laduje template'y z HeyGen albo z cache wraz z komunikatem dla UI.
def _load_templates_with_warning(use_live_data: bool) -> tuple[list[dict[str, str]], str | None]:
    if use_live_data:
        try:
            templates = generowanie.list_templates()
            if templates:
                return templates, None
            return _default_templates(), "Nie udało się pobrać listy szablonów z HeyGen."
        except Exception as exc:
            return _default_templates(), f"Nie udało się pobrać listy szablonów z HeyGen: {exc}"

    templates = generowanie.read_cached_templates()
    if templates:
        return templates, "Lista szablonów została wczytana z lokalnego cache."
    return _default_templates(), "Brak lokalnego cache szablonów. Wyświetlono szablon domyślny."


# Wyciaga ID awatara z payloadu HeyGen.
def _extract_avatar_id_from_payload(payload: dict) -> str:
    try:
        variables = payload.get("variables", {})
        if isinstance(variables, dict):
            for item in variables.values():
                if not isinstance(item, dict):
                    continue
                if str(item.get("type", "")).lower() != "character":
                    continue
                return str(item.get("properties", {}).get("character_id", generowanie.AVATAR_ID))
        return generowanie.AVATAR_ID
    except Exception:
        return generowanie.AVATAR_ID


# Ustala ID template'u z formularza lub z payloadu.
def _extract_template_id_from_form_or_payload(selected_template_id: str, payload: dict) -> str:
    value = (selected_template_id or "").strip()
    if value:
        return value
    try:
        return str(payload.get("template_id_selected", generowanie.TEMPLATE_ID))
    except Exception:
        return generowanie.TEMPLATE_ID


# Serializuje wynik skanu strony do ukrytego pola formularza.
def _build_scan_snapshot(scan: dict | None) -> str:
    if not isinstance(scan, dict):
        return ""
    try:
        payload = {
            "source_url": scan.get("source_url", ""),
            "title": scan.get("title", ""),
            "texts": scan.get("texts", []),
            "images": scan.get("images", []),
        }
        return json.dumps(payload, ensure_ascii=False)
    except Exception:
        return ""


# Odtwarza wynik skanu strony z danych przeslanych w formularzu.
def _parse_scan_snapshot(scan_snapshot: str) -> dict | None:
    value = (scan_snapshot or "").strip()
    if not value:
        return None
    try:
        payload = json.loads(value)
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    return {
        "source_url": str(payload.get("source_url", "")).strip(),
        "title": str(payload.get("title", "")).strip(),
        "texts": payload.get("texts", []) if isinstance(payload.get("texts", []), list) else [],
        "images": payload.get("images", []) if isinstance(payload.get("images", []), list) else [],
    }


@app.get("/")
def root():
    return {"info": "API generatora wideo", "web_ui": "/app"}


@app.get("/app", response_class=HTMLResponse)
def app_page(request: Request):
    return templates.TemplateResponse(
        "generator.html",
        {
            "request": request,
            "scan": None,
            "scan_snapshot": "",
            "error": None,
            "result": None,
            "payload_preview": None,
            "avatars": _default_avatars(),
            "avatar_warning": None,
            "templates_list": _default_templates(),
            "selected_avatar_id": generowanie.AVATAR_ID,
            "selected_template_id": generowanie.TEMPLATE_ID,
            "form_data": {"dry_run": True, "short_test": True},
        },
    )


@app.post("/scan", response_class=HTMLResponse)
def scan_page(request: Request, url: str = Form(...)):
    try:
        scan = generowanie.scan_webpage(url)
        return templates.TemplateResponse(
            "generator.html",
            {
                "request": request,
                "scan": scan,
                "scan_snapshot": _build_scan_snapshot(scan),
                "error": None,
                "result": None,
                "payload_preview": None,
                "avatars": _default_avatars(),
                "avatar_warning": None,
                "templates_list": _default_templates(),
                "selected_avatar_id": generowanie.AVATAR_ID,
                "selected_template_id": generowanie.TEMPLATE_ID,
                "form_data": {"dry_run": True, "short_test": True},
            },
        )
    except Exception as e:
        return templates.TemplateResponse(
            "generator.html",
            {
                "request": request,
                "scan": None,
                "scan_snapshot": "",
                "error": str(e),
                "result": None,
                "payload_preview": None,
                "avatars": _default_avatars(),
                "avatar_warning": None,
                "templates_list": _default_templates(),
                "selected_avatar_id": generowanie.AVATAR_ID,
                "selected_template_id": generowanie.TEMPLATE_ID,
                "form_data": {"dry_run": True, "short_test": True},
            },
            status_code=400,
        )


@app.post("/preview-web", response_class=HTMLResponse)
def preview_web(
    request: Request,
    source_url: str = Form(...),
    scan_snapshot: str = Form(""),
    title: str = Form(""),
    subtitle: str = Form(""),
    selected_avatar_id: str = Form(generowanie.AVATAR_ID),
    selected_template_id: str = Form(generowanie.TEMPLATE_ID),
    script_text: str = Form(""),
    selected_texts: Optional[list[str]] = Form(None),
    selected_images: Optional[list[str]] = Form(None),
    dry_run: Optional[str] = Form(None),
    short_test: Optional[str] = Form(None),
):
    try:
        scan = _parse_scan_snapshot(scan_snapshot)
        payload = generowanie.build_payload_from_selection(
            source_url=source_url,
            selected_texts=selected_texts or [],
            selected_images=selected_images or [],
            script_text=script_text,
            title=title,
            subtitle=subtitle,
            selected_avatar_id=selected_avatar_id,
            selected_template_id=selected_template_id,
            dry_run=False,
            short_test=short_test is not None,
            fast_preview=True,
        )
        if _request_is_localhost(request):
            payload.pop("callback_url", None)
            payload["webhook_enabled"] = False
        return templates.TemplateResponse(
            "generator.html",
            {
                "request": request,
                "scan": scan,
                "scan_snapshot": scan_snapshot,
                "error": None,
                "result": None,
                "payload_preview": json.dumps(payload, indent=2, ensure_ascii=False),
                "avatars": _default_avatars(),
                "avatar_warning": None,
                "templates_list": _default_templates(),
                "selected_avatar_id": selected_avatar_id,
                "selected_template_id": selected_template_id,
                "form_data": {
                    "source_url": source_url,
                    "title": title,
                    "subtitle": subtitle,
                    "selected_avatar_id": selected_avatar_id,
                    "selected_template_id": selected_template_id,
                    "script_text": script_text,
                    "selected_texts": selected_texts or [],
                    "selected_images": selected_images or [],
                    "dry_run": dry_run is not None,
                    "short_test": short_test is not None,
                },
            },
        )
    except Exception as e:
        scan = _parse_scan_snapshot(scan_snapshot)
        return templates.TemplateResponse(
            "generator.html",
            {
                "request": request,
                "scan": scan,
                "scan_snapshot": scan_snapshot,
                "error": str(e),
                "result": None,
                "payload_preview": None,
                "avatars": _default_avatars(),
                "avatar_warning": None,
                "templates_list": _default_templates(),
                "selected_avatar_id": selected_avatar_id,
                "selected_template_id": selected_template_id,
                "form_data": {
                    "source_url": source_url,
                    "title": title,
                    "subtitle": subtitle,
                    "selected_avatar_id": selected_avatar_id,
                    "selected_template_id": selected_template_id,
                    "script_text": script_text,
                    "selected_texts": selected_texts or [],
                    "selected_images": selected_images or [],
                    "dry_run": dry_run is not None,
                    "short_test": short_test is not None,
                },
            },
            status_code=400,
        )


@app.post("/generate-web", response_class=HTMLResponse)
def generate_web(
    request: Request,
    source_url: str = Form(...),
    payload_json: str = Form(...),
    scan_snapshot: str = Form(""),
    selected_template_id: str = Form(generowanie.TEMPLATE_ID),
    dry_run: Optional[str] = Form(None),
    short_test: Optional[str] = Form(None),
):
    payload: dict = {}
    try:
        payload = json.loads(payload_json)
        if _request_is_localhost(request):
            payload.pop("callback_url", None)
            payload["webhook_enabled"] = False
        template_id = _extract_template_id_from_form_or_payload(selected_template_id, payload)
        wynik = generowanie.submit_payload(payload, template_id=template_id)
        scan = _parse_scan_snapshot(scan_snapshot)
        selected_avatar_id = _extract_avatar_id_from_payload(payload)
        return templates.TemplateResponse(
            "generator.html",
            {
                "request": request,
                "scan": scan,
                "scan_snapshot": scan_snapshot,
                "error": None,
                "result": wynik,
                "payload_preview": json.dumps(payload, indent=2, ensure_ascii=False),
                "avatars": _default_avatars(),
                "avatar_warning": None,
                "templates_list": _default_templates(),
                "selected_avatar_id": selected_avatar_id,
                "selected_template_id": template_id,
                "form_data": {
                    "source_url": source_url,
                    "selected_avatar_id": selected_avatar_id,
                    "selected_template_id": template_id,
                    "dry_run": dry_run is not None,
                    "short_test": short_test is not None,
                },
            },
        )
    except Exception as e:
        scan = _parse_scan_snapshot(scan_snapshot)
        selected_avatar_id = _extract_avatar_id_from_payload(payload if isinstance(payload, dict) else {})
        return templates.TemplateResponse(
            "generator.html",
            {
                "request": request,
                "scan": scan,
                "scan_snapshot": scan_snapshot,
                "error": str(e),
                "result": None,
                "payload_preview": None,
                "avatars": _default_avatars(),
                "avatar_warning": None,
                "templates_list": _default_templates(),
                "selected_avatar_id": selected_avatar_id,
                "selected_template_id": selected_template_id or generowanie.TEMPLATE_ID,
                "form_data": {
                    "source_url": source_url,
                    "selected_avatar_id": selected_avatar_id,
                    "selected_template_id": selected_template_id or generowanie.TEMPLATE_ID,
                    "dry_run": dry_run is not None,
                    "short_test": short_test is not None,
                },
            },
            status_code=400,
        )


@app.get("/api/avatars")
def api_avatars(dry_run: bool = True):
    avatars, warning = _load_avatars_with_warning() if dry_run else _load_cached_avatars_with_warning()
    return {"items": avatars, "warning": warning}


@app.get("/api/templates")
def api_templates(dry_run: bool = True):
    templates, warning = _load_templates_with_warning(dry_run)
    return {"items": templates, "warning": warning}


@app.get("/generuj/{news_id}")
def generuj(request: Request, news_id: int, dry_run: bool = True, short_test: bool = True):
    try:
        origin = str(request.base_url) if _request_is_localhost(request) else None
        wynik = generowanie.run(news_id, dry_run=dry_run, short_test=short_test, request_origin=origin)
        return {"status": "ok", "wynik": wynik}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/webhook/heygen")
async def heygen_webhook(request: Request):
    payload = await request.json()

    source_url = str(payload.get("source_url", "")).strip()
    if source_url and generowanie.is_localhost_url(source_url):
        return JSONResponse({"status": "ignored", "reason": "localhost_source"}, status_code=202)

    WEBHOOK_LOG.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "received_at": datetime.now(timezone.utc).isoformat(),
        "headers": {
            "x-heygen-signature": request.headers.get("x-heygen-signature", ""),
            "user-agent": request.headers.get("user-agent", ""),
        },
        "payload": payload,
    }
    with WEBHOOK_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

    return {"status": "ok"}


@app.get("/webhook/heygen/events")
def heygen_webhook_events(limit: int = 20):
    if not WEBHOOK_LOG.exists():
        return {"events": []}

    lines = WEBHOOK_LOG.read_text(encoding="utf-8").splitlines()
    selected = lines[-max(1, min(limit, 200)) :]
    events = [json.loads(line) for line in selected if line.strip()]
    return {"events": events}
