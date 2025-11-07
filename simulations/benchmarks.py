import time
import secrets
from typing import Dict
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from tinyec import registry
import statistics


class CryptoBenchmark:
    def __init__(self, iterations: int = 10, data_size: int = 32):
        self.iterations = iterations
        self.data_size = data_size
        self.curve = registry.get_curve('secp256r1')
        self.G = self.curve.g
        # Get the field order from the curve's field
        self.order = self.curve.field.n
        
    def benchmark_hash(self) -> float:
        
        times = []
        data = secrets.token_bytes(self.data_size)
        
        for _ in range(self.iterations):
            start = time.perf_counter()
            digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
            digest.update(data)
            digest.finalize()
            end = time.perf_counter()
            times.append((end - start) * 1000)  # Convert to ms
        
        return statistics.mean(times)
    
    def benchmark_point_addition(self) -> float:
        
        times = []
        # Generate two random points
        k1 = secrets.randbelow(self.order)
        k2 = secrets.randbelow(self.order)
        P1 = k1 * self.G
        P2 = k2 * self.G
        
        for _ in range(self.iterations):
            start = time.perf_counter()
            _ = P1 + P2
            end = time.perf_counter()
            times.append((end - start) * 1000)
        
        return statistics.mean(times)
    
    def benchmark_symmetric_encryption(self) -> float:
        
        times = []
        key = secrets.token_bytes(32)  # 256-bit key
        data = secrets.token_bytes(self.data_size)
        
        for _ in range(self.iterations):
            iv = secrets.token_bytes(16)
            cipher = Cipher(
                algorithms.AES(key),
                modes.CBC(iv),
                backend=default_backend()
            )
            
            start = time.perf_counter()
            encryptor = cipher.encryptor()
            # Pad data to block size
            padded_data = data + b'\x00' * (16 - len(data) % 16)
            ct = encryptor.update(padded_data) + encryptor.finalize()
            
            decryptor = cipher.decryptor()
            pt = decryptor.update(ct) + decryptor.finalize()
            end = time.perf_counter()
            times.append((end - start) * 1000)
        
        return statistics.mean(times)
    
    def benchmark_scalar_multiplication(self) -> float:
        
        times = []
        k = secrets.randbelow(self.order)
        
        for _ in range(self.iterations):
            start = time.perf_counter()
            _ = k * self.G
            end = time.perf_counter()
            times.append((end - start) * 1000)
        
        return statistics.mean(times)
    
    def benchmark_bilinear_pairing(self) -> float:
        times = []
        k1 = secrets.randbelow(self.order)
        k2 = secrets.randbelow(self.order)
        
        for _ in range(self.iterations):
            start = time.perf_counter()
            # Simulate expensive pairing operation
            P1 = k1 * self.G
            P2 = k2 * self.G
            _ = P1 + P2
            end = time.perf_counter()
            times.append((end - start) * 1000)
        
        return statistics.mean(times)
    
    def run_all_benchmarks(self) -> Dict[str, float]:
        
        print(f"Running benchmarks with {self.iterations} iterations...")
        
        results = {
            'T_h': self.benchmark_hash(),
            'T_pa': self.benchmark_point_addition(),
            'T_ed': self.benchmark_symmetric_encryption(),
            'T_sm': self.benchmark_scalar_multiplication(),
            'T_bp': self.benchmark_bilinear_pairing(),
        }
        
        return results


def run_benchmarks(cfg) -> Dict[str, float]:
    
    benchmark = CryptoBenchmark(
        iterations=cfg.benchmark.iterations,
        data_size=cfg.benchmark.data_size
    )
    return benchmark.run_all_benchmarks()
