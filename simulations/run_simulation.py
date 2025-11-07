"""
Main simulation runner for performance evaluation.
"""
import hydra
from omegaconf import DictConfig, OmegaConf
import json
from pathlib import Path
import sys

from simulations.benchmarks import run_benchmarks
from simulations.computational_cost import calculate_computational_cost, print_computational_cost
from simulations.communication_cost import calculate_communication_cost, print_communication_cost


@hydra.main(version_base=None, config_path="configs", config_name="config")
def main(cfg: DictConfig):
    """
    Main simulation entry point.
    
    Args:
        cfg: Hydra configuration
    """
    device_name = cfg.device.name
    device_type = cfg.device.type
    
    print("\n" + "="*60)
    print("PERFORMANCE EVALUATION SIMULATION")
    print(f"Device: {device_name} ({device_type})")
    print(f"CPU: {cfg.device.specs.cpu}")
    print(f"RAM: {cfg.device.specs.ram}")
    print("="*60 + "\n")
    
    # 1. Run benchmarks
    print("Phase 1: Benchmarking atomic operations...")
    benchmark_results = run_benchmarks(cfg)
    
    print(f"\nBenchmark Results for {device_name}:")
    for op, time_ms in benchmark_results.items():
        print(f"  {op}: {time_ms:.6f} ms")
    
    # 2. Calculate computational cost
    print("\nPhase 2: Calculating computational costs...")
    comp_cost = calculate_computational_cost(benchmark_results, cfg)
    print_computational_cost(comp_cost)
    
    # 3. Calculate communication cost
    print("Phase 3: Calculating communication costs...")
    comm_cost = calculate_communication_cost(cfg)
    print_communication_cost(comm_cost, cfg)
    
    # 4. Save results
    output_dir = Path(cfg.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {
        'device': {
            'name': device_name,
            'type': device_type,
            'specs': OmegaConf.to_container(cfg.device.specs, resolve=True)
        },
        'benchmarks': benchmark_results,
        'computational_cost': {
            'vehicle_ms': comp_cost['vehicle'],
            'fog_node_ms': comp_cost['fog_node'],
            'cloud_server_ms': comp_cost['cloud_server'],
            'total_ms': comp_cost['total'],
            'breakdown': comp_cost['breakdown']
        },
        'communication_cost': {
            'M1_bits': comm_cost['M1'],
            'M2_bits': comm_cost['M2'],
            'M3_bits': comm_cost['M3'],
            'M4_bits': comm_cost['M4'],
            'total_bits': comm_cost['total_bits'],
            'total_bytes': comm_cost['total_bytes'],
            'total_kb': comm_cost['total_kb']
        },
        'configuration': OmegaConf.to_container(cfg, resolve=True)
    }
    
    output_file = output_dir / f"simulation_results_{device_type}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    print("\n" + "="*60)
    print("SIMULATION COMPLETE")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
