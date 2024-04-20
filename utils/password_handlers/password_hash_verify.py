from passlib.context import CryptContext as _CryptContext

_CRYPT_CONTEXT = _CryptContext(
    schemes=["sha256_crypt", "bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _CRYPT_CONTEXT.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return _CRYPT_CONTEXT.hash(password)
