"""Parse subsidy program info from a URL."""

import re
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# ROC year → Western year
def _roc_to_iso(text: str) -> str | None:
    m = re.search(r"(\d{2,3})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", text)
    if m:
        year = int(m.group(1)) + 1911
        return f"{year}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return None


def _extract_text(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)


def _guess_field(text: str, patterns: list[str]) -> str | None:
    for pat in patterns:
        m = re.search(pat, text, re.DOTALL | re.MULTILINE)
        if m:
            val = m.group(1).strip()
            return val[:500] if val else None
    return None


def parse_subsidy_url(url: str) -> dict:
    """Fetch a URL and extract subsidy program fields.

    Returns dict with keys: name, agency, deadline, deadline_date,
    funding_amount, eligibility, scope, reference_url, raw_text.
    """
    resp = requests.get(url, headers=HEADERS, timeout=15, verify=False)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or "utf-8"

    soup = BeautifulSoup(resp.text, "html.parser")
    text = _extract_text(soup)

    # Title: prefer <h1>, then <title>, then og:title
    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else None
    if not title:
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else None
    if not title:
        og = soup.find("meta", property="og:title")
        title = og["content"] if og and og.get("content") else None

    # Agency
    agency = _guess_field(text, [
        r"主辦[機單]關[：:]\s*(.+?)[\n。]",
        r"辦理單位[：:]\s*(.+?)[\n。]",
        r"執行[單機]位[：:]\s*(.+?)[\n。]",
    ])

    # Deadline
    deadline_text = _guess_field(text, [
        r"(?:申請|收件|受理)(?:截止|期[限間])[：:]\s*(.+?)[\n。]",
        r"截止[日期][：:期]\s*(.+?)[\n。]",
    ])

    deadline_date = None
    if deadline_text:
        deadline_date = _roc_to_iso(deadline_text)

    # Funding
    funding = _guess_field(text, [
        r"(?:補助|獎勵)[金額度上限]*[：:]\s*(.+?)[\n。]",
        r"(?:最高|上限)[補助獎勵]*[：:]*\s*(.+?萬.*?)[\n。]",
    ])

    # Eligibility
    eligibility = _guess_field(text, [
        r"(?:申請|適用)[資對][格象][：:]\s*(.+?)(?:\n\n|\n[一二三四五])",
        r"受理對象[：:]\s*(.+?)[\n。]",
    ])

    # Scope
    scope = _guess_field(text, [
        r"(?:補助|獎勵|申請)範[疇圍][：:]\s*(.+?)(?:\n\n|\n[一二三四五])",
        r"計畫[內範][容疇][：:]\s*(.+?)[\n。]",
    ])

    return {
        "name": (title or "")[:200],
        "agency": (agency or "")[:200],
        "deadline": (deadline_text or "")[:200],
        "deadline_date": deadline_date,
        "funding_amount": (funding or "")[:500],
        "eligibility": (eligibility or "")[:500],
        "scope": (scope or "")[:500],
        "reference_url": url,
        "raw_text": text[:3000],
    }
