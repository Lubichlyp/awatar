import argparse
import json
import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
TEMPLATE_ID = os.getenv("TEMPLATE_ID", "c4504470f364407b847459b12b291436")
AVATAR_ID = os.getenv("AVATAR_ID", "Annie_Casual_Standing_Front_2_public")
VOICE_ID = os.getenv("VOICE_ID")
HEYGEN_WEBHOOK_URL = os.getenv("HEYGEN_WEBHOOK_URL", "").strip()
HEYGEN_TEST_MODE = os.getenv("HEYGEN_TEST_MODE", "true").lower() == "true"
HEYGEN_IMAGE_FIT = os.getenv("HEYGEN_IMAGE_FIT", "cover")
SHORT_TEST_TEXT = "Test."
PLACEHOLDER_IMAGE = "https://assets.aws.londynek.net/images/jdnews/2523317/370275-202311091558-lg.jpg.webp?t=1699545571.000000"

CLEANR = re.compile(r"<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});")

HEADERS = {
    "accept": "application/json",
    "content-type": "application/json",
    "x-api-key": API_KEY,
}
TEMPLATE_DEFINITION_CACHE: dict[str, dict[str, Any]] = {}
LAST_PAYLOAD_PATH = Path("data_settings/lat-payload.json")


def split_into_n_parts(text: str, n: int) -> list[str]:
    if not text:
        return [""] * n

    parts = re.split(r'(?<=[.!?]) +', text)
    parts = [p.strip() for p in parts if p.strip()]

    if len(parts) <= n:
        # za mało zdań -> duplikuj
        while len(parts) < n:
            parts.append(parts[-1])
        return parts[:n]

    # równy podział
    chunk_size = len(parts) // n
    remainder = len(parts) % n

    result = []
    start = 0

    for i in range(n):
        extra = 1 if i < remainder else 0
        end = start + chunk_size + extra
        result.append(" ".join(parts[start:end]))
        start = end

    return result

def build_payload_dynamic(
    full_script: str,
    images: list[str],
    title: str,
    subtitle: str,
    template_id: str | None = None,
    avatar_id: str | None = None,
):
    variable_map = get_template_variable_map(template_id)

    # liczba scen z template
    n = get_scene_count(variable_map)
    scripts = split_into_n_parts(full_script, n)

    variables = {}

    script_vars = sorted(
        [v for v in variable_map["text"] if v.lower().startswith("script")]
    )
    for i, var_name in enumerate(script_vars):
        variables[var_name] = {
            "name": var_name,
            "type": "text",
            "properties": {"content": scripts[i] if i < len(scripts) else ""},
        }

    for var_name in variable_map["text"]:
        lower = var_name.lower()
        if "title" in lower and var_name not in variables:
            variables[var_name] = {
                "name": var_name,
                "type": "text",
                "properties": {"content": title},
            }
        elif "subtitle" in lower and var_name not in variables:
            variables[var_name] = {
                "name": var_name,
                "type": "text",
                "properties": {"content": subtitle},
            }


    image_vars = variable_map["image"]
    assigned_images = _map_image_urls_for_vars(
        image_vars=image_vars,
        selected_images=images,
        fallback_url=PLACEHOLDER_IMAGE,
    )
    for var_name, img_url in assigned_images.items():
        variables[var_name] = {
            "name": var_name,
            "type": "image",
            "properties": {
                "url": img_url,
                "fit": "contain" if "logo" in var_name.lower() else HEYGEN_IMAGE_FIT,
            },
        }

    character_var = _select_character_var(variable_map["character"])
    if character_var:
        variables[character_var] = {
            "name": character_var,
            "type": "character",
            "properties": {
                "character_id": avatar_id or AVATAR_ID,
                "type": "avatar",
            },
        }

    return {
        "test": HEYGEN_TEST_MODE,
        "caption": False,
        "title": title,
        "variables": variables,
    }



def get_scene_count(variable_map: dict[str, list[str]]) -> int:
    script_vars = [
        name for name in variable_map["text"]
        if name.lower().startswith("script")
    ]

    return len(script_vars) if script_vars else 1


def _template_generate_url(template_id: str | None = None) -> str:
    return f"https://api.heygen.com/v2/template/{template_id or TEMPLATE_ID}/generate"


def _template_detail_url(template_id: str | None = None) -> str:
    return f"https://api.heygen.com/v2/template/{template_id or TEMPLATE_ID}"


def cleanhtml(raw_html: str) -> str:
    return re.sub(CLEANR, "", raw_html or "")


def sprawdz_obraz(url: str) -> bool:
    try:
        r = requests.get(url, stream=True, timeout=5)
        return r.status_code == 200
    except requests.RequestException:
        return False


def _extract_ids(payload: Any, known_keys: tuple[str, ...]) -> set[str]:
    found: set[str] = set()
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in known_keys and value:
                found.add(str(value))
            found.update(_extract_ids(value, known_keys))
    elif isinstance(payload, list):
        for item in payload:
            found.update(_extract_ids(item, known_keys))
    return found


def _validate_id_via_endpoint(
    endpoint: str,
    expected_id: str,
    known_keys: tuple[str, ...],
    label: str,
) -> None:
    response = requests.get(endpoint, headers=HEADERS, timeout=15)
    if response.status_code != 200:
        raise RuntimeError(f"Dry-run: błąd walidacji {label}: {response.status_code} {response.text}")

    ids = _extract_ids(response.json(), known_keys)
    if expected_id not in ids:
        raise RuntimeError(f"Dry-run: {label} '{expected_id}' nie istnieje lub nie jest dostępny dla API key.")


def _normalize_template_var_type(node: dict[str, Any], parent_key: str = "") -> str:
    properties = node.get("properties", {}) if isinstance(node, dict) else {}
    if isinstance(properties, dict):
        if "character_id" in properties:
            return "character"
        if "url" in properties or "image_url" in properties:
            return "image"
        if "content" in properties or "text" in properties:
            return "text"

    raw = " ".join(
        str(node.get(key, "")).lower()
        for key in (
            "type",
            "var_type",
            "variable_type",
            "data_type",
            "input_type",
            "category",
            "name",
            "variable_name",
            "var_name",
            "key",
            "id",
            "label",
        )
    )
    raw = f"{raw} {str(parent_key).lower()} {str(node.get('name', '')).lower()}"
    if "character" in raw or "avatar" in raw:
        return "character"
    if "text" in raw or "subtitle" in raw or "title" in raw or "script" in raw or "caption" in raw or "content" in raw:
        return "text"
    if "image" in raw or "photo" in raw or "logo" in raw or "background" in raw or "media" in raw:
        return "image"
    return ""


def _extract_template_variables(payload: Any) -> list[dict[str, str]]:
    variables: list[dict[str, str]] = []
    reserved_keys = {"properties", "property", "props", "config", "metadata", "settings", "style", "data"}

    def walk(node: Any, parent_key: str = "") -> None:
        if isinstance(node, dict):
            node_name = str(
                node.get("name")
                or node.get("variable_name")
                or node.get("var_name")
                or node.get("key")
                or parent_key
                or ""
            ).strip()
            node_type = _normalize_template_var_type(node, parent_key)
            parent_key_l = str(parent_key).lower()
            if (
                node_name
                and node_type in {"image", "text", "character"}
                and parent_key_l not in reserved_keys
                and node_name.lower() not in reserved_keys
            ):
                variables.append({"name": node_name, "type": node_type})
            for key, value in node.items():
                walk(value, str(key))
        elif isinstance(node, list):
            for item in node:
                walk(item, parent_key)

    walk(payload)
    unique: list[dict[str, str]] = []
    seen: set[str] = set()
    for var in variables:
        key = f"{var['type']}::{var['name']}"
        if key in seen:
            continue
        seen.add(key)
        unique.append(var)
    return unique


def get_template_definition(template_id: str | None = None) -> dict[str, Any]:
    tpl_id = template_id or TEMPLATE_ID
    if tpl_id in TEMPLATE_DEFINITION_CACHE:
        return TEMPLATE_DEFINITION_CACHE[tpl_id]

    response = requests.get(_template_detail_url(tpl_id), headers=HEADERS, timeout=20)
    if response.status_code != 200:
        raise RuntimeError(f"Błąd pobierania definicji template '{tpl_id}': {response.status_code} {response.text}")
    data = response.json()
    TEMPLATE_DEFINITION_CACHE[tpl_id] = data
    return data


def get_template_variable_map(template_id: str | None = None) -> dict[str, list[str]]:
    detail = get_template_definition(template_id)
    grouped = {"image": [], "text": [], "character": []}

    # Najpierw preferuj oficjalną strukturę data.variables (dict) zwracaną przez HeyGen.
    vars_node = detail.get("data", {}).get("variables") if isinstance(detail, dict) else None
    if isinstance(vars_node, dict):
        for key, var in vars_node.items():
            if not isinstance(var, dict):
                continue
            var_name = str(var.get("name") or key or "").strip()
            var_type = str(var.get("type") or "").strip().lower()
            if var_type in grouped and var_name:
                grouped[var_type].append(var_name)
        # jeżeli udało się zebrać cokolwiek, nie używaj heurystyk rekurencyjnych
        if any(grouped.values()):
            return grouped

    # Fallback: heurystyczne szukanie dla innych wariantów odpowiedzi API
    vars_list = _extract_template_variables(detail)
    grouped = {"image": [], "text": [], "character": []}
    for var in vars_list:
        grouped[var["type"]].append(var["name"])
    return grouped


def dry_run_validate_ids(
    avatar_id: str | None = None,
    template_id: str | None = None,
) -> None:
    print("Dry-run: walidacja template_id, avatar_id i voice_id...")
    expected_template_id = template_id or TEMPLATE_ID
    template_validated = False
    template_errors: list[str] = []
    for endpoint in ("https://api.heygen.com/v2/templates", "https://api.heygen.com/v2/template"):
        try:
            _validate_id_via_endpoint(
                endpoint=endpoint,
                expected_id=expected_template_id,
                known_keys=("template_id", "id"),
                label="template_id",
            )
            template_validated = True
            break
        except RuntimeError as exc:
            template_errors.append(str(exc))

    if not template_validated:
        joined_errors = " | ".join(template_errors)
        raise RuntimeError(f"Dry-run: nie udało się zwalidować template_id. Szczegóły: {joined_errors}")

    variable_map = get_template_variable_map(expected_template_id)

    # Część template'ów ma stałe pola (bez variables) - nie blokujemy na tym dry-run.
    if variable_map["character"]:
        _validate_id_via_endpoint(
            endpoint="https://api.heygen.com/v2/avatars",
            expected_id=avatar_id or AVATAR_ID,
            known_keys=("avatar_id", "character_id", "id"),
            label="avatar_id",
        )
    if VOICE_ID:
        _validate_id_via_endpoint(
            endpoint="https://api.heygen.com/v1/voice_list",
            expected_id=VOICE_ID,
            known_keys=("voice_id", "id"),
            label="voice_id",
        )
    print("Dry-run: walidacja OK")


def generuj_wideo(image_urls: str, tytul: str, tresc: str, podtytul: str) -> requests.Response:
    payload = build_payload_dynamic(
        full_script=tresc,
        images=image_urls,
        title=tytul,
        subtitle=podtytul,
        avatar_id=AVATAR_ID,
    )

    return requests.post(_template_generate_url(), json=payload, headers=HEADERS, timeout=30)


def build_payload(
    url_obrazka: str,
    tytul: str,
    tresc: str,
    podtytul: str,
    avatar_id: str | None = None,
    template_id: str | None = None,
    selected_images: list[str] | None = None,
) -> dict[str, Any]:
    variable_map = get_template_variable_map(template_id)
    image_vars = variable_map["image"]
    character_var = _select_character_var(variable_map["character"])
    text_vars = variable_map["text"]

    variables: dict[str, Any] = {}
    payload = {
        "test": HEYGEN_TEST_MODE,
        "caption": False,
        "title": "TEST",
        "variables": variables,
    }
    image_urls = _map_image_urls_for_vars(
        image_vars=image_vars,
        selected_images=selected_images or [url_obrazka],
        fallback_url=url_obrazka,
    )
    for var_name, image_url in image_urls.items():
        variables[var_name] = {
            "name": var_name,
            "type": "image",
            "properties": {
                "url": image_url,
                "fit": "contain" if "logo" in var_name.lower() else HEYGEN_IMAGE_FIT,
            },
        }
    if character_var:
        variables[character_var] = {
            "name": character_var,
            "type": "character",
            "properties": {
                "character_id": avatar_id or AVATAR_ID,
                "type": "avatar",
            },
        }

    text_mapping = _build_text_mapping(text_vars, tytul=tytul, tresc=tresc, podtytul=podtytul)

    for var_name, content in text_mapping:
        variables[var_name] = {
            "name": var_name,
            "type": "text",
            "properties": {"content": content},
        }

    return payload


def list_avatars() -> list[dict[str, str]]:
    response = requests.get("https://api.heygen.com/v2/avatars", headers=HEADERS, timeout=20)
    if response.status_code != 200:
        raise RuntimeError(f"Błąd pobierania awatarów: {response.status_code} {response.text}")

    data = response.json()
    avatars: list[dict[str, str]] = []
    seen_ids: set[str] = set()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            avatar_id = str(node.get("avatar_id") or node.get("character_id") or node.get("id") or "").strip()
            if avatar_id and avatar_id not in seen_ids:
                seen_ids.add(avatar_id)
                avatar_name = str(node.get("avatar_name") or node.get("name") or node.get("title") or avatar_id)
                thumbnail = str(
                    node.get("preview_image_url")
                    or node.get("image_url")
                    or node.get("thumbnail_url")
                    or ""
                )
                avatars.append({"id": avatar_id, "name": avatar_name, "thumbnail": thumbnail})
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)
    if not avatars:
        return [{"id": AVATAR_ID, "name": AVATAR_ID, "thumbnail": ""}]
    return sorted(avatars, key=lambda a: a["name"].lower())


def list_templates() -> list[dict[str, str]]:
    errors: list[str] = []
    data: Any = None
    for endpoint in ("https://api.heygen.com/v2/templates", "https://api.heygen.com/v2/template"):
        response = requests.get(endpoint, headers=HEADERS, timeout=20)
        if response.status_code == 200:
            data = response.json()
            break
        errors.append(f"{endpoint}: {response.status_code}")

    if data is None:
        raise RuntimeError(f"Błąd pobierania szablonów: {' | '.join(errors)}")

    templates: list[dict[str, str]] = []
    seen_ids: set[str] = set()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            template_id = str(node.get("template_id") or node.get("id") or "").strip()
            if template_id and template_id not in seen_ids:
                seen_ids.add(template_id)
                template_name = str(node.get("template_name") or node.get("name") or node.get("title") or template_id)
                templates.append({"id": template_id, "name": template_name})
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)
    if not templates:
        return [{"id": TEMPLATE_ID, "name": TEMPLATE_ID}]
    return sorted(templates, key=lambda t: t["name"].lower())


def is_localhost_url(url: str) -> bool:
    try:
        parsed = urlparse((url or "").strip())
    except Exception:
        return False
    host = (parsed.hostname or "").lower()
    return host in {"localhost", "127.0.0.1", "::1"}


def _attach_webhook_to_payload(payload: dict[str, Any], source_url: str | None) -> None:
    if not HEYGEN_WEBHOOK_URL:
        return
    if source_url and is_localhost_url(source_url):
        return
    payload["callback_url"] = HEYGEN_WEBHOOK_URL


def submit_payload(payload: dict[str, Any], template_id: str | None = None) -> dict[str, Any]:
    payload_to_send = dict(payload)
    payload_to_send.pop("selected_images", None)
    payload_to_send.pop("webhook_enabled", None)
    payload_to_send.pop("template_id_selected", None)
    payload_to_send.pop("script_input", None)
    wynik = requests.post(
        _template_generate_url(template_id),
        json=payload_to_send,
        headers=HEADERS,
        timeout=30,
    )
    if wynik.status_code != 200:
        raise RuntimeError(f"Błąd HeyGen: {wynik.status_code} {wynik.text}")
    return wynik.json()


def _save_last_payload(payload: dict[str, Any]) -> None:
    LAST_PAYLOAD_PATH.parent.mkdir(parents=True, exist_ok=True)
    LAST_PAYLOAD_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _extract_logo_urls_from_payload(payload: dict[str, Any]) -> set[str]:
    urls: set[str] = set()
    variables = payload.get("variables", {})
    if not isinstance(variables, dict):
        return urls

    for var_name, var_data in variables.items():
        if "logo" not in str(var_name).lower():
            continue
        if not isinstance(var_data, dict):
            continue
        if str(var_data.get("type", "")).lower() != "image":
            continue
        url = str(var_data.get("properties", {}).get("url", "")).strip()
        if url:
            urls.add(url)
    return urls


def scan_webpage(url: str, max_texts: int = 20, max_images: int = 12) -> dict[str, Any]:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("URL musi zaczynać się od http:// lub https://")

    response = requests.get(
        url,
        timeout=20,
        headers={"User-Agent": "awatar-bot/1.0 (+https://example.local)"},
    )
    if response.status_code != 200:
        raise RuntimeError(f"Nie udało się pobrać strony: {response.status_code}")

    content_type = response.headers.get("content-type", "")
    if "html" not in content_type.lower():
        raise RuntimeError("Podany URL nie zwrócił dokumentu HTML.")

    soup = BeautifulSoup(response.text, "html.parser")
    for tag_name in ("script", "style", "noscript"):
        for tag in soup.find_all(tag_name):
            tag.decompose()

    raw_title = (soup.title.string or "").strip() if soup.title else ""
    page_title = raw_title or parsed.netloc

    texts: list[dict[str, str]] = []
    seen_texts: set[str] = set()
    for tag in soup.find_all(["h1", "h2", "h3", "p", "li"]):
        text = " ".join(tag.get_text(" ", strip=True).split())
        if len(text) < 45:
            continue
        if text in seen_texts:
            continue
        seen_texts.add(text)
        texts.append(
            {
                "id": str(len(texts)),
                "full": text,
                "preview": text[:220] + ("..." if len(text) > 220 else ""),
            }
        )
        if len(texts) >= max_texts:
            break

    images: list[dict[str, Any]] = []
    seen_images: set[str] = set()
    for img in soup.find_all("img"):
        src = (img.get("src") or img.get("data-src") or "").strip()
        if not src or src.startswith("data:"):
            continue
        absolute = urljoin(response.url, src)
        if absolute in seen_images:
            continue
        seen_images.add(absolute)
        alt = " ".join((img.get("alt") or "").split())[:120]
        images.append(
            {
                "id": str(len(images)),
                "url": absolute,
                "alt": alt,
                "preview": absolute[:120] + ("..." if len(absolute) > 120 else ""),
                "is_logo": "logo" in absolute.lower() or "logo" in alt.lower(),
            }
        )
        if len(images) >= max_images:
            break

    images.sort(key=lambda image: (not image["is_logo"]))

    return {
        "source_url": response.url,
        "title": page_title,
        "texts": texts,
        "images": images,
    }


def generate_from_selection(
    *,
    source_url: str,
    selected_texts: list[str],
    selected_images: list[str],
    script_text: str | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    selected_avatar_id: str | None = None,
    selected_template_id: str | None = None,
    dry_run: bool = True,
    short_test: bool = True,
) -> dict[str, Any]:
    if not selected_texts and not (script_text and script_text.strip()):
        raise ValueError("Wybierz co najmniej jeden fragment tekstu lub wpisz własny skrypt.")

    if dry_run:
        dry_run_validate_ids(
            avatar_id=selected_avatar_id,
            template_id=selected_template_id,
        )

    script = build_script(selected_texts, short_test, script_text)
    if not script:
        script = SHORT_TEST_TEXT

    image_var_name = _preferred_image_var_name(selected_template_id)
    prefer_logo = "logo" in image_var_name.lower()
    image_url = _get_primary_image(selected_images, prefer_logo=prefer_logo)

    video_title = (title or "").strip() or f"Wideo z {source_url}"
    video_subtitle = (subtitle or "").strip() or video_title

    payload = build_payload_dynamic(
        url_obrazka=image_url,
        tytul=video_title,
        tresc=script,
        podtytul=video_subtitle,
        avatar_id=selected_avatar_id,
        template_id=selected_template_id,
        selected_images=selected_images,
    )
    
    _attach_webhook_to_payload(payload, source_url)
    _save_last_payload(payload)
    return submit_payload(payload, template_id=selected_template_id)


def build_script(selected_texts: list[str], short_test: bool, script_text: str | None = None) -> str:
    if script_text and script_text.strip():
        base = " ".join(script_text.split())
        return base[:260] if short_test else base[:1850]

    cleaned = [" ".join((text or "").split()) for text in selected_texts if (text or "").strip()]
    if not cleaned:
        return SHORT_TEST_TEXT
    if short_test:
        return cleaned[0][:260]
    return " ".join(cleaned)[:1850]


def _prioritize_logo_images(image_urls: list[str]) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for url in image_urls:
        value = (url or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        unique.append(value)
    return sorted(unique, key=lambda url: ("logo" not in url.lower(),))


def _select_preferred_image_var(image_vars: list[str]) -> str:
    if not image_vars:
        return ""
    exact_priorities = ["background", "image", "photo", "cover", "hero", "logo"]
    for preferred in exact_priorities:
        for name in image_vars:
            if name.strip().lower() == preferred:
                return name
    weighted = sorted(
        image_vars,
        key=lambda name: (
            "background" not in name.lower(),
            "cover" not in name.lower(),
            "hero" not in name.lower(),
            "logo" in name.lower(),
        ),
    )
    return weighted[0]


def _select_character_var(character_vars: list[str]) -> str:
    if not character_vars:
        return ""
    for preferred in ("avatar", "speaker", "character"):
        for name in character_vars:
            if name.strip().lower() == preferred:
                return name
    weighted = sorted(
        character_vars,
        key=lambda name: (
            "avatar" not in name.lower() and "character" not in name.lower() and "speaker" not in name.lower(),
            "background" in name.lower() or "logo" in name.lower(),
        ),
    )
    return weighted[0]


def _build_text_mapping(text_vars: list[str], *, tytul: str, tresc: str, podtytul: str) -> list[tuple[str, str]]:
    if not text_vars:
        return []

    normalized = {name.strip().lower(): name for name in text_vars}
    mapping: list[tuple[str, str]] = []
    used: set[str] = set()

    preferred_pairs = [
        ("script", tresc),
        ("title_text", tytul),
        ("subtitle_text", podtytul),
        ("title", tytul),
        ("subtitle", podtytul),
    ]
    for preferred_name, content in preferred_pairs:
        actual_name = normalized.get(preferred_name)
        if not actual_name or actual_name in used:
            continue
        mapping.append((actual_name, content))
        used.add(actual_name)

    if mapping:
        return mapping

    if len(text_vars) >= 3:
        return [
            (text_vars[0], tytul),
            (text_vars[1], tresc),
            (text_vars[2], podtytul),
        ]
    if len(text_vars) == 2:
        return [
            (text_vars[0], tytul),
            (text_vars[1], tresc),
        ]
    return [(text_vars[0], tresc)]


def _map_image_urls_for_vars(
    image_vars: list[str],
    selected_images: list[str],
    fallback_url: str,
) -> dict[str, str]:
    if not image_vars:
        return {}

    ordered = _prioritize_logo_images(selected_images)
    if not ordered:
        ordered = [fallback_url]

    assigned = {}

    for i, var_name in enumerate(image_vars):
        assigned[var_name] = ordered[i % len(ordered)]

    return assigned

def _get_primary_image(selected_images: list[str], prefer_logo: bool = False) -> str:
    ordered = _prioritize_logo_images(selected_images)
    logos = [image_url for image_url in ordered if "logo" in image_url.lower()]
    non_logo = [image_url for image_url in ordered if "logo" not in image_url.lower()]

    if prefer_logo:
        for image_url in logos:
            if sprawdz_obraz(image_url):
                return image_url

    for image_url in non_logo:
        if sprawdz_obraz(image_url):
            return image_url

    for image_url in ordered:
        if sprawdz_obraz(image_url):
            return image_url
    return PLACEHOLDER_IMAGE


def _preferred_image_var_name(template_id: str | None = None) -> str:
    variable_map = get_template_variable_map(template_id)
    return _select_preferred_image_var(variable_map["image"])


def _format_var_list(var_names: list[str]) -> str:
    if not var_names:
        return "brak"
    return ", ".join(sorted(var_names))


def _validate_template_selection_compatibility(
    *,
    template_id: str | None,
    selected_images: list[str],
    script: str,
) -> None:
    variable_map = get_template_variable_map(template_id)
    image_vars = variable_map["image"]
    text_vars = variable_map["text"]

    errors: list[str] = []
    if script.strip() and not text_vars:
        errors.append(
            "Template nie ma żadnej zmiennej typu text, więc skrypt nie może zostać "
            "podmieniony przez API. W HeyGen otwórz pole skryptu avatara i dodaj do niego API Variable."
        )

    non_logo_selected = [url for url in selected_images if "logo" not in url.lower()]
    non_logo_image_vars = [name for name in image_vars if "logo" not in name.lower()]
    if non_logo_selected and not non_logo_image_vars:
        errors.append(
            "Template nie ma żadnej zmiennej obrazka tła/zdjęcia poza logo, więc wybrane obrazy "
            "nie wpłyną na wideo. Dodaj w HeyGen API Variable do backgroundu albo warstwy image/video."
        )

    if errors:
        raise ValueError(
            "Wybrany template nie pasuje do danych z formularza.\n"
            f"- dostępne text vars: {_format_var_list(text_vars)}\n"
            f"- dostępne image vars: {_format_var_list(image_vars)}\n"
            f"- dostępne character vars: {_format_var_list(variable_map['character'])}\n"
            + "\n".join(f"- {item}" for item in errors)
        )


def build_payload_from_selection(
    *,
    source_url: str,
    selected_texts: list[str],
    selected_images: list[str],
    script_text: str | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    selected_avatar_id: str | None = None,
    selected_template_id: str | None = None,
    dry_run: bool = True,
    short_test: bool = True,
) -> dict[str, Any]:
    if not selected_texts and not (script_text and script_text.strip()):
        raise ValueError("Wybierz co najmniej jeden fragment tekstu lub wpisz własny skrypt.")

    if dry_run:
        dry_run_validate_ids(
            avatar_id=selected_avatar_id,
            template_id=selected_template_id,
        )

    script = build_script(selected_texts, short_test, script_text)
    ordered_images = _prioritize_logo_images(selected_images)
    _validate_template_selection_compatibility(
        template_id=selected_template_id,
        selected_images=ordered_images,
        script=script,
    )
    image_var_name = _preferred_image_var_name(selected_template_id)
    prefer_logo = "logo" in image_var_name.lower()
    image_url = _get_primary_image(ordered_images, prefer_logo=prefer_logo)

    video_title = (title or "").strip() or f"Wideo z {source_url}"
    video_subtitle = (subtitle or "").strip() or video_title

    scripts = split_into_n_parts(script)

    variables = {}

    variables["script1"] = {
        "name": "script1",
        "type": "text",
        "properties": {"content": scripts[0]},
    }

    variables["script2"] = {
        "name": "script2",
        "type": "text",
        "properties": {"content": scripts[1]},
    }

    variables["subtitle_"] = {
        "name": "subtitle_",
        "type": "text",
        "properties": {"content": video_subtitle},
    }

    variables["image_"] = {
        "name": "image_",
        "type": "image",
        "properties": {"url": image_url, "fit": "cover"},
    }

    variables["background_"] = {
        "name": "background_",
        "type": "character",
        "properties": {
            "character_id": selected_avatar_id or AVATAR_ID,
            "type": "avatar",
        },
    }

    payload = {
        "test": HEYGEN_TEST_MODE,
        "caption": False,
        "title": video_title,
        "variables": variables,
}
    if script.strip():
        payload["script_input"] = script
    _attach_webhook_to_payload(payload, source_url)
    logo_urls = _extract_logo_urls_from_payload(payload)
    payload["selected_images"] = [url for url in ordered_images if url not in logo_urls]
    payload["template_id_selected"] = selected_template_id or TEMPLATE_ID
    payload["webhook_enabled"] = "callback_url" in payload
    _save_last_payload(payload)
    print(json.dumps(payload, indent=2))
    return payload

# https://londynek.net/api/get-data?hash=F8047E46311596755B6AE4B09C54D346B2DD712F&limit=1&sql_where=and%20ja.jdnews_id%3D4807783&select_fields=news_content,movie_p,movie,headline,headline_en,title,title_en

def run(
    article_id: int,
    dry_run: bool = True,
    short_test: bool = True,
    request_origin: str | None = None,
) -> dict[str, Any]:
    endpoint = (
        "https://londynek.net/api/get-data?hash=F8047E46311596755B6AE4B09C54D346B2DD712F"
        f"&limit=1&sql_where=and%20ja.jdnews_id%3D{article_id}"
        "&select_fields=news_content,movie_p,movie,headline,headline_en,title,title_en"
    )
    response = requests.get(endpoint, timeout=15)

    if response.status_code != 200:
        raise RuntimeError(f"Błąd pobierania danych: {response.status_code} {response.text}")

    dane = response.json()
    if not dane.get("data"):
        raise RuntimeError("Brak danych artykułu dla podanego ID.")

    event = dane["data"][0]
    images = event.get("images", [])
    obraz_url = PLACEHOLDER_IMAGE

    image_urls = []
    for image in images:
        image_url = image.get("url", "").replace("/image/", "images/")
        file_name = image.get("file_name", "")
        print(file_name)
        image["file_name"] = f"https://assets.aws.londynek.net/{image_url}/{file_name}"
        print(image["file_name"])
        if sprawdz_obraz(image["file_name"]):
            image_urls.append(image["file_name"])

    if len(images) > 1 and images[1].get("file_name"):
        obraz_url = images[1]["file_name"]
    elif len(images) > 0 and images[0].get("file_name"):
        obraz_url = images[0]["file_name"]

    if not sprawdz_obraz(obraz_url):
        print("Obraz nie działa, używam placeholdera")
        obraz_url = PLACEHOLDER_IMAGE

    pelny_skrypt = f"{event.get('headline', '')}. {cleanhtml(event.get('news_content', ''))[:1850]}".strip()
    if short_test:
        pelny_skrypt = pelny_skrypt[:210] if pelny_skrypt else SHORT_TEST_TEXT

    dane_do_filmu = {
        "obraz": obraz_url,
        "tytul": event.get("title") or "Test.",
        "skrypt": pelny_skrypt or "T",
        "podtytul": event.get("title_en") or event.get("title") or "Test",
    }

    if dry_run:
        dry_run_validate_ids(avatar_id=AVATAR_ID, template_id=TEMPLATE_ID)

    payload = build_payload_dynamic(
    full_script=dane_do_filmu["skrypt"],
    images=image_urls if image_urls else [dane_do_filmu["obraz"]],
    title=dane_do_filmu["tytul"],
    subtitle=dane_do_filmu["podtytul"],
    avatar_id=AVATAR_ID,
    )
    # CLI/API po news_id nie jest lokalnym renderem, webhook może być dołączony jeśli skonfigurowany.
    _attach_webhook_to_payload(payload, request_origin or endpoint)
    _save_last_payload(payload)
    wynik_json = submit_payload(payload, template_id=TEMPLATE_ID)
    video_id = wynik_json.get("data", {}).get("video_id")
    if video_id:
        print(f"Sukces! ID: {video_id}")
    return wynik_json


parser = argparse.ArgumentParser(description="Generator wideo na podstawie ID artykułu.")
parser.add_argument("--id", type=int, required=True, help="ID artykułu (np. 12345)")
parser.add_argument(
    "--dry-run",
    action=argparse.BooleanOptionalAction,
    default=True,
    help="Włącz/wyłącz walidację IDs przez API HeyGen przed generowaniem (domyślnie: włączona).",
)
parser.add_argument(
    "--short-test",
    action=argparse.BooleanOptionalAction,
    default=True,
    help="Włącz/wyłącz krótki skrypt testowy (domyślnie: włączony).",
)


if __name__ == "__main__":
    args = parser.parse_args()
    print("Podane ID:", args.id)
    wynik = run(args.id, dry_run=args.dry_run, short_test=args.short_test)
    print(wynik)