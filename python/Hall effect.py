import math

"""
Hall Effect Experiment Data Processor
霍尔效应实验数据处理计算器 (直接输入 VH 版)

参考了表面张力系数计算器的高精度与不确定度修约逻辑。

═══════════════════════════════════════════════════════
公式说明:
═══════════════════════════════════════════════════════

1. 霍尔电压 (Hall Voltage):
   直接测量输入 VH。
   VH > 0 → P 型 (空穴导电)
   VH < 0 → N 型 (电子导电)

2. 霍尔效应基本公式 (Hall Effect):
   VH = KH · Is · B

   其中:
     KH = 1 / (n · e · d)   — 霍尔灵敏度  [V/(A·T)]
     RH = 1 / (n · e)       — 霍尔系数    [m³/C]
     Is : 工作电流 (霍尔电流) [A]
     B  : 磁感应强度          [T]
     d  : 霍尔元件厚度        [m]
     n  : 载流子浓度          [m⁻³]
     e  : 元电荷 = 1.602×10⁻¹⁹ [C]

3. 电导率 σ 计算 (Conductivity):
   σ = Is · L / (Vσ · b · d)

   线性回归 Vσ vs Is，斜率 R_slope = Vσ/Is (即样品电阻 [Ω])，则:
   σ = L / (R_slope · b · d)    [S/m]

   其中:
     L : 电压电极间距 (霍尔片长度) [m]
     b : 霍尔片宽度               [m]
     d : 霍尔片厚度               [m]

4. 载流子浓度 n 与迁移率 μ (Carrier Concentration & Mobility):
   n = 1 / (KH · e · d) = 1 / (RH · e)         [m⁻³]
   μ = σ / (n · e)      = σ · RH = σ · KH · d   [m²/(V·s)]

5. 螺线管中心磁场 (Solenoid Field):
   B = μ₀ · (N / L_sol) · Im
   其中:
     μ₀    = 4π×10⁻⁷ T·m/A (真空磁导率)
     N     : 螺线管总匝数
     L_sol : 螺线管有效长度 [m]

═══════════════════════════════════════════════════════
不确定度传递公式:
═══════════════════════════════════════════════════════

(a) 线性回归斜率不确定度:
    u(k) = |k| · √[(1/r² − 1) / (n − 2)]
    其中 r 为相关系数, n 为数据点数

(b) 电导率 σ 的不确定度:
    σ = L / (R_slope · b · d)
    u_r(σ) = √[(u_R/R)² + (u_L/L)² + (u_b/b)² + (u_d/d)²]

(c) 霍尔灵敏度 KH 的不确定度:
    KH = slope₁ / B
    u_r(KH) = √[(u_slope₁/slope₁)² + (u_B/B)²]

(d) 载流子浓度 n 的不确定度:
    n = 1 / (KH · e · d)
    u_r(n) = √[u_r(KH)² + (u_d/d)²]

(e) 载流子迁移率 μ 的不确定度:
    μ = σ · KH · d
    u_r(μ) = √[u_r(σ)² + u_r(KH)² + (u_d/d)²]

(f) 修约规则:
    不确定度保留一位有效数字 (四舍六入五凑偶)
    结果末位与不确定度对齐
"""

# ═══════════════════════════════════════════════════════
#  通用工具函数
# ═══════════════════════════════════════════════════════

from utils import (
    scientific_round,
    linear_regression,
    input_float
)


def print_regression(label, k, b, r, u_k, x_unit, y_unit):
    """格式化打印线性回归结果"""
    print(f"\n  [{label}] 线性回归结果:")
    print(f"    y = {k:.6f} · x + ({b:.6f})")
    print(f"    斜率 k  = {k:.6f} {y_unit}/{x_unit}")
    print(f"    截距 b  = {b:.6f} {y_unit}")
    print(f"    相关系数 r  = {r:.6f}")
    print(f"    斜率不确定度 u(k) = {u_k:.4e}")


# ═══════════════════════════════════════════════════════
#  主程序
# ═══════════════════════════════════════════════════════

def main():
    print("════════════════════════════════════════════════════════════")
    print("          霍尔效应实验数据处理计算器 (直接输入VH版)")
    print("          Hall Effect Experiment Data Processor")
    print("════════════════════════════════════════════════════════════")

    # ──────────────────────────────────────────────────
    #  物理常量
    # ──────────────────────────────────────────────────
    e_charge = 1.602e-19       # C  (元电荷)
    mu_0 = 4.0 * math.pi * 1e-7  # T·m/A  (真空磁导率)

    print(f"\n  物理常量:")
    print(f"    e  = {e_charge} C")
    print(f"    μ₀ = {mu_0:.4e} T·m/A")

    # ──────────────────────────────────────────────────
    #  霍尔元件参数
    # ──────────────────────────────────────────────────
    print("\n" + "━" * 58)
    print("  霍尔元件几何参数")
    print("━" * 58)

    d_mm = input_float("  厚度 d (mm)", 0.095)
    b_mm = input_float("  宽度 b (mm)", 0.235)
    L_mm = input_float("  长度 L (mm)", 0.27)

    # 转换为国际单位 m
    d = d_mm * 1e-3
    b = b_mm * 1e-3
    L = L_mm * 1e-3

    print(f"\n  d = {d_mm} mm = {d:.4e} m")
    print(f"  b = {b_mm} mm = {b:.4e} m")
    print(f"  L = {L_mm} mm = {L:.4e} m")

    # ──────────────────────────────────────────────────
    #  螺线管参数 (计算磁场)
    # ──────────────────────────────────────────────────
    print("\n" + "━" * 58)
    print("  螺线管参数 (B = k_sol · Im)")
    print("━" * 58)
    print("  选择输入方式:")
    print("    1 - 直接输入 B/Im 比值 k_sol (T/A)")
    print("    2 - 输入匝数 N 和有效长度 L_sol")

    mode = input("  请选择 (默认 1): ").strip() or "1"

    if mode == "2":
        N_turns = input_float("  螺线管总匝数 N", 2000)
        L_sol_mm = input_float("  螺线管有效长度 (mm)", 200)
        L_sol_m = L_sol_mm * 1e-3
        k_sol = mu_0 * N_turns / L_sol_m
        print(f"  k_sol = μ₀·N/L = {mu_0:.4e} × {N_turns:.0f} / {L_sol_m:.4f}")
    else:
        k_sol = input_float("  磁场常数 k_sol = B/Im (T/A)", 0.00209)

    print(f"  ★ 螺线管常数: k_sol = {k_sol:.6e} T/A")

    # ══════════════════════════════════════════════════
    #  第一部分: VH 与 Is 的关系
    # ══════════════════════════════════════════════════
    print("\n")
    print("▓" * 58)
    print("  第一部分: VH 与 Is 的关系")
    print("  条件: 探头在螺线管中心, Im 恒定")
    print("▓" * 58)

    Im_fixed_mA = input_float("  固定励磁电流 Im (mA)", 600)
    Im_fixed_A = Im_fixed_mA * 1e-3
    B_fixed = k_sol * Im_fixed_A
    print(f"  对应磁场 B = k_sol × Im = {B_fixed:.6f} T")

    n_pts_1 = 10
    Is_1 = [0.20 * (i + 1) for i in range(n_pts_1)]  # mA: 0.20 ~ 2.00

    print(f"\n  测量要求: 请依次输入各 Is 下对应的霍尔电压 VH (mV)")
    print(f"  请注意正负号以判断导电类型。\n")

    VH_signed_1 = []
    VH_abs_1 = []

    for Is_val in Is_1:
        vh = input_float(f"  Is = {Is_val:.2f} mA → VH (mV)")
        VH_signed_1.append(vh)
        VH_abs_1.append(abs(vh))

    # 打印数据表
    print(f"\n{'─' * 46}")
    print(f"  VH - Is 数据表  (Im = {Im_fixed_mA:.0f} mA, B = {B_fixed:.4f} T)")
    print(f"{'─' * 46}")
    print(f"  {'Is(mA)':>7} │ {'VH带符号(mV)':>12} {'VH绝对值(mV)':>12}")
    print(f"  {'─' * 42}")
    for i in range(n_pts_1):
        print(f"  {Is_1[i]:>7.2f} │ {VH_signed_1[i]:>12.3f} {VH_abs_1[i]:>12.3f}")
    print(f"{'─' * 46}")

    # 线性回归: VH(mV) vs Is(mA)  —— 使用绝对值 VH
    slope_1, intercept_1, r_1, u_slope_1 = map(float, linear_regression(Is_1, VH_abs_1))
    print_regression("VH-Is", slope_1, intercept_1, r_1, u_slope_1, "mA", "mV")

    # 注: 斜率单位 mV/mA = V/A

    # 判断导电类型 (由带符号 VH 的正负判定)
    VH_sign_avg = sum(VH_signed_1) / len(VH_signed_1)
    if VH_sign_avg > 0:
        carrier_type = "P 型 (空穴导电)"
        sign_str = "VH > 0"
    else:
        carrier_type = "N 型 (电子导电)"
        sign_str = "VH < 0"

    print(f"\n  ★ 导电类型判定: {sign_str} → {carrier_type}")

    input("\n  按回车继续...")

    # ══════════════════════════════════════════════════
    #  第二部分: VH 与 Im 的关系
    # ══════════════════════════════════════════════════
    print("\n")
    print("▓" * 58)
    print("  第二部分: VH 与 Im 的关系")
    print("  条件: 探头在螺线管中心, Is 恒定")
    print("▓" * 58)

    Is_fixed_mA = input_float("  固定工作电流 Is (mA)", 1.50)
    Is_fixed_A = Is_fixed_mA * 1e-3

    Im_start = input_float("  Im 起始值 (mA)", 100)
    Im_step = input_float("  Im 步长 (mA)", 50)
    Im_end = input_float("  Im 终止值 (mA)", 600)
    Im_2 = []
    val = Im_start
    while val <= Im_end + 0.01:
        Im_2.append(val)
        val += Im_step
    n_pts_2 = len(Im_2)

    print(f"\n  共 {n_pts_2} 个数据点: Im = {Im_start:.0f} ~ {Im_end:.0f} mA, 步长 {Im_step:.0f} mA")
    print(f"  测量要求: 请依次输入各 Im 下对应的霍尔电压 VH (mV)\n")

    VH_signed_2 = []
    VH_abs_2 = []

    for Im_val in Im_2:
        vh = input_float(f"  Im = {Im_val:.0f} mA → VH (mV)")
        VH_signed_2.append(vh)
        VH_abs_2.append(abs(vh))

    # 打印数据表
    print(f"\n{'─' * 46}")
    print(f"  VH - Im 数据表  (Is = {Is_fixed_mA:.2f} mA)")
    print(f"{'─' * 46}")
    print(f"  {'Im(mA)':>7} │ {'VH带符号(mV)':>12} {'VH绝对值(mV)':>12}")
    print(f"  {'─' * 42}")
    for i in range(n_pts_2):
        print(f"  {Im_2[i]:>7.0f} │ {VH_signed_2[i]:>12.3f} {VH_abs_2[i]:>12.3f}")
    print(f"{'─' * 46}")

    # 线性回归: VH(mV) vs Im(mA)
    slope_2, intercept_2, r_2, u_slope_2 = map(float, linear_regression(Im_2, VH_abs_2))
    print_regression("VH-Im", slope_2, intercept_2, r_2, u_slope_2, "mA", "mV")

    input("\n  按回车继续...")

    # ══════════════════════════════════════════════════
    #  第三部分: 零磁场 Vσ 测量 (电导率)
    # ══════════════════════════════════════════════════
    print("\n")
    print("▓" * 58)
    print("  第三部分: 零磁场 Vσ 测量 (电导率计算)")
    print("  条件: Im = 0, 开关置 Vσ 档")
    print("▓" * 58)

    # Is 范围与第一部分相同
    Is_3 = list(Is_1)  # 0.20 ~ 2.00 mA
    Vsigma = []

    print(f"\n  输入各 Is 下的电压降 Vσ (mV):\n")
    for Is_val in Is_3:
        vs = input_float(f"  Is = {Is_val:.2f} mA → Vσ (mV)")
        Vsigma.append(vs)

    # 打印数据表
    print(f"\n{'─' * 36}")
    print(f"  Vσ - Is 数据表")
    print(f"{'─' * 36}")
    print(f"  {'Is(mA)':>8}  │  {'Vσ(mV)':>10}")
    print(f"  {'─' * 26}")
    for i in range(len(Is_3)):
        print(f"  {Is_3[i]:>8.2f}  │  {Vsigma[i]:>10.4f}")
    print(f"{'─' * 36}")

    # 线性回归: Vσ(mV) vs Is(mA)
    slope_3, intercept_3, r_3, u_slope_3 = map(float, linear_regression(Is_3, Vsigma))
    print_regression("Vσ-Is", slope_3, intercept_3, r_3, u_slope_3, "mA", "mV")
    print(f"    注: 斜率 = Vσ/Is, 单位 mV/mA = V/A = Ω (样品电阻)")

    # ══════════════════════════════════════════════════
    #  第四部分: 物理量计算
    # ══════════════════════════════════════════════════
    print("\n")
    print("▓" * 58)
    print("  第四部分: 物理量计算与不确定度分析")
    print("▓" * 58)

    # ─── 4.1 电导率 σ ───
    # σ = L / (R · b · d)
    # R = slope_3 (mV/mA = V/A = Ω)
    R_sample = slope_3  # Ω
    sigma = L / (R_sample * b * d)  # S/m

    # 不确定度 (此处仅传递回归斜率的不确定度，几何参数视为已知常量)
    u_r_R = abs(u_slope_3 / slope_3) if slope_3 != 0 else 0.0
    u_r_sigma = u_r_R  # 简化: 仅考虑斜率不确定度
    u_sigma = abs(sigma) * u_r_sigma

    print(f"\n  ── 4.1 电导率 σ ──")
    print(f"  样品电阻 R = Vσ/Is (斜率) = {R_sample:.6f} Ω")
    print(f"  σ = L / (R · b · d)")
    print(f"    = {L:.4e} / ({R_sample:.6f} × {b:.4e} × {d:.4e})")
    print(f"    = {sigma:.4f} S/m")
    print(f"  u_r(σ) = u(k₃)/k₃ = {u_r_sigma * 100:.2f}%")

    sigma_final, u_sigma_final = scientific_round(sigma, u_sigma)
    print(f"  ★ σ = {sigma_final} ± {u_sigma_final} S/m")

    # ─── 4.2 霍尔灵敏度 KH (由 VH-Is 线性回归) ───
    # VH = KH · Is · B  →  slope₁ = KH · B  →  KH = slope₁ / B
    # slope₁ 单位: mV/mA = V/A
    KH = slope_1 / B_fixed  # V/(A·T)

    u_r_slope1 = abs(u_slope_1 / slope_1) if slope_1 != 0 else 0.0
    u_r_KH = u_r_slope1  # B 视为无不确定度
    u_KH = abs(KH) * u_r_KH

    print(f"\n  ── 4.2 霍尔灵敏度 KH (VH-Is) ──")
    print(f"  KH = slope₁ / B")
    print(f"     = {slope_1:.6f} / {B_fixed:.6f}")
    print(f"     = {KH:.4f} V/(A·T)")
    print(f"  u_r(KH) = {u_r_KH * 100:.2f}%")

    KH_final, u_KH_final = scientific_round(abs(KH), u_KH)
    print(f"  ★ |KH| = {KH_final} ± {u_KH_final} V/(A·T)")

    # ─── 交叉验证: 由 VH-Im 线性回归求 KH ───
    # VH = KH · Is · k_sol · Im  →  slope₂ = KH · Is · k_sol
    # KH = slope₂ / (Is_fixed_A · k_sol)
    KH_check = slope_2 / (Is_fixed_A * k_sol)

    print(f"\n  ── 交叉验证: KH (VH-Im) ──")
    print(f"  KH' = slope₂ / (Is · k_sol)")
    print(f"      = {slope_2:.6f} / ({Is_fixed_A:.4e} × {k_sol:.6e})")
    print(f"      = {KH_check:.4f} V/(A·T)")
    deviation_pct = abs(KH - KH_check) / abs(KH) * 100 if KH != 0 else 0
    print(f"  两种方法偏差: {deviation_pct:.2f}%")

    # ─── 4.3 霍尔系数 RH ───
    RH = abs(KH) * d  # m³/C

    print(f"\n  ── 4.3 霍尔系数 RH ──")
    print(f"  RH = |KH| × d = {abs(KH):.4f} × {d:.4e}")
    print(f"  RH = {RH:.4e} m³/C")

    # ─── 4.4 载流子浓度 n ───
    # n = 1 / (RH · e)
    n_carrier = 1.0 / (RH * e_charge)

    # u_r(n) = u_r(KH) (d 视为精确)
    u_r_n = u_r_KH
    u_n = n_carrier * u_r_n

    print(f"\n  ── 4.4 载流子浓度 n ──")
    print(f"  n = 1 / (RH · e)")
    print(f"    = 1 / ({RH:.4e} × {e_charge})")
    print(f"    = {n_carrier:.4e} m⁻³")

    n_final, u_n_final = scientific_round(n_carrier, u_n)
    print(f"  ★ n = {n_final} ± {u_n_final} m⁻³")

    # ─── 4.5 载流子迁移率 μ ───
    # μ = σ / (n · e) = σ · RH
    mu = sigma / (n_carrier * e_charge)
    mu_check = sigma * RH  # 验证

    u_r_mu = math.sqrt(u_r_sigma ** 2 + u_r_KH ** 2)
    u_mu = abs(mu) * u_r_mu

    print(f"\n  ── 4.5 载流子迁移率 μ ──")
    print(f"  μ = σ / (n · e)")
    print(f"    = {sigma:.4f} / ({n_carrier:.4e} × {e_charge})")
    print(f"    = {mu:.4e} m²/(V·s)")
    print(f"  验证: μ = σ · RH = {sigma:.4f} × {RH:.4e} = {mu_check:.4e} m²/(V·s)")

    mu_final, u_mu_final = scientific_round(mu, u_mu)
    print(f"  ★ μ = {mu_final} ± {u_mu_final} m²/(V·s)")

    # ══════════════════════════════════════════════════
    #  第五部分: 结果汇总
    # ══════════════════════════════════════════════════
    print("\n")
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                   实 验 结 果 汇 总                        ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print(f"║                                                            ║")
    print(f"║  导电类型:  {carrier_type:<47}║")
    print(f"║                                                            ║")
    print(f"╟────────── 线性回归 ────────────────────────────────────────╢")
    print(f"║  VH-Is:  k₁ = {slope_1:>10.6f} V/A      r = {r_1:>9.6f}     ║")
    print(f"║  VH-Im:  k₂ = {slope_2:>10.6f} V/A      r = {r_2:>9.6f}     ║")
    print(f"║  Vσ-Is:  k₃ = {slope_3:>10.6f} Ω        r = {r_3:>9.6f}     ║")
    print(f"╟────────── 物理参数 ────────────────────────────────────────╢")
    print(f"║  电导率      σ  = {str(sigma_final):>12} ± {str(u_sigma_final):<10} S/m     ║")
    print(f"║  霍尔灵敏度  KH = {str(KH_final):>12} ± {str(u_KH_final):<10} V/(A·T)  ║")
    print(f"║  霍尔系数    RH = {RH:>12.4e}              m³/C     ║")
    print(f"║  载流子浓度  n  = {str(n_final):>12} ± {str(u_n_final):<10} m⁻³      ║")
    print(f"║  载流子迁移率 μ = {str(mu_final):>12} ± {str(u_mu_final):<10} m²/(V·s) ║")
    print(f"║                                                            ║")
    print(f"╟────────── 不确定度 ────────────────────────────────────────╢")
    print(f"║  u_r(σ)  = {u_r_sigma * 100:>6.2f}%                                  ║")
    print(f"║  u_r(KH) = {u_r_KH * 100:>6.2f}%                                  ║")
    print(f"║  u_r(n)  = {u_r_n * 100:>6.2f}%                                  ║")
    print(f"║  u_r(μ)  = {u_r_mu * 100:>6.2f}%                                  ║")
    print(f"║                                                            ║")
    print("╚══════════════════════════════════════════════════════════════╝")


if __name__ == "__main__":
    main()