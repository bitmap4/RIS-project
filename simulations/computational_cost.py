"""
Calculate computational costs for the authentication phase.
"""
from typing import Dict


def calculate_computational_cost(benchmark_results: Dict[str, float], cfg) -> Dict[str, float]:
    """
    Calculate computational cost for each entity and total.
    
    Args:
        benchmark_results: Dictionary with benchmark times (T_h, T_pa, T_ed, T_sm, T_bp)
        cfg: Hydra configuration
        
    Returns:
        Dictionary with costs for each entity and total
    """
    T_h = benchmark_results['T_h']
    T_sm = benchmark_results['T_sm']
    
    comp_cfg = cfg.evaluation.computational_cost
    
    # Calculate cost for each entity
    vehicle_cost = (
        comp_cfg.vehicle.hash * T_h +
        comp_cfg.vehicle.scalar_mult * T_sm
    )
    
    fog_node_cost = (
        comp_cfg.fog_node.hash * T_h +
        comp_cfg.fog_node.scalar_mult * T_sm
    )
    
    cloud_server_cost = (
        comp_cfg.cloud_server.hash * T_h +
        comp_cfg.cloud_server.scalar_mult * T_sm
    )
    
    total_cost = vehicle_cost + fog_node_cost + cloud_server_cost
    
    return {
        'vehicle': vehicle_cost,
        'fog_node': fog_node_cost,
        'cloud_server': cloud_server_cost,
        'total': total_cost,
        'breakdown': {
            'T_h': T_h,
            'T_sm': T_sm,
            'total_hash_ops': (
                comp_cfg.vehicle.hash +
                comp_cfg.fog_node.hash +
                comp_cfg.cloud_server.hash
            ),
            'total_scalar_mult_ops': (
                comp_cfg.vehicle.scalar_mult +
                comp_cfg.fog_node.scalar_mult +
                comp_cfg.cloud_server.scalar_mult
            )
        }
    }


def print_computational_cost(results: Dict[str, float]):
    """Print computational cost results in a formatted way."""
    print("\n" + "="*60)
    print("COMPUTATIONAL COST ANALYSIS")
    print("="*60)
    
    print(f"\nOperation Benchmarks:")
    print(f"  Hash (T_h):              {results['breakdown']['T_h']:.4f} ms")
    print(f"  Scalar Mult (T_sm):      {results['breakdown']['T_sm']:.4f} ms")
    
    print(f"\nOperation Counts:")
    print(f"  Total Hash operations:   {results['breakdown']['total_hash_ops']}")
    print(f"  Total Scalar Mult:       {results['breakdown']['total_scalar_mult_ops']}")
    
    print(f"\nEntity Costs:")
    print(f"  Vehicle (V_i):           {results['vehicle']:.4f} ms")
    print(f"  Fog Node (F_j):          {results['fog_node']:.4f} ms")
    print(f"  Cloud Server (CS):       {results['cloud_server']:.4f} ms")
    
    print(f"\n{'-'*60}")
    print(f"  TOTAL COST:              {results['total']:.4f} ms")
    print(f"{'-'*60}\n")
