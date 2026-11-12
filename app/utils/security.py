import bcrypt


@staticmethod
def hash_password (password: str) -> str:
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

@staticmethod
def verify_password(password:str, hashed:str)->bool:
    password_bytes = password.encode('utf-8')
    hash = hashed.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hash)
    
    