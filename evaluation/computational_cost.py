"""
Compute the computational cost of the scheme based on benchmarked operations.
"""
import json
from pathlib import Path
from typing import Dict
import hydra
from omegaconf import DictConfig


class ComputationalCostAnalyzer:
    """Analyze computational costs of the authentication scheme."""
    
    def __init__(self, benchmark_results: Dict[str, float], cost_formulas: DictConfig):
        self.benchmark_results = benchmark_results
        self.cost_formulas = cost_formulas
    
    def calculate_entity_cost(self, entity: str) -> Dict[str, float]:
        """Calculate the computational cost for a specific entity."""
        formula = self.cost_formulas[entity]
        
        cost_breakdown = {
            'hash': formula.hash * self.benchmark_results['T_h'],
            'ec_scalar_mult': formula.ec_scalar_mult * self.benchmark_results['T_sm'],
            'ec_point_add': formula.ec_point_add * self.benchmark_results['T_pa'],
            'sym_enc_dec': formula.sym_enc_dec * self.benchmark_results['T_ed'],
            'bilinear_pairing': formula.bilinear_pairing * self.benchmark_results['T_bp'],
        }
        
        total = sum(cost_breakdown.values())
        
        return {
            'breakdown': cost_breakdown,
            'total_ms': total,
            'formula': {
                'hash': formula.hash,
                'ec_scalar_mult': formula.ec_scalar_mult,
                'ec_point_add': formula.ec_point_add,
                'sym_enc_dec': formula.sym_enc_dec,
                'bilinear_pairing': formula.bilinear_pairing,
            }
        }
    
    def calculate_total_cost(self) -> Dict:
        """Calculate total computational cost across all entities."""
        vehicle_cost = self.calculate_entity_cost('vehicle')
        fog_node_cost = self.calculate_entity_cost('fog_node')
        cloud_server_cost = self.calculate_entity_cost('cloud_server')
        
        total_operations = {
            'hash': (self.cost_formulas.vehicle.hash + 
                    self.cost_formulas.fog_node.hash + 
                    self.cost_formulas.cloud_server.hash),
            'ec_scalar_mult': (self.cost_formulas.vehicle.ec_scalar_mult + 
                              self.cost_formulas.fog_node.ec_scalar_mult + 
                              self.cost_formulas.cloud_server.ec_scalar_mult),
            'ec_point_add': (self.cost_formulas.vehicle.ec_point_add + 
                            self.cost_formulas.fog_node.ec_point_add + 
                            self.cost_formulas.cloud_server.ec_point_add),
            'sym_enc_dec': (self.cost_formulas.vehicle.sym_enc_dec + 
                           self.cost_formulas.fog_node.sym_enc_dec + 
                           self.cost_formulas.cloud_server.sym_enc_dec),
            'bilinear_pairing': (self.cost_formulas.vehicle.bilinear_pairing + 
                                self.cost_formulas.fog_node.bilinear_pairing + 
                                self.cost_formulas.cloud_server.bilinear_pairing),
        }
        
        total_time = (vehicle_cost['total_ms'] + 
                     fog_node_cost['total_ms'] + 
                     cloud_server_cost['total_ms'])
        
        return {
            'vehicle': vehicle_cost,
            'fog_node': fog_node_cost,
            'cloud_server': cloud_server_cost,
            'total': {
                'operations': total_operations,
                'time_ms': total_time,
                'formula_string': f"{total_operations['hash']}T_h + {total_operations['ec_scalar_mult']}T_sm"
            }
        }
    
    def print_results(self, results: Dict):
        """Print computational cost results in a readable format."""
        print("\n" + "="*70)
        print("COMPUTATIONAL COST ANALYSIS")
        print("="*70)
        
        for entity in ['vehicle', 'fog_node', 'cloud_server']:
            entity_data = results[entity]
            print(f"\n{entity.upper().replace('_', ' ')}:")
            print(f"  Formula: ", end="")
            formula = entity_data['formula']
            parts = []
            if formula['hash'] > 0:
                parts.append(f"{formula['hash']}T_h")
            if formula['ec_scalar_mult'] > 0:
                parts.append(f"{formula['ec_scalar_mult']}T_sm")
            if formula['ec_point_add'] > 0:
                parts.append(f"{formula['ec_point_add']}T_pa")
            if formula['sym_enc_dec'] > 0:
                parts.append(f"{formula['sym_enc_dec']}T_ed")
            if formula['bilinear_pairing'] > 0:
                parts.append(f"{formula['bilinear_pairing']}T_bp")
            print(" + ".join(parts))
            print(f"  Total Time: {entity_data['total_ms']:.6f} ms")
        
        print(f"\n{'='*70}")
        print(f"TOTAL COMPUTATIONAL COST: {results['total']['time_ms']:.6f} ms")
        print(f"Formula: {results['total']['formula_string']}")
        print(f"{'='*70}\n")


@hydra.main(version_base=None, config_path="config", config_name="config")
def main(cfg: DictConfig):
    """Main computational cost analysis function."""
    # Load benchmark results
    results_dir = Path(cfg.output.results_dir)
    benchmark_file = results_dir / "benchmark_results.json"
    
    if not benchmark_file.exists():
        print(f"Error: Benchmark results not found at {benchmark_file}")
        print("Please run benchmark.py first.")
        return
    
    with open(benchmark_file, 'r') as f:
        benchmark_results = json.load(f)
    
    # Calculate computational costs
    analyzer = ComputationalCostAnalyzer(benchmark_results, cfg.cost_formulas)
    results = analyzer.calculate_total_cost()
    
    # Print results
    analyzer.print_results(results)
    
    # Save results
    output_file = results_dir / "computational_cost.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to: {output_file}")


if __name__ == "__main__":
    main()
