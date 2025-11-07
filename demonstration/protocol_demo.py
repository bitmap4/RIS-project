"""
Demonstration 1: End-to-End Protocol Execution
Shows the complete authentication flow with all messages and verifications.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scheme import CloudServer, FogNode, Vehicle
from scheme.common import random_nonce


def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_step(step_num, description):
    print(f"\n[Step {step_num}] {description}")
    print("-" * 70)


def print_message(entity, content):
    print(f"  {entity}: {content}")


def print_success(message):
    print(f"  [+] {message}")


def print_data(label, value):
    if isinstance(value, bytes):
        display = value.hex()[:32] + "..." if len(value.hex()) > 32 else value.hex()
    else:
        display = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
    print(f"    {label}: {display}")


def run_protocol_demo():
    """Run complete end-to-end protocol demonstration."""
    
    print_header("PROTOCOL DEMONSTRATION: Mutual Authentication")
    print("\nThis demonstration shows the complete authentication flow")
    print("between a Vehicle (V_i), Fog Node (F_j), and Cloud Server (CS).")
    print("\nProtocol Phases:")
    print("  1. System Initialization")
    print("  2. Vehicle Registration")
    print("  3. Fog Node Registration")
    print("  4. Authentication & Session Key Establishment")
    
    # Phase 1: System Initialization
    print_header("Phase 1: System Initialization")
    
    print_message("Cloud Server", "Generating master secret key K_c...")
    K_c = random_nonce()
    cs = CloudServer(K_c)
    print_success("Cloud Server initialized")
    print_data("Master Key K_c", K_c)
    
    # Phase 2: Vehicle Registration
    print_header("Phase 2: Vehicle Registration")
    
    import secrets
    VID_i = secrets.token_bytes(8)  # 64 bits = 8 bytes
    VPW_i = secrets.token_bytes(8)  # 64 bits = 8 bytes
    
    print_message("Vehicle V_i", f"Identity: {VID_i.hex()}")
    print_message("Vehicle V_i", "Password: [PROTECTED]")
    print_message("Vehicle V_i", "Generating local random r_1...")
    
    vehicle = Vehicle(VID_i, VPW_i)
    print_data("Random r_1", vehicle.r_1)
    
    print_message("Vehicle V_i", "Computing PV_i = h(VID_i || VPW_i || r_1)")
    print_message("Vehicle V_i", "Sending registration request to CS...")
    
    vehicle.register(cs)
    
    print_success("Vehicle registered successfully")
    print_data("Smart Card TV_i", vehicle.smart_card['TV_i'])
    print_data("Smart Card MV_i", vehicle.smart_card['MV_i'])
    
    # Phase 3: Fog Node Registration
    print_header("Phase 3: Fog Node Registration")
    
    FID_j = secrets.token_bytes(8)  # 64 bits = 8 bytes
    
    print_message("Fog Node F_j", f"Identity: {FID_j.hex()}")
    print_message("Fog Node F_j", "Sending registration request to CS...")
    
    fog = FogNode(FID_j)
    fog.register(cs)
    
    print_success("Fog Node registered successfully")
    print_data("Pseudo-identity PFD_j", fog.PFD_j)
    print_data("Private key b_j", fog.b_j)
    print_data("Shared key K_cf", fog.K_cf)
    print_data("Public key B_j", fog.storage['B_j'])
    
    # Phase 4: Authentication
    print_header("Phase 4: Authentication & Session Key Establishment")
    
    # Step 1: Vehicle Login
    print_step(1, "Vehicle Login and Verification")
    
    print_message("Vehicle V_i", "Inserting credentials...")
    print_message("Vehicle V_i", f"VID*: {VID_i}")
    print_message("Vehicle V_i", "VPW*: [PROTECTED]")
    
    print_message("Vehicle V_i", "Computing TV*_i and verifying against smart card...")
    a_i = vehicle.login_and_verify(VID_i, VPW_i)
    
    print_success(f"Login verification successful: TV*_i == TV_i")
    
    # Step 2: V_i -> F_j (Message M1)
    print_step(2, "V_i -> F_j: Sending Message M1")
    
    print_message("Vehicle V_i", "Generating random values r_3, r'_3...")
    print_message("Vehicle V_i", "Computing P_i = r_3 · G (elliptic curve point)")
    print_message("Vehicle V_i", "Computing Q_i = r_3 · B_j")
    
    RID_i, P_i, F_i, T_1 = vehicle.generate_m1(FID_j, fog.storage['B_j'])
    
    print_data("RID_i (masked VID)", RID_i)
    print_data("P_i (EC point)", f"({P_i.x}, {P_i.y})")
    print_data("F_i (masked r'_3)", F_i)
    print_data("T_1 (timestamp)", T_1)
    
    print_message("Vehicle V_i", f"Sending M1 = {{RID_i, P_i, F_i, T_1}} to Fog Node {FID_j}")
    print_success(f"Message M1 transmitted")
    
    # Step 3: F_j -> CS (Message M2)
    print_step(3, "F_j -> CS: Verifying and Forwarding Message M2")
    
    print_message("Fog Node F_j", "Received M1 from Vehicle")
    print_message("Fog Node F_j", f"Verifying timestamp T_1 freshness (ΔT = {time.time() - int.from_bytes(T_1, 'big')}s)...")
    
    W_i, X_i, Y_i, D, T_2 = fog.generate_m2(RID_i, P_i, F_i, T_1)
    
    print_success("Timestamp T_1 is fresh")
    print_message("Fog Node F_j", "Computing Q_i = b_j · P_i")
    print_message("Fog Node F_j", "Recovering r'_3 from F_i")
    print_message("Fog Node F_j", "Computing R_i (masked VID)")
    print_message("Fog Node F_j", "Generating random r_4 and computing message components...")
    
    print_data("W_i", W_i)
    print_data("X_i", X_i)
    print_data("Y_i", Y_i)
    print_data("D (authenticator)", D)
    print_data("T_2 (timestamp)", T_2)
    
    print_message("Fog Node F_j", f"Sending M2 = {{W_i, X_i, Y_i, D, T_2}} to Cloud Server")
    print_success(f"Message M2 transmitted")
    
    # Step 4: CS -> F_j (Message M3)
    print_step(4, "CS -> F_j: Authenticating and Sending Message M3")
    
    print_message("Cloud Server", "Received M2 from Fog Node")
    print_message("Cloud Server", f"Verifying timestamp T_2 freshness (ΔT = {time.time() - int.from_bytes(T_2, 'big')}s)...")
    
    L_i, Z_i, T_3 = cs.handle_m2(W_i, X_i, Y_i, D, T_2, FID_j)
    
    print_success("Timestamp T_2 is fresh")
    print_message("Cloud Server", "Recovering r_4, PFD_j, R_i from message components...")
    print_message("Cloud Server", "Computing authenticator D* and verifying D* == D...")
    print_success("Fog Node and Vehicle authenticated successfully")
    
    print_message("Cloud Server", "Computing VID_i from R_i...")
    print_message("Cloud Server", "Computing session key SK = h(VID_i || r_3 || r'_3 || r_4)")
    print_message("Cloud Server", "Generating challenge components L_i, Z_i...")
    
    print_data("L_i", L_i)
    print_data("Z_i", Z_i)
    print_data("T_3 (timestamp)", T_3)
    
    print_message("Cloud Server", f"Sending M3 = {{L_i, Z_i, T_3}} to Fog Node")
    print_success(f"Message M3 transmitted")
    
    # Step 5: F_j -> V_i (Message M4)
    print_step(5, "F_j -> V_i: Verifying CS and Sending Message M4")
    
    print_message("Fog Node F_j", "Received M3 from Cloud Server")
    print_message("Fog Node F_j", f"Verifying timestamp T_3 freshness (ΔT = {time.time() - int.from_bytes(T_3, 'big')}s)...")
    
    N_i, J_i, T_4 = fog.generate_m4(L_i, Z_i, T_3)
    
    print_success("Timestamp T_3 is fresh")
    print_message("Fog Node F_j", "Recovering r'_3 and computing Z*_i...")
    print_message("Fog Node F_j", "Verifying Z*_i == Z_i...")
    print_success("Cloud Server authenticated successfully")
    
    print_message("Fog Node F_j", "Computing session key SK* = h(r'_3 || r_4 || Q_i)")
    print_message("Fog Node F_j", "Generating challenge components N_i, J_i...")
    
    print_data("N_i", N_i)
    print_data("J_i", J_i)
    print_data("T_4 (timestamp)", T_4)
    
    print_message("Fog Node F_j", f"Sending M4 = {{N_i, J_i, T_4}} to Vehicle")
    print_success(f"Message M4 transmitted")
    
    # Step 6: V_i establishes session key
    print_step(6, "V_i: Verifying F_j and Establishing Session Key")
    
    print_message("Vehicle V_i", "Received M4 from Fog Node")
    print_message("Vehicle V_i", f"Verifying timestamp T_4 freshness (ΔT = {time.time() - int.from_bytes(T_4, 'big')}s)...")
    
    vehicle.establish_session_key(N_i, J_i, T_4, FID_j)
    
    print_success("Timestamp T_4 is fresh")
    print_message("Vehicle V_i", "Computing J*_i = h(RID_i || r'_3 || N_i || T_4)...")
    print_message("Vehicle V_i", "Verifying J*_i == J_i...")
    print_success("Fog Node authenticated successfully")
    
    print_message("Vehicle V_i", "Computing session key SK = h(r'_3 || N_i || Q_i)")
    print_success("Session key established")
    
    # Final Summary
    print_header("PROTOCOL EXECUTION COMPLETE")
    
    print("\n[+] All entities successfully authenticated")
    print("[+] Session key established securely")
    print("\nSession Keys:")
    print_data("  Vehicle SK", vehicle.session_key)
    print_data("  Fog Node SK", fog.session_key)
    
    # Verify session keys match
    print("\nVerifying session key agreement...")
    if vehicle.session_key == fog.session_key:
        print("  [+] SUCCESS: Vehicle and Fog Node share the same session key!")
    else:
        print("  [-] ERROR: Session keys do not match!")
        print(f"  Vehicle: {vehicle.session_key.hex()[:32]}...")
        print(f"  Fog:     {fog.session_key.hex()[:32]}...")
        # Cloud server may not store session_key for this VID (implementation choice)
        if VID_i in cs.vehicle_data and 'session_key' in cs.vehicle_data[VID_i]:
            print(f"  Cloud:   {cs.vehicle_data[VID_i]['session_key'].hex()[:32]}...")
        else:
            print("  Cloud:   [not stored]")
    
    print("\n" + "=" * 70)
    print("  DEMONSTRATION COMPLETE")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_protocol_demo()
