from pwdlib import PasswordHash

pin_hash = PasswordHash.recommended()

def hash_pin(pin: str) -> str:
    return pin_hash.hash(pin)

def verify_pin(pin: str, hashed_pin: str) -> bool:
    return pin_hash.verify(pin, hashed_pin)