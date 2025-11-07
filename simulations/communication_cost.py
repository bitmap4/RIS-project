"""
Calculate communication costs for the authentication phase.
"""
from typing import Dict, List


def calculate_message_size(message_components: List[str], bit_sizes: Dict[str, int]) -> int:
    """
    Calculate the size of a message in bits.
    
    Args:
        message_components: List of component types in the message
        bit_sizes: Dictionary mapping component types to their sizes in bits
        
    Returns:
        Total message size in bits
    """
    return sum(bit_sizes[component] for component in message_components)


def calculate_communication_cost(cfg) -> Dict[str, int]:
    """
    Calculate communication cost for all messages.
    
    Args:
        cfg: Hydra configuration
        
    Returns:
        Dictionary with message sizes and total cost
    """
    comm_cfg = cfg.evaluation.communication_cost
    
    # Extract bit sizes
    bit_sizes = {
        'hash_output': comm_cfg.hash_output,
        'random_number': comm_cfg.random_number,
        'ec_point': comm_cfg.ec_point,
        'identifier': comm_cfg.identifier,
        'timestamp': comm_cfg.timestamp,
    }
    
    # Calculate size for each message
    m1_size = calculate_message_size(comm_cfg.messages.M1, bit_sizes)
    m2_size = calculate_message_size(comm_cfg.messages.M2, bit_sizes)
    m3_size = calculate_message_size(comm_cfg.messages.M3, bit_sizes)
    m4_size = calculate_message_size(comm_cfg.messages.M4, bit_sizes)
    
    total_size = m1_size + m2_size + m3_size + m4_size
    
    return {
        'M1': m1_size,
        'M2': m2_size,
        'M3': m3_size,
        'M4': m4_size,
        'total_bits': total_size,
        'total_bytes': total_size // 8,
        'total_kb': total_size / (8 * 1024),
    }


def print_communication_cost(results: Dict[str, int], cfg):
    """Print communication cost results in a formatted way."""
    print("\n" + "="*60)
    print("COMMUNICATION COST ANALYSIS")
    print("="*60)
    
    comm_cfg = cfg.evaluation.communication_cost
    
    print(f"\nData Type Sizes:")
    print(f"  Hash Output:             {comm_cfg.hash_output} bits")
    print(f"  Random/Non-random:       {comm_cfg.random_number} bits")
    print(f"  EC Point:                {comm_cfg.ec_point} bits")
    print(f"  Identifier:              {comm_cfg.identifier} bits")
    print(f"  Timestamp:               {comm_cfg.timestamp} bits")
    
    print(f"\nMessage Sizes:")
    print(f"  M1 (V_i -> F_j):          {results['M1']} bits ({results['M1']//8} bytes)")
    print(f"  M2 (F_j -> CS):           {results['M2']} bits ({results['M2']//8} bytes)")
    print(f"  M3 (CS -> F_j):           {results['M3']} bits ({results['M3']//8} bytes)")
    print(f"  M4 (F_j -> V_i):          {results['M4']} bits ({results['M4']//8} bytes)")
    
    print(f"\n{'-'*60}")
    print(f"  TOTAL:                   {results['total_bits']} bits")
    print(f"                           {results['total_bytes']} bytes")
    print(f"                           {results['total_kb']:.2f} KB")
    print(f"{'-'*60}\n")
