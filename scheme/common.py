import hashlib
from tinyec import registry
import secrets

def get_curve(name='secp256r1'):
    return registry.get_curve(name)

# Public Parameters
CURVE = get_curve()
G = CURVE.g  # Generator of the elliptic curve group
ORDER = CURVE.field.n  # Order of the curve
DELTA_T = 10  # Timestamp validity period in seconds

def h(data):
    
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha256(data).digest()[:20]  # Truncate to 160 bits

def int_to_bytes(i, length=None):
    
    if length is None:
        return i.to_bytes((i.bit_length() + 7) // 8, 'big')
    return i.to_bytes(length, 'big')

def bytes_to_int(b):
    
    return int.from_bytes(b, 'big')

def xor_bytes(b1, b2):
    
    if len(b1) != len(b2):
        raise ValueError(f"XOR requires equal length inputs: {len(b1)} != {len(b2)}")
    return bytes(a ^ b for a, b in zip(b1, b2))

def random_nonce(length=20):
    
    return secrets.token_bytes(length)

def pad_to_length(data, length):
    
    if isinstance(data, str):
        data = data.encode('utf-8')
    if len(data) >= length:
        return data[:length]
    return data + b'\x00' * (length - len(data))
