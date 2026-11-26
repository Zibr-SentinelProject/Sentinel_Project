import bcrypt

# Whitelist of the extensions that can be uploaded, with the type we store for each one.
# Anything not listed here is rejected (a whitelist, never a blacklist).
ALLOWED_EXTENSIONS = {
"txt": "text/plain",
"log": "text/plain",
"pdf": "application/pdf",
"png": "image/png",
"jpg": "image/jpeg",
"jpeg": "image/jpeg",
"pcap": "application/vnd.tcpdump.pcap",
"pcapng": "application/vnd.tcpdump.pcap",
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

