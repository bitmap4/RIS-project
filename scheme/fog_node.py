import time
import secrets
from .common import h, G, CURVE, xor_bytes, int_to_bytes, bytes_to_int, random_nonce, DELTA_T, pad_to_length

class FogNode:
    def __init__(self, FID_j):
        # FID must be 8 bytes (64 bits) as per scheme specification
        if isinstance(FID_j, str):
            FID_j = FID_j.encode()[:8].ljust(8, b'\x00')
        self.FID_j = FID_j
        self.storage = {}
        self.session_key = None
        self.b_j = None
        self.K_cf = None
        self.PFD_j = None
        self.r_4 = None
        self.R_i = None
        self.Q_i = None
        self.RID_i = None
        self.r_3_prime = None

    def register(self, cs):
        
        PFD_j, b_j, K_cf, B_j = cs.register_fog_node(self.FID_j)
        
        self.PFD_j = PFD_j
        self.b_j = b_j
        self.K_cf = K_cf
        
        Rb_j = xor_bytes(b_j, h(self.FID_j + K_cf))
        RK_cf = xor_bytes(K_cf, pad_to_length(self.FID_j, 20))
        
        self.storage['Rb_j'] = Rb_j
        self.storage['PFD_j'] = PFD_j
        self.storage['RK_cf'] = RK_cf
        self.storage['B_j'] = B_j # Public key

    def _recover_secrets(self):
        
        self.K_cf = xor_bytes(self.storage['RK_cf'], pad_to_length(self.FID_j, 20))
        self.b_j = xor_bytes(self.storage['Rb_j'], h(self.FID_j + self.K_cf))

    def generate_m2(self, RID_i, P_i, F_i, T_1):
        
        if abs(int(time.time()) - bytes_to_int(T_1)) > DELTA_T:
            raise ValueError("F_j: T1 is not fresh. Aborting.")

        self._recover_secrets()
        
        self.Q_i = bytes_to_int(self.b_j) * P_i
        self.r_3_prime = xor_bytes(F_i, int_to_bytes(self.Q_i.x)[:20])  # Truncate Q_i.x to 20 bytes
        self.R_i = xor_bytes(RID_i, int_to_bytes(self.Q_i.x)[:8])  # Truncate Q_i.x to 8 bytes
        self.RID_i = RID_i

        self.r_4 = random_nonce()  # 20 bytes
        T_2 = int_to_bytes(int(time.time()), 4)  # 32 bits = 4 bytes

        W_i = xor_bytes(self.r_4, h(self.K_cf + pad_to_length(self.FID_j, 20)))
        X_i = xor_bytes(self.storage['PFD_j'], h(self.FID_j + xor_bytes(self.K_cf, self.r_4)))
        Y_i = xor_bytes(pad_to_length(self.R_i, 20), h(self.K_cf + self.r_4))  # Pad R_i to 20 bytes
        D = h(self.storage['PFD_j'] + self.r_4 + xor_bytes(pad_to_length(self.R_i, 20), self.K_cf))  # Pad R_i to 20 bytes

        return W_i, X_i, Y_i, D, T_2

    def generate_m4(self, L_i, Z_i, T_3):
        
        if abs(int(time.time()) - bytes_to_int(T_3)) > DELTA_T:
            raise ValueError("F_j: T3 is not fresh. Aborting.")

        r_5_star = xor_bytes(L_i, h(xor_bytes(self.K_cf, pad_to_length(self.FID_j, 20)) + self.r_4))
        SK_star = h(self.storage['PFD_j'] + pad_to_length(self.R_i, 20) + self.r_4 + xor_bytes(r_5_star, self.K_cf))  # Pad R_i to 20 bytes
        
        Z_i_star = h(SK_star + xor_bytes(self.K_cf, pad_to_length(self.FID_j, 20)))

        if Z_i_star != Z_i:
            raise ValueError("F_j: Z_i* verification failed. Aborting.")

        self.session_key = SK_star
        T_4 = int_to_bytes(int(time.time()), 4)  # 32 bits = 4 bytes

        J_i = h(self.RID_i + xor_bytes(self.r_3_prime, int_to_bytes(self.Q_i.x)[:20]))  # Truncate Q_i.x to 20 bytes
        N_i = xor_bytes(h(xor_bytes(pad_to_length(self.FID_j, 20), int_to_bytes(self.Q_i.x)[:20]) + self.R_i), self.session_key)  # Truncate Q_i.x to 20 bytes

        return N_i, J_i, T_4
