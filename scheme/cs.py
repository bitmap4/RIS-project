import time
from .common import h, G, xor_bytes, int_to_bytes, bytes_to_int, random_nonce, DELTA_T, pad_to_length

class CloudServer:
    def __init__(self, k_c):
        self.K_c = k_c  # Master secret key
        self.vehicle_data = {}
        self.fog_node_data = {}

    def register_vehicle(self, VID_i, PV_i):
        
        a_i_int = bytes_to_int(h(VID_i + PV_i + self.K_c))
        # A_i = a_i_int * G  # This is never used, as per instructions
        MV_i = xor_bytes(int_to_bytes(a_i_int), PV_i)
        
        # Store for later verification if needed, though not specified
        self.vehicle_data[VID_i] = {'PV_i': PV_i, 'a_i': int_to_bytes(a_i_int)}
        
        return MV_i

    def register_fog_node(self, FID_j):
        
        r_2 = random_nonce()
        PFD_j = h(FID_j + r_2)
        b_j_int = bytes_to_int(h(PFD_j + self.K_c))
        B_j = b_j_int * G
        K_cf = h(xor_bytes(pad_to_length(FID_j, 20), self.K_c))

        self.fog_node_data[FID_j] = {'PFD_j': PFD_j, 'b_j': int_to_bytes(b_j_int), 'K_cf': K_cf}
        
        return PFD_j, int_to_bytes(b_j_int), K_cf, B_j

    def handle_m2(self, W_i, X_i, Y_i, D, T_2, FID_j):
        
        if abs(int(time.time()) - bytes_to_int(T_2)) > DELTA_T:
            raise ValueError("CS: T2 is not fresh. Aborting.")

        # Assuming CS knows FID_j from the communication channel
        if FID_j not in self.fog_node_data:
            raise ValueError("Fog node not registered.")

        K_cf = self.fog_node_data[FID_j]['K_cf']
        
        r_4_star = xor_bytes(W_i, h(K_cf + pad_to_length(FID_j, 20)))
        PFD_j_star = xor_bytes(X_i, h(FID_j + xor_bytes(K_cf, r_4_star)))
        R_i_star = xor_bytes(Y_i, h(K_cf + r_4_star))
        
        D_star = h(PFD_j_star + r_4_star + xor_bytes(R_i_star, K_cf))

        if D_star != D:
            raise ValueError("CS: D* verification failed. Aborting.")

        r_5 = random_nonce()  # 20 bytes
        T_3 = int_to_bytes(int(time.time()), 4)  # 32 bits = 4 bytes

        SK = h(PFD_j_star + R_i_star + r_4_star + xor_bytes(r_5, K_cf))

        real_R_i = R_i_star[:8] 
        # Now we can find the real VID_i
        VID_i_star = xor_bytes(real_R_i, FID_j)

        # Store session key for verification
        if VID_i_star in self.vehicle_data:
            self.vehicle_data[VID_i_star]['session_key'] = SK
        
        # # Store session key for verification
        # if R_i_star[:8] in self.vehicle_data:
        #     self.vehicle_data[R_i_star[:8]]['session_key'] = SK
        
        Z_i = h(SK + xor_bytes(K_cf, pad_to_length(FID_j, 20)))
        L_i = xor_bytes(r_5, h(xor_bytes(K_cf, pad_to_length(FID_j, 20)) + r_4_star))

        return L_i, Z_i, T_3
