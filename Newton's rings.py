import math
from decimal import Decimal, ROUND_HALF_EVEN

"""
Newton's Rings Curvature Radius Calculator (Successive Difference Method)
牛顿环曲率半径计算器 (逐差法)

参考 lenth.py 的高精度与不确定度修约逻辑。
"""

from utils import get_decimal_places, scientific_round

def main():
    # --- 1. 参数与常量初始化 ---
    WAVELENGTH = Decimal("0.0005893")  # 钠光波长默认 589.3 nm = 0.0005893 mm
    M = 10  # 逐差法的差值项数 (30-20=10)
    
    print("========================================")
    print("      牛顿环曲率半径计算 (逐差法)       ")
    print("========================================")
    print(f"默认波长 λ = {WAVELENGTH} mm (钠光)")
    print("参考环数: 第 11 环 到 第 30 环 (共 20 个数据)")
    
    # --- 2. 数据输入 ---
    d_squared_vals = []
    data_strs = []
    print("\n[第一步] 请输入暗环直径平方 D^2 (单位: mm^2)")
    print("支持粘贴或逐个输入，精确到小数点后三位。")
    
    for i in range(11, 31):
        while True:
            try:
                user_input = input(f"D_{i:02d}^2 = ").strip()
                if not user_input:
                    continue
                val = Decimal(user_input)
                d_squared_vals.append(val)
                data_strs.append(user_input)
                break
            except Exception:
                print("无效输入！请输入正确的直径平方值（如 12.345）。")
    
    print("\n[第二步] 仪器参数输入")
    res_input = input("请输入仪器分度值 (默认 0.01 mm): ").strip() or "0.01"
    delta_inst_input = input("请输入仪器误差 Δ_inst (默认 0.005 mm): ").strip() or "0.005"
    
    res = Decimal(res_input)
    delta_inst = Decimal(delta_inst_input)
    
    # --- 3. 逐差计算 ---
    # Δ_i = D_{i+M}^2 - D_i^2  (i = 11...20)
    deltas = []
    sum_d_pairs = Decimal("0") # 用于 B 类不确定度传播: sum(D_low^2 + D_high^2)
    
    print("\n--- 逐差过程 ---")
    for i in range(10):
        d_low_sq = d_squared_vals[i]
        d_high_sq = d_squared_vals[i + 10]
        diff = d_high_sq - d_low_sq
        deltas.append(diff)
        sum_d_pairs += (d_low_sq + d_high_sq)
        print(f"Δ_{i+11:02d} = D_{i+21}^2 - D_{i+11}^2 = {diff} mm^2")
    
    mean_delta = sum(deltas) / Decimal(str(M))
    
    # --- 4. 曲率半径计算 ---
    # R = Δ_avg / (4 * M * λ)
    # M = 10, 所以分母是 40 * λ
    denominator = Decimal("4") * Decimal(str(M)) * WAVELENGTH
    r_val = mean_delta / denominator
    
    # --- 5. 不确定度计算 ---
    # (1) A 类不确定度 u_A (针对逐差后的 Δ)
    variance_delta = sum((x - mean_delta)**2 for x in deltas) / Decimal(str(M - 1))
    s_delta = Decimal(str(math.sqrt(float(variance_delta))))
    u_a_delta = s_delta / Decimal(str(math.sqrt(M)))
    
    # (2) B 类不确定度 u_B (传播自读数显微镜的仪器误差)
    # 推导过程:
    # u(x) = delta_inst / sqrt(3)
    # u(D^2) = sqrt( (2D u_x)^2 + (2D u_x)^2 ) = 2 * sqrt(2) * D * u_x
    # u(D^2)^2 = 8 * D^2 * u_x^2
    # u(Δ)^2 = u(D_high^2)^2 + u(D_low^2)^2 = 8 * u_x^2 * (D_high^2 + D_low^2)
    # u(Δ_avg)^2 = (1/M^2) * sum( u(Δ_i)^2 ) = (8 * u_x^2 / M^2) * sum_d_pairs
    u_x = delta_inst / Decimal(str(math.sqrt(3)))
    u_b_delta_sq = (Decimal("8") * (u_x**2) * sum_d_pairs) / (Decimal(str(M))**2)
    u_b_delta = Decimal(str(math.sqrt(float(u_b_delta_sq))))
    
    # (3) 合成不确定度 u(Δ) 并在 R 上传播
    u_delta_combined = Decimal(str(math.sqrt(float(u_a_delta**2 + u_b_delta**2))))
    u_r = u_delta_combined / denominator
    
    # --- 6. 修约与展示 ---
    r_final, u_final = scientific_round(r_val, u_r)
    
    print("\n--- 中间统计结果 (高精度) ---")
    print(f"平均差值 Δ_avg: {mean_delta:.6f} mm^2")
    print(f"Δ 的标准差 s: {s_delta:.6f}")
    print(f"Δ 的 A 类不确定度 u_A(Δ): {u_a_delta:.6f}")
    print(f"Δ 的 B 类不确定度 u_B(Δ): {u_b_delta:.6f}")
    
    print("\n--- 最终计算结果 (R) ---")
    print(f"曲率半径 R (原始): {r_val:.4f} mm")
    print(f"R 的合成不确定度 u(R): {u_r:.4f} mm")
    
    print("\n========================================")
    print("     最终修约结果 (四舍六入五凑偶)")
    print(f"     R = {r_final} ± {u_final} mm")
    print("========================================")

if __name__ == "__main__":
    main()
