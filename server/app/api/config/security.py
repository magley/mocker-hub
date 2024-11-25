import bcrypt

def hash_password(password_plaintext: str) -> str:
    pw = str.encode(password_plaintext)
    return bytes.decode(bcrypt.hashpw(pw, bcrypt.gensalt()))

def verify_password(password_plaintext: str, password_hashed: str) -> bool:
    pw_1 = str.encode(password_plaintext)
    pw_2 = str.encode(password_hashed)
    return bcrypt.checkpw(pw_1, pw_2)