from urllib.request import urlopen

DEFAULT_TITLE = "No title"


def fetch_page_title(url: str):
    """El servidor descarga la pgina y devuelve su <title>"""
    try:
        with urlopen(url, timeout=5) as response:
            html = response.read(100_000).decode("utf-8", errors="ignore")
    except Exception:
        return DEFAULT_TITLE

    # The page has no title if it lacks the opening or the closing tag.
    if "<title>" not in html or "</title>" not in html:
        return DEFAULT_TITLE

    after_open_tag = html.split("<title>")[1]

    title = after_open_tag.split("</title>")[0]
    return title.strip()[:255] or DEFAULT_TITLE
