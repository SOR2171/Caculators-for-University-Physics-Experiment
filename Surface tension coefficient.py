import math
from decimal import Decimal, ROUND_HALF_EVEN

"""
Surface Tension Coefficient Calculator (Pull-off Method)
拉脱法测液体表面张力系数计算器

参考了杨氏模量及粘滞系数代码的高精度与不确定度修约逻辑。

公式说明:
1. 表面张力系数计算公式:
   α = F / [π * (d1 + d2)]
   其中:
   F  : 拉脱力，通过传感器测得 F = U / K (K为传感器灵敏度)
   d1 : 铁环内径
   d2 : 铁环外径
   
2. 传感器灵敏度 K (通过砝码标定):
   测得 2 组不同砝码个数 i (0~5) 下的电压 U1_i 与 U2_i (通常为增重与减重过程)。
   取其平均值 U_avg_i = (U1_i + U2_i) / 2。
   设单个砝码质量为 m，则受力 F_i = i * m * g。
   使用最小二乘法对 (F_i, U_avg_i) 进行线性回归，斜率即为灵敏度 K (V/N)。

3. 不确定度传递公式 (相对不确定度):
   假定 K 的不确定度 u_K 通过线性回归标准差求得。
   
   拉脱力 F 的平均值: F_mean = U_pull_mean / K
   拉脱力 F 的不确定度 (相对不确定度):
   u_r(F) = sqrt( (u_U / U_pull_mean)^2 + (u_K / K)^2 )
   
   内外径和(d1+d2)的不确定度:
   u_d_sum = sqrt( u_d1^2 + u_d2^2 )
   u_r(d_sum) = u_d_sum / (d1_mean + d2_mean)
   
   总相对不确定度:
   u_r(α) = u_α / α = sqrt( u_r(F)^2 + u_r(d_sum)^2 )
   
   绝对不确定度:
   u_α = α * u_r(α)
   
   对于多次测量量 X 的不确定度:
   u_X = sqrt( u_A,X^2 + u_B,X^2 )
   u_A,X = s_X / sqrt(n)
   u_B,X = Δ_inst / sqrt(3)
"""

from utils import (
    scientific_round,
    calculate_stats,
    linear_regression,
    input_data_group
)

def main():
    print("========================================")
    print("      拉脱法测水表面张力系数计算器      ")
    print("========================================")
    
    # --- 1. 常量设置 ---
    G = Decimal("9.80")          # 重力加速度 m/s^2
    PI = Decimal(str(math.pi))
    print(f"重力加速度 g = {G} m/s^2")
    print(f"圆周率 π ≈ {PI:.5f}")
    
    print("\n--- 砝码参数与标定 ---")
    m_default = "0.5"
    m_input = input(f"单个小砝码质量 m (g, 默认 {m_default}): ").strip() or m_default
    m_mass = Decimal(m_input) / Decimal("1000") # 转为 kg
    
    print("\n请输入力敏传感器标定电压 (共 2 组，0~5 个小砝码，例如：第 1 组为增重，第 2 组为减重):")
    
    print("\n--- 输入第 1 组标定电压 (U1) ---")
    U_calib_1 = []
    for i in range(6):
        while True:
            try:
                val = input(f"第1组 - 放 {i} 个砝码时的电压 U1 (V或mV, 请统一单位) = ").strip()
                if not val: continue
                U_calib_1.append(Decimal(val))
                break
            except Exception:
                print("输入无效，请输入数字。")
                
    print("\n--- 输入第 2 组标定电压 (U2) ---")
    U_calib_2 = []
    for i in range(6):
        while True:
            try:
                val = input(f"第2组 - 放 {i} 个砝码时的电压 U2 (V或mV, 请统一单位) = ").strip()
                if not val: continue
                U_calib_2.append(Decimal(val))
                break
            except Exception:
                print("输入无效，请输入数字。")
                
    # 计算两组的平均电压并生成对应的受力
    U_calib_avg = []
    F_calib = []
    for i in range(6):
        avg_val = (U_calib_1[i] + U_calib_2[i]) / Decimal("2")
        U_calib_avg.append(avg_val)
        F_calib.append(Decimal(str(i)) * m_mass * G)
        
    # 打印标定数据对照表
    print("\n" + "-"*65)
    print(f"{'砝码数':<6} | {'受力 F (N)':<12} | {'第1组 U1':<10} | {'第2组 U2':<10} | {'平均 U_avg':<10}")
    print("-"*65)
    for i in range(6):
        print(f"{i:<8} | {F_calib[i]:<12.6f} | {U_calib_1[i]:<10.4f} | {U_calib_2[i]:<10.4f} | {U_calib_avg[i]:<10.4f}")
    print("-"*65)
                
    # 计算灵敏度 K
    K, K_b, r, u_K = linear_regression(F_calib, U_calib_avg)
    print(f"\n[标定结果] 传感器灵敏度 K = {K:.6f}, 截距 = {K_b:.6f}")
    print(f"线性相关系数 r = {r:.6f}, 斜率不确定度 u_K = {u_K:.6e}")
    
    # --- 2. 拉脱测量与仪器误差输入 ---
    print("\n--- 输入仪器误差 Δ_inst ---")
    delta_U = Decimal(input("电压 U 的仪器误差 (默认 0.001): ").strip() or "0.001")
    delta_d = Decimal(input("游标卡尺测量内外径的仪器误差 (mm, 默认 0.02): ").strip() or "0.02")
    
    # 输入拉脱电压 U_pull (6次)
    U_pull_vals = input_data_group("拉脱时的电压差/峰值电压 U_pull", 6, "同标定电压单位")
    U_pull_mean, U_pull_u = calculate_stats(U_pull_vals, delta_U)[:2]
    
    # 输入内径 d1 (6次)
    d1_vals = input_data_group("铁环内径 d1", 6, "mm")
    d1_mean, d1_u = calculate_stats(d1_vals, delta_d)[:2]
    
    # 输入外径 d2 (6次)
    d2_vals = input_data_group("铁环外径 d2", 6, "mm")
    d2_mean, d2_u = calculate_stats(d2_vals, delta_d)[:2]
    
    # --- 3. 表面张力系数计算 ---
    # F = U / K
    F_pull_mean = U_pull_mean / K
    
    # 统一转化内径、外径为国际标准单位 m
    d1_m = d1_mean / Decimal("1000")
    d2_m = d2_mean / Decimal("1000")
    
    d1_u_m = d1_u / Decimal("1000")
    d2_u_m = d2_u / Decimal("1000")
    
    # α = F / [π * (d1 + d2)]
    d_sum = d1_m + d2_m
    alpha_val = F_pull_mean / (PI * d_sum)
    
    # --- 4. 不确定度传播 ---
    # u_r(F) = sqrt( (u_U / U_pull_mean)^2 + (u_K / K)^2 )
    u_r_F_sq = (U_pull_u / U_pull_mean)**2 + (u_K / K)**2
    u_r_F = Decimal(str(math.sqrt(float(u_r_F_sq))))
    
    # u(d1 + d2)
    u_d_sum = Decimal(str(math.sqrt(float(d1_u_m**2 + d2_u_m**2))))
    u_r_d_sum = u_d_sum / d_sum
    
    # u_r(α) = sqrt( u_r(F)^2 + u_r(d_sum)^2 )
    u_r_alpha = Decimal(str(math.sqrt(float(u_r_F**2 + u_r_d_sum**2))))
    
    # 绝对不确定度
    alpha_u = alpha_val * u_r_alpha
    
    # --- 5. 修约与输出 ---
    alpha_final, u_final = scientific_round(alpha_val, alpha_u)
    
    print("\n" + "="*40)
    print("             计算结果")
    print("="*40)
    print(f"拉脱电压 U_pull = {U_pull_mean:.4f} ± {U_pull_u:.4f}")
    print(f"拉脱力 F        = {F_pull_mean:.6f} N")
    print(f"铁环内径 d1     = {d1_mean:.3f} ± {d1_u:.3f} mm")
    print(f"铁环外径 d2     = {d2_mean:.3f} ± {d2_u:.3f} mm")
    print("-" * 40)
    print(f"相对不确定度 u_r = {u_r_alpha*100:.2f}%")
    print(f"绝对不确定度 u_α = {alpha_u:.6f} N/m")
    print("-" * 40)
    print(f"最终表面张力系数: α = {alpha_final} ± {u_final} N/m")
    print("="*40)

if __name__ == "__main__":
    main()
