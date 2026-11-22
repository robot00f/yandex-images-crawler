import hashlib
import html
import io
import json
import logging
import re
import threading
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path
from typing import Dict, FrozenSet, List, Optional, Set, Tuple, Union
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse

import requests
from PIL import Image

requests.packages.urllib3.disable_warnings()

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/130.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

IMAGE_DOWNLOAD_HEADERS = {
    "User-Agent": DEFAULT_HEADERS["User-Agent"],
    "Referer": "https://yandex.com/",
}

BLACKLIST_HOSTS = (
    "yandex-images",
    "avatars.mds.yandex.net",
)


def is_captcha_response(response: requests.Response) -> bool:
    url_lower = response.url.lower()
    if "showcaptcha" in url_lower or "/captcha" in url_lower:
        return True
    if len(response.text) < 40000:
        body_lower = response.text.lower()
        if (
            "smartcaptcha" in body_lower
            or "captcha__image" in body_lower
            or "are you not a robot" in body_lower
            or "вы не робот" in body_lower
        ):
            return True
    return False


def _extract_img_url_from_query(url_str: str) -> Optional[str]:
    try:
        vals = parse_qs(urlparse(url_str).query).get("img_url")
        if vals and vals[0].startswith("http"):
            return vals[0]
    except Exception:
        pass
    return None


def _is_blacklisted(url: str) -> bool:
    return any(b in url for b in BLACKLIST_HOSTS)


def _extract_entity_image(
    entity: dict,
) -> Optional[Tuple[str, Optional[int], Optional[int]]]:
    url = None
    orig_url = entity.get("origUrl")
    if isinstance(orig_url, str) and orig_url.startswith("http"):
        url = orig_url

    viewer_data = entity.get("viewerData") or {}
    if not url and isinstance(viewer_data, dict):
        img_href = viewer_data.get("img_href")
        if isinstance(img_href, str) and img_href.startswith("http"):
            url = img_href

        if not url:
            for preview in viewer_data.get("preview") or []:
                if isinstance(preview, dict):
                    p_url = preview.get("url")
                    if isinstance(p_url, str) and p_url.startswith("http"):
                        url = p_url
                        break

    if not url:
        rel_url = entity.get("url")
        if isinstance(rel_url, str):
            url = _extract_img_url_from_query(rel_url)

    if not url or _is_blacklisted(url):
        return None

    width = entity.get("origWidth") or entity.get("width")
    height = entity.get("origHeight") or entity.get("height")
    try:
        width = int(width) if width is not None else None
        height = int(height) if height is not None else None
    except (TypeError, ValueError):
        width, height = None, None

    return (url, width, height)


def extract_images_from_html(
    page_html: str, page_url: str
) -> Tuple[List[Tuple[str, Optional[int], Optional[int]]], Optional[str], bool]:
    items: List[Tuple[str, Optional[int], Optional[int]]] = []
    seen: Set[str] = set()
    next_page_url: Optional[str] = None
    is_empty_page = False

    # Include img_url if the starting URL points directly to an open preview
    direct_img = _extract_img_url_from_query(page_url)
    if direct_img and not _is_blacklisted(direct_img):
        seen.add(direct_img)
        items.append((direct_img, None, None))

    # Primary parser: Yandex SSR Redux state (initialState.serpList)
    for raw_state in re.findall(r'data-state="([^"]+)"', page_html):
        try:
            obj = json.loads(html.unescape(raw_state))
        except Exception:
            continue
        if not isinstance(obj, dict) or "initialState" not in obj:
            continue

        serp_list = (obj.get("initialState") or {}).get("serpList")
        if not isinstance(serp_list, dict):
            continue

        is_empty_page = bool(serp_list.get("isEmptyPage", False))

        navi = serp_list.get("navi")
        if isinstance(navi, dict) and isinstance(navi.get("next"), str):
            next_page_url = urljoin(page_url, navi["next"])

        serp_items = serp_list.get("items") or {}
        entities = serp_items.get("entities") or {}
        ordered_keys = serp_items.get("keys") or list(entities.keys())

        for key in ordered_keys:
            entity = entities.get(key)
            if not isinstance(entity, dict):
                continue
            parsed = _extract_entity_image(entity)
            if parsed and parsed[0] not in seen:
                seen.add(parsed[0])
                items.append(parsed)

    # Fallback parser: regex extraction of img_url query parameters in HTML
    if not items:
        for encoded in re.findall(r'img_url=([^&"\'\s<>]+)', page_html):
            decoded = html.unescape(encoded)
            try:
                from urllib.parse import unquote

                decoded = unquote(decoded)
            except Exception:
                pass
            if (
                decoded.startswith("http")
                and not _is_blacklisted(decoded)
                and decoded not in seen
            ):
                seen.add(decoded)
                items.append((decoded, None, None))

    return items, next_page_url, is_empty_page


def _build_next_page_url(current_url: str, page_index: int) -> str:
    parsed = urlparse(current_url)
    query = parse_qs(parsed.query, keep_blank_values=True)
    query["p"] = [str(page_index)]
    new_query = urlencode(query, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


def download_http(
    links: List[str],
    image_size: Tuple[int, int],
    image_count: int,
    image_dir: Union[str, Path],
    skip_files: FrozenSet[str],
    loaders_per_link: int = 1,
    page_delay: float = 1.0,
) -> Dict[str, object]:
    """
    Lightweight pure-HTTP Yandex Images crawler and downloader.
    Runs in a single Python process with a bounded thread pool (no browser/Selenium).
    """
    logger = logging.getLogger("yandex_http_crawler")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(levelname)s - %(asctime)s - %(message)s")
        )
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    out_dir = Path(image_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    min_width, min_height = image_size

    existing_count = sum(1 for p in out_dir.iterdir() if p.is_file())
    lock = threading.Lock()
    stop_event = threading.Event()
    known_hashes: Set[str] = set(skip_files)
    seen_urls: Set[str] = set()
    state = {
        "total_in_dir": existing_count,
        "downloaded": 0,
        "captcha_hit": False,
    }

    if image_count > 0 and existing_count >= image_count:
        logger.info("The required number of images is reached.")
        return {
            "downloaded": 0,
            "total_in_dir": existing_count,
            "reached_target": True,
            "captcha_hit": False,
            "remaining_links": [],
        }

    download_session = requests.Session()
    download_session.headers.update(IMAGE_DOWNLOAD_HEADERS)

    def fetch_and_save(
        img_url: str, width: Optional[int], height: Optional[int]
    ) -> None:
        if stop_event.is_set():
            return
        if (
            width is not None
            and height is not None
            and (width < min_width or height < min_height)
        ):
            return

        logger.info(img_url)
        try:
            resp = download_session.get(img_url, verify=False, timeout=10)
        except Exception:
            return

        if not (200 <= resp.status_code < 300):
            return

        try:
            with Image.open(io.BytesIO(resp.content)) as img:
                actual_w, actual_h = img.size
                if actual_w < min_width or actual_h < min_height:
                    return
                hash_name = hashlib.sha256(img.tobytes()).hexdigest()
                img_path = out_dir / f"{hash_name}.png"
                rgb_img = img.convert("RGB")

            with lock:
                if stop_event.is_set():
                    return
                if image_count > 0 and state["total_in_dir"] >= image_count:
                    stop_event.set()
                    return
                if hash_name in known_hashes or img_path.exists():
                    return
                known_hashes.add(hash_name)
                state["downloaded"] += 1
                state["total_in_dir"] += 1
                if image_count > 0 and state["total_in_dir"] >= image_count:
                    stop_event.set()
                    logger.info("The required number of images is reached.")

            try:
                rgb_img.save(img_path, "PNG")
            except Exception:
                with lock:
                    state["downloaded"] -= 1
                    state["total_in_dir"] -= 1
                return
        except Exception:
            return

    max_workers = max(2, min(16, len(links) * max(2, loaders_per_link)))
    remaining_links: List[str] = []

    try:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for link_idx, start_link in enumerate(links):
                if stop_event.is_set():
                    break

                page_session = requests.Session()
                page_session.headers.update(DEFAULT_HEADERS)
                current_url: Optional[str] = start_link
                page_num = 0
                pending_futures = set()
                link_hit_captcha = False

                try:
                    while current_url and not stop_event.is_set():
                        if page_num > 0 and page_delay > 0:
                            time.sleep(page_delay)
                            if stop_event.is_set():
                                break

                        try:
                            resp = page_session.get(current_url, timeout=15)
                        except Exception as exc:
                            logger.warning(
                                f"Link #{link_idx} page {page_num} request failed: {exc}"
                            )
                            break

                        if is_captcha_response(resp):
                            logger.warning(
                                f"Link #{link_idx} hit Yandex CAPTCHA on page {page_num}."
                            )
                            state["captcha_hit"] = True
                            link_hit_captcha = True
                            break

                        if not (200 <= resp.status_code < 300):
                            logger.warning(
                                f"Link #{link_idx} page {page_num} returned HTTP {resp.status_code}."
                            )
                            break

                        items, next_url, is_empty = extract_images_from_html(
                            resp.text, resp.url
                        )

                        new_items = []
                        for img_url, w, h in items:
                            if img_url not in seen_urls:
                                seen_urls.add(img_url)
                                new_items.append((img_url, w, h))

                        if not new_items:
                            logger.info(
                                f"Link #{link_idx} page {page_num}: no new images found."
                            )
                            break

                        for img_url, w, h in new_items:
                            if stop_event.is_set():
                                break
                            # Keep bounded number of in-flight downloads to stay low-RAM
                            while len(pending_futures) >= max_workers * 3:
                                done, pending_futures = wait(
                                    pending_futures,
                                    timeout=0.5,
                                    return_when=FIRST_COMPLETED,
                                )
                                if stop_event.is_set():
                                    break
                            if not stop_event.is_set():
                                pending_futures.add(
                                    executor.submit(fetch_and_save, img_url, w, h)
                                )

                        # Drain current page's downloads before fetching the next Yandex page
                        # so we avoid unnecessary page requests if --count is reached!
                        while pending_futures and not stop_event.is_set():
                            done, pending_futures = wait(
                                pending_futures,
                                timeout=0.5,
                                return_when=FIRST_COMPLETED,
                            )

                        if stop_event.is_set() or is_empty:
                            break

                        page_num += 1
                        if next_url and next_url != current_url:
                            current_url = next_url
                        else:
                            current_url = _build_next_page_url(start_link, page_num)

                    # Wait for any remaining in-flight tasks for this link
                    if pending_futures:
                        for fut in pending_futures:
                            if stop_event.is_set():
                                fut.cancel()
                        wait(pending_futures)
                finally:
                    page_session.close()

                if link_hit_captcha and not stop_event.is_set():
                    remaining_links.append(start_link)
    finally:
        download_session.close()

    reached_target = bool(image_count > 0 and state["total_in_dir"] >= image_count)
    return {
        "downloaded": state["downloaded"],
        "total_in_dir": state["total_in_dir"],
        "reached_target": reached_target,
        "captcha_hit": state["captcha_hit"],
        "remaining_links": remaining_links,
    }
