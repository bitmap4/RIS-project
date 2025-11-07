import hashlib
from tinyec import registry
import secrets

def get_curve(name='secp256r1'):
    """Get a named elliptic curve."""
    return registry.get_curve(name)

# Public Parameters
CURVE = get_curve()
G = CURVE.g  # Generator of the elliptic curve group
ORDER = CURVE.field.n  # Order of the curve
DELTA_T = 10  # Timestamp validity period in seconds

def h(data):
    """A cryptographic one-way hash function. Returns 160 bits (20 bytes)."""
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha256(data).digest()[:20]  # Truncate to 160 bits

def int_to_bytes(i, length=None):
    """Convert an integer to bytes. If length specified, pads/truncates to that length."""
    if length is None:
        return i.to_bytes((i.bit_length() + 7) // 8, 'big')
    return i.to_bytes(length, 'big')

def bytes_to_int(b):
    """Convert bytes to an integer."""
    return int.from_bytes(b, 'big')

def xor_bytes(b1, b2):
    """XOR two byte strings. Must be same length."""
    if len(b1) != len(b2):
        raise ValueError(f"XOR requires equal length inputs: {len(b1)} != {len(b2)}")
    return bytes(a ^ b for a, b in zip(b1, b2))

def random_nonce(length=20):
    """Generate a random nonce. Default 160 bits (20 bytes)."""
    return secrets.token_bytes(length)

def pad_to_length(data, length):
    """Pad data to specified length with zeros."""
    if isinstance(data, str):
        data = data.encode('utf-8')
    if len(data) >= length:
        return data[:length]
    return data + b'\x00' * (length - len(data))
