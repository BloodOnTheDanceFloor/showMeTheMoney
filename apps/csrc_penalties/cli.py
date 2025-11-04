import argparse
import os
import re
import time
from typing import Dict, List, Optional

import requests


CNINFO_SEARCH_URL = "http://www.cninfo.com.cn/new/fulltextSearch/full"
CNINFO_STATIC_PREFIX = "http://static.cninfo.com.cn/"


def sanitize_filename(name: str) -> str:
    # Remove illegal filesystem characters for Windows
    name = re.sub(r"[\\/:*?\"<>|]", "_", name)
    # Trim whitespace
    name = name.strip()
    # Limit length to avoid very long filenames
    return name[:180] if len(name) > 180 else name


def extract_year_from_fields(item: Dict) -> Optional[str]:
    # Try various fields to determine year
    for key in ("announcementTime", "publishDate", "pubDate"):
        if key in item and item[key]:
            val = str(item[key])
            # Unix ms timestamp
            if val.isdigit() and len(val) >= 10:
                try:
                    ts = int(val)
                    # If seconds, ts ~ 1e9; if ms, ts ~ 1e12
                    if ts > 10**11:
                        ts //= 1000
                    year = time.strftime("%Y", time.localtime(ts))
                    return year
                except Exception:
                    pass
            # ISO date string
            m = re.match(r"(\d{4})-(\d{2})-(\d{2})", val)
            if m:
                return m.group(1)

    # Try adjunct url path like /finalpage/2023-08-24/xxxxx.PDF
    for key in ("adjunctUrl", "attachPath", "pdfUrl"):
        path = item.get(key)
        if isinstance(path, str):
            m = re.search(r"/(\d{4})-(\d{2})-(\d{2})/", path)
            if m:
                return m.group(1)

    return None


def build_headers() -> Dict[str, str]:
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/119.0.0.0 Safari/537.36"
        ),
        "Referer": "http://www.cninfo.com.cn/new/commonQuery/",
        "Accept": "application/json, text/javascript, */*; q=0.01",
    }


def search_page(query: str, page_num: int, page_size: int = 20) -> Dict:
    params = {
        "searchkey": query,
        "isfulltext": "false",
        "sortfield": "pubdate",
        "sorttype": "desc",
        "pageNum": page_num,
        "pageSize": page_size,
    }
    resp = requests.get(CNINFO_SEARCH_URL, params=params, headers=build_headers(), timeout=20)
    resp.raise_for_status()
    return resp.json()


def extract_download_url(item: Dict) -> Optional[str]:
    # Known field: adjunctUrl, sometimes starts with finalpage/...
    for key in ("adjunctUrl", "attachPath", "pdfUrl"):
        path = item.get(key)
        if isinstance(path, str) and path:
            # If already absolute
            if path.startswith("http://") or path.startswith("https://"):
                return path
            # Otherwise prepend static host
            return CNINFO_STATIC_PREFIX + path.lstrip("/")
    return None


def download_file(url: str, out_path: str, delay: float) -> bool:
    try:
        with requests.get(url, headers=build_headers(), timeout=60, stream=True) as r:
            r.raise_for_status()
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        if delay > 0:
            time.sleep(delay)
        return True
    except Exception as e:
        print(f"[WARN] Failed to download {url}: {e}")
        return False


def run(query: str, out_dir: str, max_pages: Optional[int], page_size: int, delay: float, skip_existing: bool) -> None:
    print(f"[INFO] Querying cninfo for: {query}")
    page = 1
    total_downloads = 0

    while True:
        if max_pages is not None and page > max_pages:
            break
        try:
            data = search_page(query, page, page_size)
        except Exception as e:
            print(f"[ERROR] Search request failed on page {page}: {e}")
            break

        # Results structure may include 'announcements'
        items: List[Dict] = data.get("announcements") or data.get("classifiedAnnouncements") or []
        if not items:
            print(f"[INFO] No items on page {page}. Stopping.")
            break

        print(f"[INFO] Page {page}: {len(items)} items")
        for item in items:
            title = item.get("announcementTitle") or item.get("title") or "untitled"
            title = sanitize_filename(title)
            year = extract_year_from_fields(item) or "unknown"
            url = extract_download_url(item)

            if not url:
                print(f"[SKIP] No attachment URL for: {title}")
                continue

            # Guess extension from URL
            ext = ".pdf"
            m = re.search(r"\.(pdf|PDF|doc|docx|zip|rar)$", url)
            if m:
                ext = "." + m.group(1).lower()

            out_path = os.path.join(out_dir, year, f"{title}{ext}")
            if skip_existing and os.path.exists(out_path):
                print(f"[SKIP] Exists: {out_path}")
                continue

            ok = download_file(url, out_path, delay)
            if ok:
                total_downloads += 1

        page += 1

    print(f"[DONE] Total downloaded: {total_downloads}")


def main():
    parser = argparse.ArgumentParser(
        description="下载‘证监会行政处罚决定书’并按年份分类保存"
    )
    parser.add_argument(
        "--query",
        default="证监会行政处罚决定书",
        help="搜索关键词（默认：证监会行政处罚决定书）",
    )
    parser.add_argument(
        "--out",
        default=os.path.join("apps", "csrc_penalties", "downloads"),
        help="输出目录（默认：apps/csrc_penalties/downloads）",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="最多抓取的页数（默认：全部直到无数据）",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=20,
        help="每页数量（默认：20，受接口限制）",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="每次下载后的延迟秒数（默认：0.5，避免过快请求）",
    )
    parser.add_argument(
        "--no-skip-existing",
        action="store_true",
        help="不跳过已存在文件（默认跳过）",
    )

    args = parser.parse_args()
    skip_existing = not args.no_skip_existing

    run(
        query=args.query,
        out_dir=args.out,
        max_pages=args.max_pages,
        page_size=args.page_size,
        delay=args.delay,
        skip_existing=skip_existing,
    )


if __name__ == "__main__":
    main()