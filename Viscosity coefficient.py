import math
from decimal import Decimal, ROUND_HALF_EVEN

"""
Viscosity Coefficient Calculator (Stokes' Law)
蓖麻油粘滞系数计算器 (斯托克斯定律)

参考了杨氏模量代码的高精度与不确定度修约逻辑。
（注：由于实验提供的是同一距离20cm的5次重复时间测量，此处直接求平均计算，不适用逐差法。逐差法通常用于等间距的多组累积物理量测量。）

公式说明:
1. 粘滞系数计算公式 (考虑管壁修正):
   η = (ρ - ρ0) * g * d^2 * t / [18 * l * (1 + 2.4 * d/D)]
   其中:
   ρ  : 小球密度
   ρ0 : 液体(蓖麻油)密度
   d  : 小球直径
   D  : 玻璃管内径
   l  : 下落距离
   t  : 下落平均时间

2. 雷诺数 (Re) 判断和修正公式:
   Re = ρ0 * v * d / η
   其中 v = l / t。
   当 Re < 0.1 时，斯托克斯定律完全适用。
   当 0.1 <= Re <= 1.0 时，可使用奥辛(Oseen)修正:
   η_corrected = η / (1 + 3/16 * Re)

3. 不确定度传递公式 (相对不确定度):
   假定 ρ, ρ0, g 的不确定度可忽略，则:
   u_r(η) = u_η / η = sqrt( (2 * u_d / d)^2 + (u_t / t)^2 + (u_l / l)^2 + (u_D / D)^2 )
   
   绝对不确定度:
   u_η = η * u_r(η)
   
   其中各个量 X 的不确定度 u_X = sqrt( u_A,X^2 + u_B,X^2 )
   u_A,X = s_X / sqrt(n)
   u_B,X = Δ_inst / sqrt(3)
"""

from utils import (
    scientific_round,
    calculate_stats,
    input_data_group
)

def main():
    print("========================================")
    print("       蓖麻油粘滞系数计算 (斯托克斯定律)      ")
    print("========================================")
    
    # --- 1. 常量设置 ---
    G = Decimal("9.80")          # 重力加速度 m/s^2
    RHO_BALL = Decimal("7800")   # 钢球密度 kg/m^3 (默认为钢球，通常实验室用此值)
    RHO_OIL = Decimal("960")     # 蓖麻油密度 kg/m^3 (随温度变化，常温附近约 960)
    
    print(f"重力加速度 g = {G} m/s^2")
    print(f"小球密度 ρ = {RHO_BALL} kg/m^3")
    print(f"蓖麻油密度 ρ0 = {RHO_OIL} kg/m^3")
    
    # --- 2. 测量数据输入 ---
    print("\n--- 仪器与实验参数设定 ---")
    D_mean = Decimal("20.0")
    d_mean = Decimal("1.0")
    l_mean = Decimal("20.0") # 默认单位 cm，后续转化为 mm 或 m 计算
    
    ans = input("使用默认参数 (玻璃管直径D=20mm, 小球直径d=1mm, 下落距离l=20cm) 吗？[Y/n]: ").strip().lower()
    if ans == 'n':
        D_mean = Decimal(input("玻璃管直径 D (mm): ").strip() or "20.0")
        d_mean = Decimal(input("小球直径 d (mm): ").strip() or "1.0")
        l_mean = Decimal(input("下落距离 l (cm): ").strip() or "20.0")
    
    l_mean_mm = l_mean * Decimal("10") # 统一 cm 转为 mm
    
    print("\n--- 输入仪器误差 Δ_inst ---")
    delta_D = Decimal(input("D 的仪器误差 (mm, 默认 0): ").strip() or "0")
    delta_d = Decimal(input("d 的仪器误差 (mm, 默认 0): ").strip() or "0")
    delta_l = Decimal(input("l 的仪器误差 (mm, 默认 0): ").strip() or "0")
    delta_t = Decimal(input("t(时间)的仪器误差 (s, 默认 0.01): ").strip() or "0.01")
    
    # D, d, l 我们假设只进行了单次测量或作为已知常数处理，所以只算B类不确定度
    D_u = delta_D / Decimal(str(math.sqrt(3)))
    d_u = delta_d / Decimal(str(math.sqrt(3)))
    l_u = delta_l / Decimal(str(math.sqrt(3)))
    
    # 输入5个时间数据
    t_vals = input_data_group("小球下落时间 t", 5, "s")
    t_mean, t_u = calculate_stats(t_vals, delta_t)[:2]
    
    # --- 3. 粘滞系数计算 ---
    # 统一转化为国际标准单位 (m, kg, s)
    D_m = D_mean / Decimal("1000")
    d_m = d_mean / Decimal("1000")
    l_m = l_mean_mm / Decimal("1000")
    
    # η = (ρ - ρ0) * g * d^2 * t / [18 * l * (1 + 2.4 * d/D)]
    correction_factor = Decimal("1") + Decimal("2.4") * (d_m / D_m)
    numerator = (RHO_BALL - RHO_OIL) * G * (d_m**2) * t_mean
    denominator = Decimal("18") * l_m * correction_factor
    eta_val = numerator / denominator
    
    # --- 4. 雷诺数判断与修正 ---
    # v = l / t
    v_val = l_m / t_mean
    # Re = ρ0 * v * d / η
    Re = RHO_OIL * v_val * d_m / eta_val
    
    eta_corrected = eta_val
    if Re > Decimal("0.1"):
        # Oseen 修正
        eta_corrected = eta_val / (Decimal("1") + Decimal("3") / Decimal("16") * Re)
    
    # --- 5. 不确定度传播 ---
    # 相对不确定度平方和
    rel_u_sq = (Decimal("2") * d_u / d_mean)**2 + (t_u / t_mean)**2 + (l_u / l_mean_mm)**2 + (D_u / D_mean)**2
    rel_u = Decimal(str(math.sqrt(float(rel_u_sq))))
    
    # 绝对不确定度
    eta_u = eta_corrected * rel_u
    
    # --- 6. 修约与输出 ---
    eta_final, u_final = scientific_round(eta_corrected, eta_u)
    
    print("\n" + "="*40)
    print("             计算结果")
    print("="*40)
    print(f"下落时间 t  = {t_mean:.3f} ± {t_u:.3f} s")
    print(f"下落速度 v  = {v_val:.5f} m/s")
    print("-" * 40)
    print(f"雷诺数 Re = {Re:.4f}")
    if Re <= Decimal("0.1"):
        print("Re <= 0.1，满足斯托克斯定律条件，无需 Oseen 修正。")
    else:
        print("Re > 0.1，已应用 Oseen 修正。")
        print(f"修正前 η = {eta_val:.4f} Pa·s")
    print("-" * 40)
    print(f"相对不确定度 u_r = {rel_u*100:.2f}%")
    print(f"绝对不确定度 u_η = {eta_u:.4f} Pa·s")
    print("-" * 40)
    print(f"最终结果: η = {eta_final} ± {u_final} Pa·s")
    print("="*40)

if __name__ == "__main__":
    main()
