"""
Benchmark atomic cryptographic operations.
"""
import time
import hashlib
import secrets
import sys
from pathlib import Path
from typing import Dict

# Add parent directory to path to import scheme module
sys.path.insert(0, str(Path(__file__).parent.parent))

from scheme.common import get_curve
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import hydra
from omegaconf import DictConfig


class CryptoBenchmark:
    """Benchmark cryptographic operations."""
    
    def __init__(self, curve_name: str = 'secp256r1', iterations: int = 10):
        self.curve = get_curve(curve_name)
        self.G = self.curve.g
        self.iterations = iterations
    
    def benchmark_hash(self) -> float:
        """Benchmark hash function (T_h)."""
        data = b"benchmark_data" * 100
        times = []
        
        for _ in range(self.iterations):
            start = time.perf_counter()
            hashlib.sha256(data).digest()
            end = time.perf_counter()
            times.append((end - start) * 1000)  # Convert to milliseconds
        
        return sum(times) / len(times)
    
    def benchmark_ec_point_addition(self) -> float:
        """Benchmark elliptic curve point addition (T_pa)."""
        # Generate random points
        scalar1 = secrets.randbelow(self.curve.field.n)
        scalar2 = secrets.randbelow(self.curve.field.n)
        point1 = scalar1 * self.G
        point2 = scalar2 * self.G
        
        times = []
        for _ in range(self.iterations):
            start = time.perf_counter()
            _ = point1 + point2
            end = time.perf_counter()
            times.append((end - start) * 1000)
        
        return sum(times) / len(times)
    
    def benchmark_symmetric_enc_dec(self) -> float:
        """Benchmark symmetric encryption/decryption (T_ed)."""
        key = get_random_bytes(16)
        data = b"benchmark_data" * 100
        
        times = []
        for _ in range(self.iterations):
            # Encryption
            cipher = AES.new(key, AES.MODE_EAX)
            nonce = cipher.nonce
            start = time.perf_counter()
            ciphertext, tag = cipher.encrypt_and_digest(data)
            
            # Decryption
            cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
            _ = cipher.decrypt_and_verify(ciphertext, tag)
            end = time.perf_counter()
            
            times.append((end - start) * 1000)
        
        return sum(times) / len(times)
    
    def benchmark_ec_scalar_multiplication(self) -> float:
        """Benchmark elliptic curve scalar multiplication (T_sm)."""
        scalar = secrets.randbelow(self.curve.field.n)
        
        times = []
        for _ in range(self.iterations):
            start = time.perf_counter()
            _ = scalar * self.G
            end = time.perf_counter()
            times.append((end - start) * 1000)
        
        return sum(times) / len(times)
    
    def benchmark_bilinear_pairing(self) -> float:
        """
        Benchmark bilinear pairing (T_bp).
        Note: This is a placeholder as bilinear pairings require specialized libraries.
        The proposed scheme doesn't use bilinear pairings, but we include it for completeness.
        """
        # Placeholder - bilinear pairings are not used in the proposed scheme
        return 0.0
    
    def run_all_benchmarks(self) -> Dict[str, float]:
        """Run all benchmarks and return results."""
        print("Running benchmarks...")
        results = {
            'T_h': self.benchmark_hash(),
            'T_pa': self.benchmark_ec_point_addition(),
            'T_ed': self.benchmark_symmetric_enc_dec(),
            'T_sm': self.benchmark_ec_scalar_multiplication(),
            'T_bp': self.benchmark_bilinear_pairing(),
        }
        
        print("\nBenchmark Results (milliseconds):")
        for op, time_ms in results.items():
            print(f"  {op}: {time_ms:.6f} ms")
        
        return results


@hydra.main(version_base=None, config_path="config", config_name="config")
def main(cfg: DictConfig):
    """Main benchmark function."""
    benchmark = CryptoBenchmark(
        curve_name=cfg.benchmark.curve_name,
        iterations=cfg.benchmark.iterations
    )
    
    results = benchmark.run_all_benchmarks()
    
    # Save results
    import json
    import os
    from pathlib import Path
    
    output_dir = Path(cfg.output.results_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "benchmark_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    main()
