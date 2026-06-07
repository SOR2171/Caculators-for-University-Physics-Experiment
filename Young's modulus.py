import math
from decimal import Decimal, ROUND_HALF_EVEN

"""
Young's Modulus Calculator (Optical Lever & Successive Difference Method)
杨氏模量计算器 (光杠杆 & 逐差法)

不确定度传递公式:
1. 杨氏模量公式:
   E = (32 * m * g * L * D) / (π * d^2 * b * Δn_avg)
   其中 Δn_avg 是 4 个砝码对应的平均刻度位移（由 8 个刻度值通过逐差法求得）。

2. 相对不确定度传递公式:
   u_r(E) = u_E / E = sqrt( (u_L/L)^2 + (u_D/D)^2 + (2 * u_d/d)^2 + (u_b/b)^2 + (u_Δn/Δn_avg)^2 )
   
3. 合成不确定度:
   u_E = E * u_r(E)
   其中各物理量 X 的不确定度 u_X = sqrt( u_A,X^2 + u_B,X^2 )
   u_A,X = s_X / sqrt(n)
   u_B,X = Δ_inst / sqrt(3)
"""

def scientific_round(value, uncertainty):
    """
    按照“四舍六入五凑偶”修约：
    1. 不确定度 u 保留一位有效数字（若首位是1或2，有时保留两位，此处统一保留一位）
    2. 平均值末位与 u 对齐
    """
    if uncertainty <= 0:
        return str(value), "0"
    
    u_float = float(uncertainty)
    # 找到第一位非零数字的位置
    first_digit_pos = math.floor(math.log10(u_float))
    prec = Decimal('1e' + str(first_digit_pos))
    
    # 不确定度修约
    u_final = uncertainty.quantize(prec, rounding=ROUND_HALF_EVEN)
    # 平均值修约，保持与不确定度末位对齐
    val_final = value.quantize(prec, rounding=ROUND_HALF_EVEN)
    
    return val_final, u_final

def calculate_stats(data_list, delta_inst):
    """计算一组数据的平均值、A类、B类及合成不确定度"""
    n = len(data_list)
    mean = sum(data_list) / Decimal(n)
    
    # A类不确定度
    if n > 1:
        variance = sum((x - mean)**2 for x in data_list) / Decimal(n - 1)
        s = Decimal(str(math.sqrt(float(variance))))
        u_a = s / Decimal(str(math.sqrt(n)))
    else:
        u_a = Decimal("0")
        
    # B类不确定度
    u_b = Decimal(delta_inst) / Decimal(str(math.sqrt(3)))
    
    # 合成
    u_combined = Decimal(str(math.sqrt(float(u_a**2 + u_b**2))))
    
    return mean, u_combined

def input_data_group(name, count, unit="mm"):
    """输入一组重复测量的数值"""
    print(f"\n请输入 {name} 的 {count} 次测量值 (单位: {unit}):")
    data = []
    for i in range(count):
        while True:
            try:
                val = input(f"{name}_{i+1} = ").strip()
                if not val: continue
                data.append(Decimal(val))
                break
            except Exception:
                print("输入无效，请输入数字。")
    return data

def main():
    # --- 1. 常量设置 ---
    M_WEIGHT = Decimal("0.350")  # 单个砝码质量 350g = 0.350kg
    G = Decimal("9.80")          # 重力加速度
    PI = Decimal(str(math.pi))
    
    print("========================================")
    print("      杨氏模量计算 (光杠杆 & 逐差法)    ")
    print("========================================")
    print(f"单个砝码质量 m = {M_WEIGHT} kg")
    print(f"重力加速度 g = {G} m/s^2")
    
    # --- 2. 几何长度输入 (各6次测量) ---
    # L: 钢丝长度, D: 镜面到刻度尺距离, d: 钢丝直径, b: 光杠杆臂长
    L_vals = input_data_group("钢丝长度 L", 6, "mm")
    D_vals = input_data_group("镜面到尺距离 D", 6, "mm")
    d_vals = input_data_group("钢丝直径 d", 6, "mm")
    b_vals = input_data_group("光杠杆臂长 b", 6, "mm")
    
    print("\n--- 输入仪器误差 Δ_inst ---")
    delta_L = Decimal(input("L 的仪器误差 (mm, 默认 1.0): ").strip() or "1.0")
    delta_D = Decimal(input("D 的仪器误差 (mm, 默认 1.0): ").strip() or "1.0")
    delta_d = Decimal(input("d 的仪器误差 (mm, 默认 0.005): ").strip() or "0.005")
    delta_b = Decimal(input("b 的仪器误差 (mm, 默认 0.02): ").strip() or "0.02")
    
    L_mean, L_u = calculate_stats(L_vals, delta_L)
    D_mean, D_u = calculate_stats(D_vals, delta_D)
    d_mean, d_u = calculate_stats(d_vals, delta_d)
    b_mean, b_u = calculate_stats(b_vals, delta_b)
    
    # --- 3. 刻度值输入 (0-7个砝码, 加重+减重) ---
    print("\n--- 输入刻度尺读数 n (单位: mm) ---")
    n_up = []
    n_down = []
    for i in range(8):
        while True:
            try:
                line = input(f"砝码数量 {i} (加重, 减重): ").replace(',', ' ').split()
                if len(line) != 2:
                    print("请输入两个数值（空格或逗号隔开）")
                    continue
                n_up.append(Decimal(line[0]))
                n_down.append(Decimal(line[1]))
                break
            except Exception:
                print("输入无效！")
                
    delta_n_inst = Decimal(input("刻度尺仪器误差 (mm, 默认 0.5): ").strip() or "0.5")
    
    # 计算平均读数 n_i
    n_means = [(u + d) / 2 for u, d in zip(n_up, n_down)]
    
    print("\n--- 中间量 (加重与减重的平均值 n_i) ---")
    for i, val in enumerate(n_means):
        print(f"n_{i} = {val} mm")
    
    # 逐差法计算 Δn (隔 4 项相减)
    # Δn_j = n_{j+4} - n_j, j = 0,1,2,3
    dn_list = []
    print("\n--- 逐差计算过程 ---")
    for j in range(4):
        diff = n_means[j+4] - n_means[j]
        dn_list.append(diff)
        print(f"Δn_{j} = n_{j+4} - n_{j} = {diff} mm")
    
    # Δn 的平均值及不确定度
    dn_mean = sum(dn_list) / Decimal("4")
    # A类: 针对这 4 个差值
    variance_dn = sum((x - dn_mean)**2 for x in dn_list) / Decimal("3")
    s_dn = Decimal(str(math.sqrt(float(variance_dn))))
    u_a_dn = s_dn / Decimal(str(math.sqrt(4)))
    
    # B类: 刻度尺误差
    # 因为 n_i = (n_up + n_down)/2, Δn = n_high - n_low
    # 传播得 u_B(Δn) = Δ_inst / sqrt(3)
    u_b_dn = delta_n_inst / Decimal(str(math.sqrt(3)))
    dn_u = Decimal(str(math.sqrt(float(u_a_dn**2 + u_b_dn**2))))
    
    # --- 4. 杨氏模量计算 ---
    # 全部转为标准单位 (m)
    L_m = L_mean / 1000
    D_m = D_mean / 1000
    d_m = d_mean / 1000
    b_m = b_mean / 1000
    dn_m = dn_mean / 1000
    
    # E = (32 * m * g * L * D) / (pi * d^2 * b * Δn)
    # 这里的 Δn 对应 4 个砝码的位移
    numerator = Decimal("32") * M_WEIGHT * G * L_m * D_m
    denominator = PI * (d_m**2) * b_m * dn_m
    E_val = numerator / denominator
    
    # --- 5. 不确定度传播 ---
    # rel_u = sqrt( (uL/L)^2 + (uD/D)^2 + (2*ud/d)^2 + (ub/b)^2 + (udn/dn)^2 )
    rel_u_sq = (L_u/L_mean)**2 + (D_u/D_mean)**2 + (Decimal("2")*d_u/d_mean)**2 + (b_u/b_mean)**2 + (dn_u/dn_mean)**2
    rel_u = Decimal(str(math.sqrt(float(rel_u_sq))))
    E_u = E_val * rel_u
    
    # --- 6. 修约与输出 ---
    # 通常用 10^11 Pa 表示
    E_11 = E_val / Decimal("1e11")
    E_u_11 = E_u / Decimal("1e11")
    
    E_final, u_final = scientific_round(E_11, E_u_11)
    
    print("\n" + "="*40)
    print("             计算结果")
    print("="*40)
    print(f"L  = {L_mean:.2f} ± {L_u:.2f} mm")
    print(f"D  = {D_mean:.2f} ± {D_u:.2f} mm")
    print(f"d  = {d_mean:.4f} ± {d_u:.4f} mm")
    print(f"b  = {b_mean:.3f} ± {b_u:.3f} mm")
    print(f"Δn = {dn_mean:.3f} ± {dn_u:.3f} mm (4个砝码位移)")
    print("-" * 40)
    print(f"杨氏模量 E (原始): {E_val:.4e} Pa")
    print(f"相对不确定度 u_r: {rel_u*100:.2f}%")
    print("-" * 40)
    print(f"最终结果: E = {E_final} ± {u_final} × 10^11 Pa")
    print("="*40)

if __name__ == "__main__":
    main()
