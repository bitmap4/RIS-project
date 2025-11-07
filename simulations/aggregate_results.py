import json
from pathlib import Path
from typing import Dict, List


def load_device_results(output_dir: Path) -> Dict[str, dict]:
    
    results = {}
    
    for device_type in ['vehicle', 'fog_node', 'cloud_server']:
        result_file = output_dir / f"simulation_results_{device_type}.json"
        if result_file.exists():
            with open(result_file, 'r') as f:
                results[device_type] = json.load(f)
    
    return results


def aggregate_results(output_dir: Path = Path("outputs")) -> dict:
    device_results = load_device_results(output_dir)
    
    if not device_results:
        print("No device results found. Run simulations first.")
        return {}
    
    # Aggregate computational costs using average benchmark times
    avg_benchmarks = {}
    for op in ['T_h', 'T_pa', 'T_ed', 'T_sm', 'T_bp']:
        times = [res['benchmarks'][op] for res in device_results.values()]
        avg_benchmarks[op] = sum(times) / len(times)
    
    # Get communication cost (same across all devices)
    comm_cost = list(device_results.values())[0]['communication_cost']
    
    # Calculate total computational cost using average times
    T_h = avg_benchmarks['T_h']
    T_sm = avg_benchmarks['T_sm']
    
    # Total operations: 28T_h + 5T_sm
    total_comp_cost = 28 * T_h + 5 * T_sm
    
    aggregated = {
        'devices': {
            device_type: {
                'name': res['device']['name'],
                'benchmarks': res['benchmarks'],
                'computational_cost_breakdown': res['computational_cost']
            }
            for device_type, res in device_results.items()
        },
        'average_benchmarks': avg_benchmarks,
        'total_computational_cost_ms': total_comp_cost,
        'communication_cost': comm_cost,
        'summary': {
            'total_computational_cost_ms': total_comp_cost,
            'total_communication_bits': comm_cost['total_bits'],
            'total_communication_bytes': comm_cost['total_bytes'],
        }
    }
    
    return aggregated


def print_aggregate_results(results: dict):
    
    print("\n" + "="*60)
    print("AGGREGATED SIMULATION RESULTS")
    print("="*60)
    
    print("\nDevice Benchmarks:")
    for device_type, device_data in results['devices'].items():
        print(f"\n  {device_data['name']} ({device_type}):")
        for op, time_ms in device_data['benchmarks'].items():
            print(f"    {op}: {time_ms:.6f} ms")
    
    print("\n" + "-"*60)
    print("Average Benchmark Times (across all devices):")
    for op, time_ms in results['average_benchmarks'].items():
        print(f"  {op}: {time_ms:.6f} ms")
    
    print("\n" + "-"*60)
    print("FINAL RESULTS:")
    print(f"  Total Computational Cost:  {results['total_computational_cost_ms']:.4f} ms")
    print(f"  Total Communication Cost:  {results['communication_cost']['total_bits']} bits")
    print(f"                             {results['communication_cost']['total_bytes']} bytes")
    print(f"                             {results['communication_cost']['total_kb']:.2f} KB")
    print("="*60 + "\n")


def main():
    
    output_dir = Path("outputs")
    
    if not output_dir.exists():
        print(f"Output directory '{output_dir}' not found.")
        print("Run simulations first using Docker Compose.")
        return
    
    results = aggregate_results(output_dir)
    
    if results:
        print_aggregate_results(results)
        
        # Save aggregated results
        output_file = output_dir / "aggregated_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Aggregated results saved to: {output_file}\n")


if __name__ == "__main__":
    main()
