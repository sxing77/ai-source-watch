from __future__ import annotations

import hashlib
import os
import re
import time
from dataclasses import dataclass, field
from typing import Iterable
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .items import WatchItem


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36 ai-source-watch/0.1"
)


@dataclass
class SourceResult:
    items: list[WatchItem] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def fetch_replicate_models(limit: int = 20) -> SourceResult:
    token = os.getenv("REPLICATE_API_TOKEN", "").strip()
    if not token:
        return SourceResult(
            warnings=[
                "Replicate skipped: set REPLICATE_API_TOKEN in .env or environment."
            ]
        )

    url = "https://api.replicate.com/v1/models"
    headers = {"Authorization": f"Bearer {token}", "User-Agent": "ai-source-watch/0.1"}
    params = {
        "sort_by": "model_created_at",
        "sort_direction": "desc",
    }

    response = requests.get(url, headers=headers, params=params, timeout=30)
    if response.status_code == 401:
        return SourceResult(warnings=["Replicate skipped: API token was rejected."])
    response.raise_for_status()
    data = response.json()

    raw_items = data.get("results", data if isinstance(data, list) else [])
    items: list[WatchItem] = []
    for model in raw_items[:limit]:
        owner = str(model.get("owner", "")).strip()
        name = str(model.get("name", "")).strip()
        if not owner or not name:
            continue

        full_name = f"{owner}/{name}"
        page_url = str(model.get("url") or f"https://replicate.com/{full_name}")
        items.append(
            WatchItem(
                source="replicate",
                external_id=full_name,
                name=full_name,
                url=page_url,
                description=str(model.get("description") or "").strip(),
                category=str(model.get("visibility") or ""),
                published_at=str(model.get("created_at") or ""),
                raw=model,
            )
        )
    return SourceResult(items=items)


def fetch_toolify_new(
    limit: int = 30,
    url: str = "https://www.toolify.ai/zh/new",
    use_browser: bool = True,
) -> SourceResult:
    warnings: list[str] = []
    html = ""

    # 1. 首选：Jina AI Reader（绕过 Cloudflare）
    try:
        html = _fetch_html_jina(url)
        if html:
            warnings.append("Toolify fetched via Jina AI Reader successfully.")
    except Exception as exc:
        warnings.append(f"Toolify Jina fetch failed: {exc}")

    # 2. 回退：直接 requests 抓取
    if not html:
        try:
            html = _fetch_html_requests(url)
        except Exception as exc:
            warnings.append(f"Toolify direct fetch failed: {exc}")

        if _looks_like_cloudflare(html):
            warnings.append("Toolify direct fetch hit a Cloudflare challenge.")
            html = ""

    # 3. 兜底：Playwright 浏览器渲染
    if not html and use_browser:
        try:
            html = _fetch_html_playwright(url)
        except Exception as exc:
            warnings.append(f"Toolify browser fetch failed: {exc}")
        if _looks_like_cloudflare(html):
            warnings.append("Toolify browser fetch still hit a Cloudflare challenge.")
            html = ""

    if not html:
        return SourceResult(warnings=warnings or ["Toolify skipped: no HTML returned."])

    items = _parse_toolify_new(html, base_url=url, limit=limit)
    if not items:
        warnings.append("Toolify returned HTML, but no new-tool cards were parsed.")
    return SourceResult(items=items, warnings=warnings)


def _fetch_html_jina(url: str) -> str:
    """Use Jina AI Reader to fetch content, bypassing Cloudflare."""
    jina_url = f"https://r.jina.ai/{url}"
    response = requests.get(
        jina_url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/plain,text/html,*/*",
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.text


def _fetch_html_requests(url: str) -> str:
    response = requests.get(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.text


def _fetch_html_playwright(url: str) -> str:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent=USER_AGENT,
            locale="zh-CN",
            viewport={"width": 1365, "height": 900},
        )
        page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        # Respect the site's crawl-delay and give client rendering/challenges a moment.
        time.sleep(6)
        html = page.content()
        browser.close()
        return html


def _looks_like_cloudflare(html: str) -> bool:
    if not html:
        return False
    lowered = html.lower()
    return "challenge-error-text" in lowered or "cf_chl" in lowered


def _parse_toolify_new(html: str, base_url: str, limit: int) -> list[WatchItem]:
    soup = BeautifulSoup(html, "html.parser")
    candidates: list[WatchItem] = []
    seen_ids: set[str] = set()

    for link in soup.find_all("a", href=True):
        href = str(link["href"]).strip()
        absolute_url = urljoin(base_url, href)
        if not _is_toolify_tool_url(absolute_url):
            continue

        text = _clean_text(link.get_text(" ", strip=True))
        container = _best_tool_card_container(link)
        card_text = _clean_text(container.get_text(" ", strip=True) if container else text)
        name = _extract_tool_name(text, card_text, absolute_url)
        if not name:
            continue

        description = _extract_description(card_text, name)
        external_id = _stable_toolify_id(absolute_url, name)
        if external_id in seen_ids:
            continue
        seen_ids.add(external_id)

        candidates.append(
            WatchItem(
                source="toolify",
                external_id=external_id,
                name=name,
                url=absolute_url,
                description=description,
                category="new-ai-tool",
                raw={"href": href, "card_text": card_text[:1500]},
            )
        )
        if len(candidates) >= limit:
            break

    return candidates


def _is_toolify_tool_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.netloc and parsed.netloc != "www.toolify.ai":
        return False
    path = parsed.path.lower()
    if any(part in path for part in ["/tool/", "/zh/tool/", "/ai-tool/", "/zh/ai-tool/"]):
        return True
    return False


def _best_tool_card_container(link) -> object | None:
    current = link
    for _ in range(5):
        current = current.parent
        if current is None:
            return None
        text = _clean_text(current.get_text(" ", strip=True))
        if len(text) >= 20:
            return current
    return link.parent


def _extract_tool_name(link_text: str, card_text: str, url: str) -> str:
    for candidate in (link_text, card_text):
        lines = [line.strip() for line in re.split(r"[\r\n]+", candidate) if line.strip()]
        for line in lines:
            normalized = _clean_text(line)
            if normalized and normalized.lower() not in {"image", "free"}:
                return normalized[:160]

    slug = urlparse(url).path.rstrip("/").split("/")[-1]
    return slug.replace("-", " ").strip().title()


def _extract_description(card_text: str, name: str) -> str:
    text = card_text.replace(name, " ", 1)
    text = re.sub(r"\b(Image|Free|Paid|Freemium)\b", " ", text, flags=re.I)
    text = _clean_text(text)
    if len(text) > 400:
        text = text[:397].rstrip() + "..."
    return text


def _stable_toolify_id(url: str, name: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    if path:
        return path.lower()
    digest = hashlib.sha256(name.encode("utf-8")).hexdigest()[:16]
    return f"name:{digest}"


def merge_results(results: Iterable[SourceResult]) -> SourceResult:
    merged = SourceResult()
    for result in results:
        merged.items.extend(result.items)
        merged.warnings.extend(result.warnings)
    return merged
