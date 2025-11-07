import sys
import secrets
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scheme import CloudServer, FogNode, Vehicle
from scheme.common import random_nonce, h, G, xor_bytes, int_to_bytes, bytes_to_int, pad_to_length, ORDER


def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_scenario(num, title):
    print(f"\n{'-' * 70}")
    print(f"ATTACK {num}: {title}")
    print('-' * 70)


def print_step(description):
    print(f"  - {description}")


def print_attack_success(message):
    print(f"\n[!] ATTACK SUCCESSFUL: {message}")


def print_attack_detail(label, value):
    if isinstance(value, bytes):
        display = value.hex()[:32] + "..." if len(value.hex()) > 32 else value.hex()
    else:
        display = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
    print(f"    {label}: {display}")


def attack_1_vehicle_impersonation():
    print_scenario(1, "Vehicle Impersonation Attack (No Authentication)")
    
    print("\nBackground:")
    print("  The vehicle V_i only checks TV_i* == TV_i locally.")
    print("  The secret a_i is never used in messages to F_j or CS.")
    print("  The protocol proceeds without V_i proving its identity.")
    
    # Setup legitimate system
    K_c = random_nonce()
    cs = CloudServer(K_c)
    
    # Register a legitimate vehicle (victim)
    VID_victim = secrets.token_bytes(8)
    VPW_victim = secrets.token_bytes(8)
    vehicle_victim = Vehicle(VID_victim, VPW_victim)
    vehicle_victim.register(cs)
    
    # Register fog node
    FID_j = secrets.token_bytes(8)
    fog = FogNode(FID_j)
    fog.register(cs)
    
    print("\n[+] Setup: Legitimate vehicle and fog node registered")
    print_attack_detail("Victim VID", VID_victim)
    
    # ATTACK: Attacker impersonates victim without password/smart card
    print("\n[!]  ATTACKER ACTION:")
    print_step("Attacker knows victim's VID (not secret)")
    print_step("Attacker knows fog node's public key B_j and FID_j")
    print_step("Attacker generates random r_3, r'_3")
    
    # Attacker generates message components
    r_3_attacker = secrets.randbelow(ORDER)
    r_3_prime_attacker = random_nonce()
    
    P_i_fake = r_3_attacker * G
    Q_i_fake = r_3_attacker * fog.storage['B_j']
    
    # Compute fake message components
    RID_i_fake = xor_bytes(VID_victim, xor_bytes(int_to_bytes(Q_i_fake.x)[:8], pad_to_length(FID_j, 8)))
    F_i_fake = xor_bytes(r_3_prime_attacker, int_to_bytes(Q_i_fake.x)[:20])
    T_1_fake = int_to_bytes(int(__import__('time').time()), 4)
    
    print_step("Attacker computes P_i = r_3 · G")
    print_attack_detail("  P_i.x", int_to_bytes(P_i_fake.x))
    print_step("Attacker computes Q_i = r_3 · B_j")
    print_attack_detail("  Q_i.x", int_to_bytes(Q_i_fake.x))
    print_step("Attacker computes RID_i = VID_i ⊕ (Q_i ⊕ FID_j)")
    print_attack_detail("  RID_i", RID_i_fake)
    print_step("Attacker computes F_i = r'_3 ⊕ Q_i")
    print_attack_detail("  F_i", F_i_fake)
    print_step("Attacker sends M1 = {RID_i, P_i, F_i, T_1} to F_j")
    
    # Try to authenticate as victim
    try:
        # Fog node processes attacker's message (no way to detect it's fake)
        W_i, X_i, Y_i, D, T_2 = fog.generate_m2(RID_i_fake, P_i_fake, F_i_fake, T_1_fake)
        print_step("F_j accepts M1 and generates M2")
        
        # Cloud server processes message
        L_i, Z_i, T_3 = cs.handle_m2(W_i, X_i, Y_i, D, T_2, FID_j)
        print_step("CS accepts M2 and generates M3")
        
        # Fog node generates M4
        N_i, J_i, T_4 = fog.generate_m4(L_i, Z_i, T_3)
        print_step("F_j accepts M3 and generates M4")
        
        # Attacker establishes session key
        print_attack_success("Attacker impersonated victim vehicle!")
        print(f"\n  [-] Fog Node established session with attacker")
        print(f"  [-] Cloud Server believes attacker is legitimate victim")
        print(f"  [-] Session key shared with attacker: {fog.session_key.hex()[:32]}...")
        
        print("\nRoot Cause:")
        print("  - Vehicle never proves knowledge of password or a_i")
        print("  - Only local check TV_i* == TV_i (bypassed by attacker)")
        print("  - Message M1 contains no authenticator tied to vehicle's secrets")
        
        return True
        
    except Exception as e:
        print(f"\n[+] Attack failed: {e}")
        return False


def attack_2_offline_password_guessing():
    print_scenario(2, "Off-Line Password Guessing Attack (Smart Card Stolen)")
    
    print("\nBackground:")
    print("  The smart card stores {TV_i, MV_i, r_1}.")
    print("  TV_i = h(VID_i ⊕ VPW_i || a_i) acts as a verifiable equation.")
    print("  All components needed for verification are on the card.")
    
    # Setup
    K_c = random_nonce()
    cs = CloudServer(K_c)
    
    # Create victim vehicle with known weak password (for demo)
    VID_victim = b"VEHICLE1"  # 8 bytes
    VPW_victim = b"pass1234"  # 8 bytes (weak password)
    vehicle_victim = Vehicle(VID_victim, VPW_victim)
    vehicle_victim.register(cs)
    
    print("\n[+] Setup: Victim vehicle registered")
    print_attack_detail("Victim VID", VID_victim)
    print_attack_detail("Victim Password", b"[PROTECTED]")
    
    print("\n[!]  ATTACKER ACTION:")
    print_step("Attacker steals victim's smart card")
    print_step("Attacker reads {TV_i, MV_i, r_1} from card")
    
    # Attacker extracts smart card data
    stolen_TV_i = vehicle_victim.smart_card['TV_i']
    stolen_MV_i = vehicle_victim.smart_card['MV_i']
    stolen_r_1 = vehicle_victim.smart_card['r_1']
    
    print_attack_detail("Stolen TV_i", stolen_TV_i)
    print_attack_detail("Stolen MV_i", stolen_MV_i)
    print_attack_detail("Stolen r_1", stolen_r_1)
    
    print("\n  Attacker tries password dictionary attack:")
    
    # Dictionary of common passwords
    password_dict = [
        b"12345678",
        b"password",
        b"pass1234",  # This will match
        b"qwerty12",
        b"admin123"
    ]
    
    for i, guess_pwd in enumerate(password_dict, 1):
        print(f"    Attempt {i}: Testing password '{guess_pwd.decode()}'...", end=" ")
        
        # Try to verify the guess
        PV_guess = h(VID_victim + guess_pwd + stolen_r_1)
        a_guess = xor_bytes(stolen_MV_i, PV_guess)
        TV_guess = h(xor_bytes(VID_victim, guess_pwd) + a_guess)
        
        if i == len(password_dict):  # Show computation for matching password
            print(f"\n    Computing verification for '{guess_pwd.decode()}':")
            print(f"      PV_i = h(VID || PWD || r_1) = {PV_guess.hex()[:32]}...")
            print(f"      a_i = MV_i ⊕ PV_i = {a_guess.hex()[:32]}...")
            print(f"      TV_i* = h((VID ⊕ PWD) || a_i) = {TV_guess.hex()[:32]}...")
            print(f"      TV_i (stored) = {stolen_TV_i.hex()[:32]}...")
        
        if TV_guess == stolen_TV_i:
            print("[+] MATCH!")
            print_attack_success("Password recovered!")
            print(f"\n  [-] Recovered VID: {VID_victim.hex()}")
            print(f"  [-] Recovered Password: {guess_pwd.decode()}")
            
            print("\nRoot Cause:")
            print("  - Smart card stores all verification data")
            print("  - No rate limiting on password attempts")
            print("  - TV_i = h(VID_i ⊕ VPW_i || a_i) is directly verifiable")
            print("  - Attacker can test unlimited passwords offline")
            
            return True
        else:
            print("[-]")
    
    print("\n  Attack failed: Password not in dictionary")
    return False


def attack_3_privileged_insider():
    print_scenario(3, "Privileged Insider Attack (Cloud Server Key Escrow)")
    
    print("\nBackground:")
    print("  The CS generates fog node private key: b_j = h(PFD_j || K_c)")
    print("  The CS has complete key escrow - knows all fog node secrets.")
    print("  No separation of trust between CS and fog nodes.")
    
    # Setup
    K_c = random_nonce()
    cs = CloudServer(K_c)
    
    # Register vehicle
    VID_i = secrets.token_bytes(8)
    VPW_i = secrets.token_bytes(8)
    vehicle = Vehicle(VID_i, VPW_i)
    vehicle.register(cs)
    
    # Register fog node
    FID_j = secrets.token_bytes(8)
    fog = FogNode(FID_j)
    fog.register(cs)
    
    print("\n[+] Setup: Vehicle and fog node registered")
    print_attack_detail("Fog Node FID", FID_j)
    print_attack_detail("Fog Node Private Key b_j", fog.b_j)
    
    print("\n[!]  ATTACKER ACTION (Malicious CS Insider):")
    print_step("Insider has access to master key K_c")
    print_step("Insider retrieves fog node data from CS database")
    
    # Malicious insider extracts secrets
    stored_fog_data = cs.fog_node_data[FID_j]
    insider_PFD_j = stored_fog_data['PFD_j']
    insider_b_j = stored_fog_data['b_j']
    insider_K_cf = stored_fog_data['K_cf']
    
    print_attack_detail("Extracted PFD_j", insider_PFD_j)
    print_attack_detail("Extracted b_j", insider_b_j)
    print_attack_detail("Extracted K_cf", insider_K_cf)
    
    print_step("Insider can compute: b_j = h(PFD_j || K_c)")
    print_step("Insider can recompute: K_cf = h(FID_j ⊕ K_c)")
    
    # Verify insider has correct secrets
    if insider_b_j == fog.b_j:
        print("\n  [+] Insider successfully extracted fog node private key!")
    
    # Demonstrate passive eavesdropping
    print("\n  Demonstrating passive eavesdropping:")
    
    # Normal authentication
    vehicle.login_and_verify(VID_i, VPW_i)
    RID_i, P_i, F_i, T_1 = vehicle.generate_m1(FID_j, fog.storage['B_j'])
    
    print_step("Vehicle sends M1 to Fog Node")
    
    # Insider intercepts and decrypts
    print_step("Insider intercepts M1 = {RID_i, P_i, F_i, T_1}")
    
    # Insider computes session key using stolen b_j
    Q_i_insider = bytes_to_int(insider_b_j) * P_i
    r_3_prime_insider = xor_bytes(F_i, int_to_bytes(Q_i_insider.x)[:20])
    
    print_step("Insider computes Q_i = b_j · P_i using stolen b_j")
    print_attack_detail("  Q_i.x", int_to_bytes(Q_i_insider.x))
    print_step("Insider recovers r'_3 = F_i ⊕ Q_i")
    print_attack_detail("  r'_3", r_3_prime_insider)
    
    # Continue protocol
    W_i, X_i, Y_i, D, T_2 = fog.generate_m2(RID_i, P_i, F_i, T_1)
    
    print_step("Insider observes/intercepts M2 = {W_i, X_i, Y_i, D, T_2}")
    
    # Insider can recover values from M2 using stolen K_cf
    r_4_insider = xor_bytes(W_i, h(insider_K_cf + pad_to_length(FID_j, 20)))
    PFD_j_insider = xor_bytes(X_i, h(FID_j + xor_bytes(insider_K_cf, r_4_insider)))
    R_i_insider = xor_bytes(Y_i, h(insider_K_cf + r_4_insider))
    
    print_step("Insider recovers r_4 = W_i ⊕ h(K_cf || FID_j)")
    print_attack_detail("  r_4", r_4_insider)
    print_step("Insider recovers PFD_j = X_i ⊕ h(FID_j || (K_cf ⊕ r_4))")
    print_attack_detail("  PFD_j", PFD_j_insider)
    print_step("Insider recovers R_i = Y_i ⊕ h(K_cf || r_4)")
    print_attack_detail("  R_i", R_i_insider)
    
    L_i, Z_i, T_3 = cs.handle_m2(W_i, X_i, Y_i, D, T_2, FID_j)
    
    print_step("Insider observes/intercepts M3 = {L_i, Z_i, T_3}")
    
    # Insider can recover r_5 from L_i
    r_5_insider = xor_bytes(L_i, h(xor_bytes(insider_K_cf, pad_to_length(FID_j, 20)) + r_4_insider))
    
    print_step("Insider recovers r_5 = L_i ⊕ h((K_cf ⊕ FID_j) || r_4)")
    print_attack_detail("  r_5", r_5_insider)
    
    N_i, J_i, T_4 = fog.generate_m4(L_i, Z_i, T_3)
    
    # Insider can now compute session key
    print("\n  Insider computes session key:")
    print_step("SK = h(PFD_j || pad(R_i, 20) || r_4 || (r_5 ⊕ K_cf))")
    insider_SK = h(PFD_j_insider + pad_to_length(R_i_insider, 20) + r_4_insider + xor_bytes(r_5_insider, insider_K_cf))
    print_attack_detail("  Computed SK", insider_SK)
    
    print_attack_success("Insider computed session key!")
    print(f"\n  [-] Legitimate session key:  {fog.session_key.hex()[:32]}...")
    print(f"  [-] Insider computed key:    {insider_SK.hex()[:32]}...")
    
    if insider_SK == fog.session_key:
        print(f"  [-] KEYS MATCH - Insider can decrypt all communications!")
        
        print("\nRoot Cause:")
        print("  - CS generates all fog node private keys")
        print("  - No forward secrecy or key separation")
        print("  - Single point of trust failure")
        print("  - Complete key escrow by cloud server")
        
        return True
    
    return False


def attack_4_fog_node_impersonation():
    print_scenario(4, "Fog Node Impersonation Attack (Flawed Authentication)")
    
    print("\nBackground:")
    print("  V_i checks: J_i == h(RID_i || r'_3 ⊕ Q_i)")
    print("  But RID_i and F_i = r'_3 ⊕ Q_i were both sent BY V_i in M1!")
    print("  This only proves the recipient read M1, not that it has b_j.")
    
    # Setup
    K_c = random_nonce()
    cs = CloudServer(K_c)
    
    # Register vehicle
    VID_i = secrets.token_bytes(8)
    VPW_i = secrets.token_bytes(8)
    vehicle = Vehicle(VID_i, VPW_i)
    vehicle.register(cs)
    
    # Register legitimate fog node
    FID_j = secrets.token_bytes(8)
    fog_legit = FogNode(FID_j)
    fog_legit.register(cs)
    
    print("\n[+] Setup: Vehicle and legitimate fog node registered")
    print_attack_detail("Legitimate FID_j", FID_j)
    
    # Vehicle initiates authentication
    vehicle.login_and_verify(VID_i, VPW_i)
    RID_i, P_i, F_i, T_1 = vehicle.generate_m1(FID_j, fog_legit.storage['B_j'])
    
    print("\n  Vehicle sends M1 = {RID_i, P_i, F_i, T_1}")
    print_attack_detail("RID_i", RID_i)
    print_attack_detail("F_i", F_i)
    
    print("\n[!]  ATTACKER ACTION:")
    print_step("Attacker intercepts M1 (impersonating fog node)")
    print_step("Attacker has NO knowledge of b_j or any fog secrets")
    print_step("Attacker computes J_i = h(RID_i || F_i)")
    
    # Attacker forges response
    J_i_fake = h(RID_i + F_i)  # Just hash what was received!
    N_i_fake = random_nonce()  # Random fake value
    T_4_fake = int_to_bytes(int(__import__('time').time()), 4)
    
    print_step("Attacker sends forged M4 = {N_i_fake, J_i_correct, T_4}")
    
    print("\n  Vehicle verifies J_i:")
    print_step("Vehicle computes J_i* = h(RID_i || (r'_3 ⊕ Q_i))")
    
    # Vehicle attempts to verify (will succeed!)
    try:
        # Store the values vehicle needs
        vehicle.RID_i = RID_i
        vehicle.r_3_prime = xor_bytes(F_i, int_to_bytes(vehicle.Q_i.x)[:20])
        
        # Vehicle computes J_i*
        r3_xor_Qi = xor_bytes(vehicle.r_3_prime, int_to_bytes(vehicle.Q_i.x)[:20])
        print_attack_detail("  r'_3 ⊕ Q_i", r3_xor_Qi)
        print_step("But r'_3 ⊕ Q_i = F_i (what vehicle sent in M1!)")
        print_attack_detail("  F_i (from M1)", F_i)
        print_step("So J_i* = h(RID_i || F_i)")
        
        J_i_star = h(vehicle.RID_i + r3_xor_Qi)
        print_attack_detail("  J_i* computed", J_i_star)
        
        if J_i_star == J_i_fake:
            print_attack_success("Vehicle authenticated fake fog node!")
            print(f"\n  [-] Vehicle computed J_i*: {J_i_star.hex()[:32]}...")
            print(f"  [-] Attacker sent J_i:     {J_i_fake.hex()[:32]}...")
            print(f"  [-] J_i* == J_i: Vehicle is convinced!")
            
            print("\nRoot Cause:")
            print("  - Authentication check uses values vehicle sent itself")
            print("  - J_i = h(RID_i || F_i) requires no secrets from fog node")
            print("  - Attacker just echoes received data in hash")
            print("  - No proof that fog node possesses private key b_j")
            
            return True
        else:
            print(f"\n[+] Attack failed: J_i mismatch")
            return False
            
    except Exception as e:
        print(f"\n[+] Attack failed: {e}")
        return False


def run_attack_demos():
    print_header("CRITICAL SECURITY FLAWS DEMONSTRATION")
    print("\nThis demonstrates SUCCESSFUL attacks exploiting vulnerabilities.")
    print("Each attack shows the scheme is NOT SECURE against these threats.")
    
    results = []
    
    # Run each attack
    results.append(("Vehicle Impersonation", attack_1_vehicle_impersonation()))
    results.append(("Offline Password Guessing", attack_2_offline_password_guessing()))
    results.append(("Privileged Insider", attack_3_privileged_insider()))
    results.append(("Fog Node Impersonation", attack_4_fog_node_impersonation()))
    
    # Summary
    print_header("ATTACK SUMMARY")
    print("\nResults:")
    for attack_name, success in results:
        symbol = "[!]" if success else "[+]"
        status = "VULNERABLE" if success else "PROTECTED"
        print(f"  {symbol} {attack_name}: {status}")
    
    vulnerable_count = sum(1 for _, success in results if success)
    print(f"\n[!]  Scheme is vulnerable to {vulnerable_count}/{len(results)} demonstrated attacks")
    print("=" * 70)


if __name__ == "__main__":
    run_attack_demos()
