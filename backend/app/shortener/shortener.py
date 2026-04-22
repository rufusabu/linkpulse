import base64

def shorten_url(url: str):
    url_bytes = url.encode("utf-8")
    b64_bytes = base64.b64encode(url_bytes)
    b64_string = b64_bytes.decode("utf-8")

    return b64_string
