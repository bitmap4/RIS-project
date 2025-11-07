import time
import secrets
from .common import h, G, CURVE, ORDER, xor_bytes, int_to_bytes, bytes_to_int, random_nonce, DELTA_T, pad_to_length

class Vehicle:
    def __init__(self, VID_i, VPW_i):
        # VID and VPW must be 8 bytes (64 bits) as per scheme specification
        if isinstance(VID_i, str):
            VID_i = VID_i.encode()[:8].ljust(8, b'\x00')
        if isinstance(VPW_i, str):
            VPW_i = VPW_i.encode()[:8].ljust(8, b'\x00')
        self.VID_i = VID_i
        self.VPW_i = VPW_i
        self.r_1 = random_nonce()
        self.smart_card = {}
        self.session_key = None
        self.r_3 = None
        self.r_3_prime = None
        self.Q_i = None
        self.RID_i = None

    def register(self, cs):
        """Phase 2: V_i Registration"""
        PV_i = h(self.VID_i + self.VPW_i + self.r_1)
        MV_i = cs.register_vehicle(self.VID_i, PV_i)
        
        a_i = xor_bytes(MV_i, PV_i)
        TV_i = h(xor_bytes(self.VID_i, self.VPW_i) + a_i)
        
        self.smart_card['TV_i'] = TV_i
        self.smart_card['MV_i'] = MV_i
        self.smart_card['r_1'] = self.r_1

    def login_and_verify(self, VID_i_star, VPW_i_star):
        """Phase 4, Step 1: V_i Login and Verification"""
        if 'r_1' not in self.smart_card or 'MV_i' not in self.smart_card:
            raise ValueError("Vehicle not registered.")

        PV_i = h(VID_i_star + VPW_i_star + self.smart_card['r_1'])
        a_i = xor_bytes(self.smart_card['MV_i'], PV_i)
        TV_i_star = h(xor_bytes(VID_i_star, VPW_i_star) + a_i)

        if TV_i_star != self.smart_card['TV_i']:
            raise ValueError("Login failed: TV_i does not match.")
        
        return a_i

    def generate_m1(self, FID_j, B_j):
        """Phase 4, Step 2: V_i -> F_j (Message M1)"""
        self.r_3 = secrets.randbelow(ORDER)
        self.r_3_prime = random_nonce()  # 20 bytes
        T_1 = int_to_bytes(int(time.time()), 4)  # 32 bits = 4 bytes

        P_i = self.r_3 * G
        self.Q_i = self.r_3 * B_j
        
        # As per flaw, V_i needs FID_j
        self.RID_i = xor_bytes(self.VID_i, xor_bytes(int_to_bytes(self.Q_i.x)[:8], pad_to_length(FID_j, 8)))
        F_i = xor_bytes(self.r_3_prime, int_to_bytes(self.Q_i.x)[:20])  # Truncate Q_i.x to 20 bytes

        return self.RID_i, P_i, F_i, T_1

    def establish_session_key(self, N_i, J_i, T_4, FID_j):
        """Phase 4, Step 6: V_i Session Key Establishment"""
        if abs(int(time.time()) - bytes_to_int(T_4)) > DELTA_T:
            raise ValueError("V_i: T4 is not fresh. Aborting.")
        
        J_i_star = h(self.RID_i + xor_bytes(self.r_3_prime, int_to_bytes(self.Q_i.x)[:20]))  # Truncate Q_i.x to 20 bytes
        if J_i_star != J_i:
            raise ValueError("V_i: J_i* verification failed. Aborting.")

        # As per flaw, V_i needs FID_j
        VID_i_xor_FID_j = xor_bytes(self.VID_i, pad_to_length(FID_j, 8))
        self.session_key = xor_bytes(N_i, h(xor_bytes(pad_to_length(FID_j, 20), int_to_bytes(self.Q_i.x)[:20]) + VID_i_xor_FID_j))  # Truncate Q_i.x to 20 bytes
        return self.session_key
