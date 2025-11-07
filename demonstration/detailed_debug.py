import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scheme import CloudServer, FogNode, Vehicle
from scheme.common import random_nonce, h, xor_bytes

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

print("=== REGISTRATION PHASE ===")
print(f"CS stored K_cf: {cs.fog_node_data[FID_j]['K_cf'].hex()}")
print(f"Fog stored K_cf: {fog.K_cf.hex()}")
print(f"K_cf match: {cs.fog_node_data[FID_j]['K_cf'] == fog.K_cf}")

print(f"\nCS stored PFD_j: {cs.fog_node_data[FID_j]['PFD_j'].hex()}")
print(f"Fog stored PFD_j: {fog.storage['PFD_j'].hex()}")
print(f"PFD_j match: {cs.fog_node_data[FID_j]['PFD_j'] == fog.storage['PFD_j']}")

# Authentication
vehicle.login_and_verify(VID_i, VPW_i)
RID_i, P_i, F_i, T_1 = vehicle.generate_m1(FID_j, fog.storage['B_j'])
W_i, X_i, Y_i, D, T_2 = fog.generate_m2(RID_i, P_i, F_i, T_1)

print("\n=== FOG NODE M2 COMPUTATION ===")
print(f"FID_j: {FID_j}")
print(f"K_cf: {fog.K_cf.hex()}")
print(f"r_4: {fog.r_4.hex()}")
print(f"PFD_j: {fog.storage['PFD_j'].hex()}")
print(f"R_i: {fog.R_i.hex()}")

print("\n--- Computing W_i ---")
h_input_w = fog.K_cf + FID_j.encode()
print(f"h(K_cf || FID_j) input: {h_input_w.hex()}")
h_result_w = h(h_input_w)
print(f"h(K_cf || FID_j) result: {h_result_w.hex()}")
print(f"r_4 length: {len(fog.r_4)}, hash length: {len(h_result_w)}")
W_i_check = xor_bytes(fog.r_4, h_result_w)
print(f"W_i = r_4 ⊕ h(...): {W_i_check.hex()}")
print(f"W_i (from method): {W_i.hex()}")
print(f"W_i match: {W_i == W_i_check}")

print("\n--- Computing X_i ---")
h_input_x = FID_j.encode() + fog.K_cf + fog.r_4
print(f"h(FID_j || K_cf || r_4) input: {h_input_x.hex()}")
h_result_x = h(h_input_x)
print(f"h(FID_j || K_cf || r_4) result: {h_result_x.hex()}")
print(f"PFD_j length: {len(fog.storage['PFD_j'])}, hash length: {len(h_result_x)}")
X_i_check = xor_bytes(fog.storage['PFD_j'], h_result_x)
print(f"X_i = PFD_j ⊕ h(...): {X_i_check.hex()}")
print(f"X_i (from method): {X_i.hex()}")
print(f"X_i match: {X_i == X_i_check}")

print("\n--- Computing Y_i ---")
h_input_y = fog.K_cf + fog.r_4
print(f"h(K_cf || r_4) input: {h_input_y.hex()}")
h_result_y = h(h_input_y)
print(f"h(K_cf || r_4) result: {h_result_y.hex()}")
print(f"R_i length: {len(fog.R_i)}, hash length: {len(h_result_y)}")
Y_i_check = xor_bytes(fog.R_i, h_result_y)
print(f"Y_i = R_i ⊕ h(...): {Y_i_check.hex()}")
print(f"Y_i (from method): {Y_i.hex()}")
print(f"Y_i match: {Y_i == Y_i_check}")

print("\n--- Computing D ---")
xor_input = xor_bytes(fog.R_i, fog.K_cf)
print(f"R_i ⊕ K_cf: {xor_input.hex()}")
d_input = fog.storage['PFD_j'] + fog.r_4 + xor_input
print(f"h(PFD_j || r_4 || (R_i ⊕ K_cf)) input: {d_input.hex()}")
D_check = h(d_input)
print(f"D = h(...): {D_check.hex()}")
print(f"D (from method): {D.hex()}")
print(f"D match: {D == D_check}")

print("\n\n=== CLOUD SERVER M2 VERIFICATION ===")
K_cf_cs = cs.fog_node_data[FID_j]['K_cf']
print(f"K_cf (CS): {K_cf_cs.hex()}")

print("\n--- Recovering r_4 ---")
h_input_w_cs = K_cf_cs + FID_j.encode()
print(f"h(K_cf || FID_j) input: {h_input_w_cs.hex()}")
h_result_w_cs = h(h_input_w_cs)
print(f"h(K_cf || FID_j) result: {h_result_w_cs.hex()}")
print(f"W_i: {W_i.hex()}")
r_4_star = xor_bytes(W_i, h_result_w_cs)
print(f"r_4* = W_i ⊕ h(...): {r_4_star.hex()}")
print(f"r_4 (original): {fog.r_4.hex()}")
print(f"r_4* match: {r_4_star == fog.r_4}")

print("\n--- Recovering PFD_j ---")
h_input_x_cs = FID_j.encode() + K_cf_cs + r_4_star
print(f"h(FID_j || K_cf || r_4*) input: {h_input_x_cs.hex()}")
h_result_x_cs = h(h_input_x_cs)
print(f"h(FID_j || K_cf || r_4*) result: {h_result_x_cs.hex()}")
print(f"X_i: {X_i.hex()}")
PFD_j_star = xor_bytes(X_i, h_result_x_cs)
print(f"PFD_j* = X_i ⊕ h(...): {PFD_j_star.hex()}")
print(f"PFD_j (original): {fog.storage['PFD_j'].hex()}")
print(f"PFD_j* match: {PFD_j_star == fog.storage['PFD_j']}")

print("\n--- Recovering R_i ---")
h_input_y_cs = K_cf_cs + r_4_star
print(f"h(K_cf || r_4*) input: {h_input_y_cs.hex()}")
h_result_y_cs = h(h_input_y_cs)
print(f"h(K_cf || r_4*) result: {h_result_y_cs.hex()}")
print(f"Y_i: {Y_i.hex()}")
R_i_star = xor_bytes(Y_i, h_result_y_cs)
print(f"R_i* = Y_i ⊕ h(...): {R_i_star.hex()}")
print(f"R_i (original): {fog.R_i.hex()}")
print(f"R_i* match: {R_i_star == fog.R_i}")

print("\n--- Computing D* ---")
xor_input_cs = xor_bytes(R_i_star, K_cf_cs)
print(f"R_i* ⊕ K_cf: {xor_input_cs.hex()}")
d_input_cs = PFD_j_star + r_4_star + xor_input_cs
print(f"h(PFD_j* || r_4* || (R_i* ⊕ K_cf)) input: {d_input_cs.hex()}")
D_star = h(d_input_cs)
print(f"D* = h(...): {D_star.hex()}")
print(f"D (original): {D.hex()}")
print(f"D* match: {D == D_star}")

print("\n=== COMPARISON ===")
print(f"Fog D input:  {d_input.hex()}")
print(f"CS D* input:  {d_input_cs.hex()}")
print(f"Inputs match: {d_input == d_input_cs}")
