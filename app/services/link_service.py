from urllib.request import Request, urlopen

DEFAULT_TITLE = "No title"

# Algunas webs (WAF) rechazan con 406 al user-agent por defecto de Python, así que imitamos un navegador.
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}


def fetch_page_title(url: str):
    """El servidor descarga la pgina y devuelve su <title>"""
    try:
        with urlopen(Request(url, headers=BROWSER_HEADERS), timeout=5) as response:
            html = response.read(100_000).decode("utf-8", errors="ignore")
    except Exception:
        return DEFAULT_TITLE

    # The page has no title if it lacks the opening or the closing tag.
    open_tag = html.find("<title")
    close_tag = html.find("</title>")
    if open_tag == -1 or close_tag == -1:
        return DEFAULT_TITLE

    # La etiqueta de apertura puede traer saltos de línea o atributos, así que el texto empieza tras su ">".
    text_start = html.find(">", open_tag) + 1
    title = html[text_start:close_tag]
    # split/join quita los saltos de línea y espacios repetidos de dentro del título.
    return " ".join(title.split())[:255] or DEFAULT_TITLE
