import secrets
import string

# Base-62 alphabet: a-z A-Z 0-9
_ALPHABET = string.ascii_letters + string.digits
_CODE_LENGTH = 7


def generate_code(length: int = _CODE_LENGTH) -> str:
    """Return a cryptographically random base-62 short code.

    With length=7 and a 62-char alphabet this gives 62^7 ≈ 3.5 trillion
    possible codes — collision probability is negligible even at millions
    of URLs.
    """
    return "".join(secrets.choice(_ALPHABET) for _ in range(length))
