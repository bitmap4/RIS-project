"""
Debug version of protocol demo to trace the authentication failure.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scheme import CloudServer, FogNode, Vehicle
from scheme.common import random_nonce

# Setup
K_c = random_nonce()
cs = CloudServer(K_c)

VID_i = "VEHICLE_001"
VPW_i = "SecurePassword123"
FID_j = "FOG_NODE_001"

# Registration
vehicle = Vehicle(VID_i, VPW_i)
vehicle.register(cs)

fog = FogNode(FID_j)
fog.register(cs)

# Authentication
vehicle.login_and_verify(VID_i, VPW_i)
RID_i, P_i, F_i, T_1 = vehicle.generate_m1(FID_j, fog.storage['B_j'])

print("=== Message M1 ===")
print(f"RID_i: {RID_i.hex()}")
print(f"P_i: ({P_i.x}, {P_i.y})")
print(f"F_i: {F_i.hex()}")
print(f"T_1: {T_1.hex()}")

W_i, X_i, Y_i, D, T_2 = fog.generate_m2(RID_i, P_i, F_i, T_1)

print("\n=== Message M2 (Fog Node) ===")
print(f"W_i: {W_i.hex()}")
print(f"X_i: {X_i.hex()}")
print(f"Y_i: {Y_i.hex()}")
print(f"D: {D.hex()}")
print(f"T_2: {T_2.hex()}")
print(f"\nFog Node State:")
print(f"  PFD_j: {fog.storage['PFD_j'].hex()}")
print(f"  r_4: {fog.r_4.hex()}")
print(f"  R_i: {fog.R_i.hex()}")
print(f"  K_cf: {fog.K_cf.hex()}")

# Now let's manually compute what CS should get
from scheme.common import h, xor_bytes

K_cf_cs = cs.fog_node_data[FID_j]['K_cf']
print(f"\n=== Cloud Server Verification ===")
print(f"K_cf (CS): {K_cf_cs.hex()}")

r_4_star = xor_bytes(W_i, h(K_cf_cs + FID_j.encode()))
print(f"r_4* (recovered): {r_4_star.hex()}")
print(f"r_4 (original):   {fog.r_4.hex()}")
print(f"Match: {r_4_star == fog.r_4}")

PFD_j_star = xor_bytes(X_i, h(FID_j.encode() + K_cf_cs + r_4_star))
print(f"\nPFD_j* (recovered): {PFD_j_star.hex()}")
print(f"PFD_j (original):   {fog.storage['PFD_j'].hex()}")
print(f"Match: {PFD_j_star == fog.storage['PFD_j']}")

R_i_star = xor_bytes(Y_i, h(K_cf_cs + r_4_star))
print(f"\nR_i* (recovered): {R_i_star.hex()}")
print(f"R_i (original):   {fog.R_i.hex()}")
print(f"Match: {R_i_star == fog.R_i}")

D_star = h(PFD_j_star + r_4_star + xor_bytes(R_i_star, K_cf_cs))
print(f"\nD* (computed): {D_star.hex()}")
print(f"D (original):  {D.hex()}")
print(f"Match: {D_star == D}")

# Show what went into D computation on both sides
print(f"\n=== D Computation Debugging ===")
print("Fog Node computes D as:")
print(f"  h(PFD_j || r_4 || (R_i ⊕ K_cf))")
fog_d_input = fog.storage['PFD_j'] + fog.r_4 + xor_bytes(fog.R_i, fog.K_cf)
print(f"  Input: {fog_d_input.hex()}")
print(f"  D = {D.hex()}")

print("\nCloud Server computes D* as:")
print(f"  h(PFD_j* || r_4* || (R_i* ⊕ K_cf))")
cs_d_input = PFD_j_star + r_4_star + xor_bytes(R_i_star, K_cf_cs)
print(f"  Input: {cs_d_input.hex()}")
print(f"  D* = {D_star.hex()}")

print(f"\nInputs match: {fog_d_input == cs_d_input}")
