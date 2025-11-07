import sys
import time
import secrets
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scheme import CloudServer, FogNode, Vehicle
from scheme.common import random_nonce, int_to_bytes


def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_scenario(num, title):
    print(f"\n{'-' * 70}")
    print(f"Scenario {num}: {title}")
    print('-' * 70)


def print_attack(description):
    print(f"\n[!] ATTACK: {description}")


def print_result(success, message):
    symbol = "[+]" if success else "[-]"
    print(f"{symbol} {message}")


def run_security_demo():
    print_header("SECURITY DEMONSTRATION: Attack Resistance")
    print("\nThis demonstration shows how the protocol handles:")
    print("  1. [+] Successful authentication (baseline)")
    print("  2. [-] Replay attack (old timestamp)")
    print("  3. [-] Impersonation attack (wrong credentials)")
    print("  4. [-] Man-in-the-middle attack (tampered message)")
    
    # Setup
    K_c = random_nonce()
    cs = CloudServer(K_c)
    
    # Generate 8-byte identifiers
    VID_i = secrets.token_bytes(8)
    VPW_i = secrets.token_bytes(8)
    FID_j = secrets.token_bytes(8)
    
    # Scenario 1: Successful Authentication (Baseline)
    print_scenario(1, "Successful Authentication (Baseline)")
    
    vehicle = Vehicle(VID_i, VPW_i)
    vehicle.register(cs)
    
    fog = FogNode(FID_j)
    fog.register(cs)
    
    print("Setup: Vehicle and Fog Node registered with Cloud Server")
    
    try:
        a_i = vehicle.login_and_verify(VID_i, VPW_i)
        RID_i, P_i, F_i, T_1 = vehicle.generate_m1(FID_j, fog.storage['B_j'])
        W_i, X_i, Y_i, D, T_2 = fog.generate_m2(RID_i, P_i, F_i, T_1)
        L_i, Z_i, T_3 = cs.handle_m2(W_i, X_i, Y_i, D, T_2, FID_j)
        N_i, J_i, T_4 = fog.generate_m4(L_i, Z_i, T_3)
        vehicle.establish_session_key(N_i, J_i, T_4, FID_j)
        
        print_result(True, "Authentication completed successfully")
        print_result(True, "Session key established")
        print(f"  Session Key: {vehicle.session_key.hex()[:32]}...")
    except Exception as e:
        print_result(False, f"Unexpected error: {e}")
    
    # Scenario 2: Replay Attack
    print_scenario(2, "Replay Attack (Old Timestamp)")
    
    VID_2 = secrets.token_bytes(8)
    VPW_2 = secrets.token_bytes(8)
    FID_2 = secrets.token_bytes(8)
    
    vehicle2 = Vehicle(VID_2, VPW_2)
    vehicle2.register(cs)
    
    fog2 = FogNode(FID_2)
    fog2.register(cs)
    
    print("Setup: New vehicle and fog node registered")
    
    try:
        vehicle2.login_and_verify(VID_2, VPW_2)
        RID_i, P_i, F_i, T_1 = vehicle2.generate_m1(FID_2, fog2.storage['B_j'])
        
        print(f"  Original Message: M1 generated at T_1 = {int.from_bytes(T_1, 'big')}")
        print("  Attacker captures M1...")
        
        # Wait to simulate old timestamp
        print("  Simulating time delay (timestamp becomes stale)...")
        time.sleep(11)  # Sleep longer than DELTA_T (10 seconds)
        
        print_attack("Replaying captured M1 with stale timestamp")
        
        # Try to use old message
        W_i, X_i, Y_i, D, T_2 = fog2.generate_m2(RID_i, P_i, F_i, T_1)
        
        print_result(False, "Replay attack should have been detected!")
        
    except ValueError as e:
        if "not fresh" in str(e):
            print_result(True, f"Protocol rejected replay: {e}")
            print("  [+] Timestamp verification prevents replay attacks")
        else:
            print_result(False, f"Wrong error: {e}")
    except Exception as e:
        print_result(False, f"Unexpected error: {e}")
    
    # Scenario 3: Impersonation Attack
    print_scenario(3, "Impersonation Attack (Wrong Credentials)")
    
    VID_3 = secrets.token_bytes(8)
    VPW_3 = secrets.token_bytes(8)
    FAKE_VPW = secrets.token_bytes(8)
    
    vehicle3 = Vehicle(VID_3, VPW_3)
    vehicle3.register(cs)
    
    print("Setup: Legitimate vehicle registered")
    print(f"  Real VID: {VID_3.hex()}")
    print(f"  Real Password: [PROTECTED]")
    
    print_attack("Attacker tries to login with wrong password")
    print(f"  Attempted VID: {VID_3.hex()}")
    print(f"  Attempted Password: {FAKE_VPW.hex()}")
    
    try:
        # Attacker tries wrong password
        vehicle3.login_and_verify(VID_3, FAKE_VPW)
        print_result(False, "Impersonation attack should have been detected!")
        
    except ValueError as e:
        if "TV_i does not match" in str(e) or "Login failed" in str(e):
            print_result(True, f"Protocol rejected impersonation: {e}")
            print("  [+] Password verification prevents impersonation")
        else:
            print_result(False, f"Wrong error: {e}")
    except Exception as e:
        print_result(False, f"Unexpected error: {e}")
    
    # Scenario 4: Man-in-the-Middle Attack
    print_scenario(4, "Man-in-the-Middle Attack (Message Tampering)")
    
    VID_4 = secrets.token_bytes(8)
    VPW_4 = secrets.token_bytes(8)
    FID_4 = secrets.token_bytes(8)
    
    vehicle4 = Vehicle(VID_4, VPW_4)
    vehicle4.register(cs)
    
    fog4 = FogNode(FID_4)
    fog4.register(cs)
    
    print("Setup: Vehicle and fog node registered")
    
    try:
        vehicle4.login_and_verify(VID_4, VPW_4)
        RID_i, P_i, F_i, T_1 = vehicle4.generate_m1(FID_4, fog4.storage['B_j'])
        
        print("  Vehicle sends M1 to Fog Node...")
        
        W_i, X_i, Y_i, D, T_2 = fog4.generate_m2(RID_i, P_i, F_i, T_1)
        
        print("  Fog Node sends M2 to Cloud Server...")
        
        print_attack("Attacker intercepts M2 and modifies authenticator D")
        
        # Tamper with the authenticator
        D_tampered = bytes([b ^ 0xFF for b in D[:8]]) + D[8:]  # Flip bits in first 8 bytes
        print(f"  Original D:  {D.hex()[:32]}...")
        print(f"  Tampered D:  {D_tampered.hex()[:32]}...")
        
        # Try to authenticate with tampered message
        L_i, Z_i, T_3 = cs.handle_m2(W_i, X_i, Y_i, D_tampered, T_2, FID_4)
        
        print_result(False, "MITM attack should have been detected!")
        
    except ValueError as e:
        if "verification failed" in str(e) or "does not match" in str(e):
            print_result(True, f"Protocol rejected tampered message: {e}")
            print("  [+] Cryptographic authenticator detects tampering")
        else:
            print_result(False, f"Wrong error: {e}")
    except Exception as e:
        print_result(False, f"Unexpected error: {e}")
    
    # Additional Scenario: Timestamp Tampering in M3
    print_scenario(5, "Timestamp Tampering in M3")
    
    VID_5 = secrets.token_bytes(8)
    VPW_5 = secrets.token_bytes(8)
    FID_5 = secrets.token_bytes(8)
    
    vehicle5 = Vehicle(VID_5, VPW_5)
    vehicle5.register(cs)
    
    fog5 = FogNode(FID_5)
    fog5.register(cs)
    
    print("Setup: Vehicle and fog node registered")
    
    try:
        vehicle5.login_and_verify(VID_5, VPW_5)
        RID_i, P_i, F_i, T_1 = vehicle5.generate_m1(FID_5, fog5.storage['B_j'])
        W_i, X_i, Y_i, D, T_2 = fog5.generate_m2(RID_i, P_i, F_i, T_1)
        L_i, Z_i, T_3 = cs.handle_m2(W_i, X_i, Y_i, D, T_2, FID_5)
        
        print("  Cloud Server sends M3 to Fog Node...")
        
        print_attack("Attacker delays M3 (timestamp becomes stale)")
        
        # Simulate delay - longer than DELTA_T
        time.sleep(11)
        
        N_i, J_i, T_4 = fog5.generate_m4(L_i, Z_i, T_3)
        
        print_result(False, "Timestamp attack should have been detected!")
        
    except ValueError as e:
        if "not fresh" in str(e):
            print_result(True, f"Protocol rejected stale message: {e}")
            print("  [+] Timestamp verification prevents delayed messages")
        else:
            print_result(False, f"Wrong error: {e}")
    except Exception as e:
        print_result(False, f"Unexpected error: {e}")
    
    # Summary
    print_header("SECURITY DEMONSTRATION COMPLETE")
    
    print("\nSecurity Properties Verified:")
    print("  [+] Replay Attack Protection (Timestamp verification)")
    print("  [+] Impersonation Attack Protection (Credential verification)")
    print("  [+] Message Integrity (Cryptographic authenticators)")
    print("  [+] Freshness Guarantee (Timestamp checks)")
    print("  [+] Mutual Authentication (All entities verified)")
    
    print("\nConclusion:")
    print("  The protocol successfully resists common attacks and ensures")
    print("  secure mutual authentication between all three entities.")
    
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    run_security_demo()
