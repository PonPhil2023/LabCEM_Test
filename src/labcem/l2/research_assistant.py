import json
import urllib.parse
import urllib.request


def _fetch_duckduckgo(query, timeout_sec):
    url = "https://api.duckduckgo.com/?" + urllib.parse.urlencode(
        {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1,
        }
    )
    req = urllib.request.Request(url, headers={"User-Agent": "LabCEM/0.1"})
    with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
        payload = json.loads(resp.read().decode("utf-8", errors="ignore"))

    abstract = (payload.get("AbstractText") or "").strip()
    heading = (payload.get("Heading") or "").strip()
    related = payload.get("RelatedTopics") or []
    bullets = []
    for item in related[:5]:
        txt = (item.get("Text") if isinstance(item, dict) else "") or ""
        if txt:
            bullets.append(txt)
    parts = []
    if heading:
        parts.append("Heading: " + heading)
    if abstract:
        parts.append("Abstract: " + abstract)
    if bullets:
        parts.append("Related: " + " | ".join(bullets))
    return "\n".join(parts)


def _fetch_wikipedia_summary(query, timeout_sec):
    url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(
        {
            "action": "opensearch",
            "search": query,
            "limit": 3,
            "namespace": 0,
            "format": "json",
        }
    )
    req = urllib.request.Request(url, headers={"User-Agent": "LabCEM/0.1"})
    with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
        payload = json.loads(resp.read().decode("utf-8", errors="ignore"))

    titles = payload[1] if len(payload) > 1 else []
    descs = payload[2] if len(payload) > 2 else []
    lines = []
    for i, title in enumerate(titles[:3]):
        desc = descs[i] if i < len(descs) else ""
        lines.append("{0}: {1}".format(title, desc))
    return "\n".join(lines)


def fetch_research_context(query, timeout_sec=6):
    q = (query or "").strip()
    if not q:
        return ""

    for fetcher in (_fetch_duckduckgo, _fetch_wikipedia_summary):
        try:
            text = (fetcher(q, timeout_sec) or "").strip()
            if text:
                return text[:1800]
        except Exception:
            continue
    return ""
