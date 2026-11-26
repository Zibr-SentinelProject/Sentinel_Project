import bcrypt

# Whitelist of the files that can be uploaded: extension -> (type we store, valid first bytes).
# Anything not listed here is rejected (a whitelist, never a blacklist).
# The signatures are written here instead of asking libmagic, because libmagic gives different
# MIME types depending on its version (e.g. pcapng). None = plain text, which has no signature.
ALLOWED_TYPES = {
    "pdf": ("application/pdf", (b"%PDF-",)),
    "png": ("image/png", (b"\x89PNG\r\n\x1a\n",)),
    "jpg": ("image/jpeg", (b"\xff\xd8\xff",)),
    "jpeg": ("image/jpeg", (b"\xff\xd8\xff",)),
    "pcap": ("application/vnd.tcpdump.pcap",
             (b"\xd4\xc3\xb2\xa1", b"\xa1\xb2\xc3\xd4",     # microseconds: little / big endian
              b"\x4d\x3c\xb2\xa1", b"\xa1\xb2\x3c\x4d")),   # nanoseconds: little / big endian
    "pcapng": ("application/x-pcapng", (b"\x0a\x0d\x0d\x0a",)),
    "txt": ("text/plain", None),
    "log": ("text/plain", None),
}

@staticmethod
def hash_password (password: str) -> str:
    """Hashes a password with bcrypt, using a new random salt each time.

    The same password gives a different hash on every call, so hashes can only be compared
    with verify_password, never with ==.

    Args:
        password (str): The password in plain text

    Returns:
        str: The bcrypt hash, safe to store in the database
    """
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

@staticmethod
def verify_password(password:str, hashed:str)->bool:
    """Checks a password against a bcrypt hash.

    Args:
        password (str): The password in plain text, as typed by the user
        hashed (str): The hash stored in the database

    Raises:
        ValueError: If hashed is not a valid bcrypt hash (e.g. a plain-text password in the database)

    Returns:
        bool: True if the password matches the hash
    """
    password_bytes = password.encode('utf-8')
    hashed_bytes = hashed.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)

def validate_attachment(filename: str, content: bytes) -> bool:
    """Checks that the extension is allowed and that the real content matches it (magic bytes).

    The type sent by the browser is never used: it is chosen by the user.

    Args:
        filename (str): The original name of the file, only used to read its extension
        content (bytes): The content of the file

    Returns:
        bool: True if the extension is in ALLOWED_TYPES and the content starts with one of its signatures
            (or, for text files, is UTF-8 text without null bytes)
    """
    if not filename or not isinstance(content, bytes) or not content:
        return False

    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in ALLOWED_TYPES:
        return False

    _, signatures = ALLOWED_TYPES[extension]
    if signatures is None:
        # Plain text has no signature: it must be valid UTF-8 and have no null bytes (binary files do).
        try:
            content.decode("utf-8")
        except UnicodeDecodeError:
            return False
        return b"\x00" not in content
    # startswith accepts a tuple: True if the content starts with any of the signatures.
    return content.startswith(signatures)
