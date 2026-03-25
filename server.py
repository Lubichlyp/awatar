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


def _request_is_localhost(request: Request) -> bool:
    host = (request.url.hostname or "").lower()
    return host in {"localhost", "127.0.0.1", "::1"}


def _load_avatars_safe() -> list[dict[str, str]]:
    try:
        avatars = generowanie.list_avatars()
        if avatars:
            return avatars
    except Exception:
        pass
    return [{"id": generowanie.AVATAR_ID, "name": generowanie.AVATAR_ID, "thumbnail": ""}]


def _load_templates_safe() -> list[dict[str, str]]:
    try:
        templates = generowanie.list_templates()
        if templates:
            return templates
    except Exception:
        pass
    return [{"id": generowanie.TEMPLATE_ID, "name": generowanie.TEMPLATE_ID}]


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


def _extract_template_id_from_form_or_payload(selected_template_id: str, payload: dict) -> str:
    value = (selected_template_id or "").strip()
    if value:
        return value
    try:
        return str(payload.get("template_id_selected", generowanie.TEMPLATE_ID))
    except Exception:
        return generowanie.TEMPLATE_ID


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
            "error": None,
            "result": None,
            "payload_preview": None,
            "avatars": _load_avatars_safe(),
            "templates_list": _load_templates_safe(),
            "selected_avatar_id": generowanie.AVATAR_ID,
            "selected_template_id": generowanie.TEMPLATE_ID,
        },
    )


@app.post("/scan", response_class=HTMLResponse)
def scan_page(request: Request, url: str = Form(...)):
    try:
        scan = generowanie.scan_webpage(url)
        avatars = _load_avatars_safe()
        templates_list = _load_templates_safe()
        return templates.TemplateResponse(
            "generator.html",
            {
                "request": request,
                "scan": scan,
                "error": None,
                "result": None,
                "payload_preview": None,
                "avatars": avatars,
                "templates_list": templates_list,
                "selected_avatar_id": generowanie.AVATAR_ID,
                "selected_template_id": generowanie.TEMPLATE_ID,
            },
        )
    except Exception as e:
        return templates.TemplateResponse(
            "generator.html",
            {
                "request": request,
                "scan": None,
                "error": str(e),
                "result": None,
                "payload_preview": None,
                "avatars": _load_avatars_safe(),
                "templates_list": _load_templates_safe(),
                "selected_avatar_id": generowanie.AVATAR_ID,
                "selected_template_id": generowanie.TEMPLATE_ID,
            },
            status_code=400,
        )


@app.post("/preview-web", response_class=HTMLResponse)
def preview_web(
    request: Request,
    source_url: str = Form(...),
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
        payload = generowanie.build_payload_from_selection(
            source_url=source_url,
            selected_texts=selected_texts or [],
            selected_images=selected_images or [],
            script_text=script_text,
            title=title,
            subtitle=subtitle,
            selected_avatar_id=selected_avatar_id,
            selected_template_id=selected_template_id,
            dry_run=dry_run is not None,
            short_test=short_test is not None,
        )
        if _request_is_localhost(request):
            payload.pop("callback_url", None)
            payload["webhook_enabled"] = False
        scan = generowanie.scan_webpage(source_url)
        avatars = _load_avatars_safe()
        templates_list = _load_templates_safe()
        return templates.TemplateResponse(
            "generator.html",
            {
                "request": request,
                "scan": scan,
                "error": None,
                "result": None,
                "payload_preview": json.dumps(payload, indent=2, ensure_ascii=False),
                "avatars": avatars,
                "templates_list": templates_list,
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
        scan = None
        try:
            scan = generowanie.scan_webpage(source_url)
        except Exception:
            pass
        avatars = _load_avatars_safe()
        templates_list = _load_templates_safe()
        return templates.TemplateResponse(
            "generator.html",
            {
                "request": request,
                "scan": scan,
                "error": str(e),
                "result": None,
                "payload_preview": None,
                "avatars": avatars,
                "templates_list": templates_list,
                "selected_avatar_id": selected_avatar_id,
                "selected_template_id": selected_template_id,
            },
            status_code=400,
        )


@app.post("/generate-web", response_class=HTMLResponse)
def generate_web(
    request: Request,
    source_url: str = Form(...),
    payload_json: str = Form(...),
    selected_template_id: str = Form(generowanie.TEMPLATE_ID),
):
    payload: dict = {}
    try:
        payload = json.loads(payload_json)
        if _request_is_localhost(request):
            payload.pop("callback_url", None)
            payload["webhook_enabled"] = False
        template_id = _extract_template_id_from_form_or_payload(selected_template_id, payload)
        wynik = generowanie.submit_payload(payload, template_id=template_id)
        scan = generowanie.scan_webpage(source_url)
        selected_avatar_id = _extract_avatar_id_from_payload(payload)
        return templates.TemplateResponse(
            "generator.html",
            {
                "request": request,
                "scan": scan,
                "error": None,
                "result": wynik,
                "payload_preview": json.dumps(payload, indent=2, ensure_ascii=False),
                "avatars": _load_avatars_safe(),
                "templates_list": _load_templates_safe(),
                "selected_avatar_id": selected_avatar_id,
                "selected_template_id": template_id,
            },
        )
    except Exception as e:
        scan = None
        try:
            scan = generowanie.scan_webpage(source_url)
        except Exception:
            pass
        selected_avatar_id = _extract_avatar_id_from_payload(payload if isinstance(payload, dict) else {})
        return templates.TemplateResponse(
            "generator.html",
            {
                "request": request,
                "scan": scan,
                "error": str(e),
                "result": None,
                "payload_preview": None,
                "avatars": _load_avatars_safe(),
                "templates_list": _load_templates_safe(),
                "selected_avatar_id": selected_avatar_id,
                "selected_template_id": selected_template_id or generowanie.TEMPLATE_ID,
            },
            status_code=400,
        )


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
