"""
Calculate the communication cost of the scheme based on message sizes.
"""
import json
from pathlib import Path
from typing import Dict
import hydra
from omegaconf import DictConfig


class CommunicationCostAnalyzer:
    """Analyze communication costs of the authentication scheme."""
    
    def __init__(self, data_sizes: DictConfig, network: DictConfig):
        self.data_sizes = data_sizes
        self.bandwidth_bps = network.bandwidth_bps
    
    def calculate_message_sizes(self) -> Dict:
        """
        Calculate the size of each message in the authentication phase.
        
        Messages:
        - M1 = {RID_i, P_i, F_i, T_1}
        - M2 = {W_i, X_i, Y_i, D, T_2}
        - M3 = {L_i, Z_i, T_3}
        - M4 = {N_i, J_i, T_4}
        """
        messages = {
            'M1': {
                'components': {
                    'RID_i': self.data_sizes.hash_output,
                    'P_i': self.data_sizes.ec_point,
                    'F_i': self.data_sizes.random_number,
                    'T_1': self.data_sizes.timestamp,
                },
                'description': 'Vehicle to Fog Node'
            },
            'M2': {
                'components': {
                    'W_i': self.data_sizes.random_number,
                    'X_i': self.data_sizes.hash_output,
                    'Y_i': self.data_sizes.hash_output,
                    'D': self.data_sizes.hash_output,
                    'T_2': self.data_sizes.timestamp,
                },
                'description': 'Fog Node to Cloud Server'
            },
            'M3': {
                'components': {
                    'L_i': self.data_sizes.random_number,
                    'Z_i': self.data_sizes.hash_output,
                    'T_3': self.data_sizes.timestamp,
                },
                'description': 'Cloud Server to Fog Node'
            },
            'M4': {
                'components': {
                    'N_i': self.data_sizes.hash_output,
                    'J_i': self.data_sizes.hash_output,
                    'T_4': self.data_sizes.timestamp,
                },
                'description': 'Fog Node to Vehicle'
            }
        }
        
        for message_name, message_data in messages.items():
            total_bits = sum(message_data['components'].values())
            message_data['total_bits'] = total_bits
            message_data['total_bytes'] = total_bits / 8
            message_data['transmission_time_ms'] = (total_bits / self.bandwidth_bps) * 1000
        
        return messages
    
    def calculate_total_cost(self, messages: Dict) -> Dict:
        """Calculate total communication cost."""
        total_bits = sum(msg['total_bits'] for msg in messages.values())
        total_bytes = total_bits / 8
        total_transmission_time_ms = (total_bits / self.bandwidth_bps) * 1000
        
        return {
            'total_bits': total_bits,
            'total_bytes': total_bytes,
            'total_transmission_time_ms': total_transmission_time_ms,
            'bandwidth_bps': self.bandwidth_bps,
            'messages': messages
        }
    
    def print_results(self, results: Dict):
        """Print communication cost results in a readable format."""
        print("\n" + "="*70)
        print("COMMUNICATION COST ANALYSIS")
        print("="*70)
        print(f"\nBandwidth: {results['bandwidth_bps'] / 1_000_000:.1f} Mbps")
        
        for message_name, message_data in results['messages'].items():
            print(f"\n{message_name} ({message_data['description']}):")
            for component, size_bits in message_data['components'].items():
                print(f"  {component:8s}: {size_bits:4d} bits")
            print(f"  {'Total':8s}: {message_data['total_bits']:4d} bits ({message_data['total_bytes']:.1f} bytes)")
            print(f"  {'Time':8s}: {message_data['transmission_time_ms']:.6f} ms")
        
        print(f"\n{'='*70}")
        print(f"TOTAL COMMUNICATION COST:")
        print(f"  {results['total_bits']} bits ({results['total_bytes']:.1f} bytes)")
        print(f"  Transmission Time: {results['total_transmission_time_ms']:.6f} ms")
        print(f"{'='*70}\n")


@hydra.main(version_base=None, config_path="config", config_name="config")
def main(cfg: DictConfig):
    """Main communication cost analysis function."""
    analyzer = CommunicationCostAnalyzer(cfg.data_sizes, cfg.network)
    
    messages = analyzer.calculate_message_sizes()
    results = analyzer.calculate_total_cost(messages)
    
    analyzer.print_results(results)
    
    results_dir = Path(cfg.output.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = results_dir / "communication_cost.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to: {output_file}")


if __name__ == "__main__":
    main()
