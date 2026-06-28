import math
from decimal import Decimal

"""
Thermal Conductivity & Specific Heat Calculator (Steady-State Plate Method)
导热系数与比热容计算器 (稳态平板法 — 一维无限大平板)

实验原理:
  利用稳态平板法测量不良导体的导热系数。
  当加热板和样品达到热平衡（稳态）时，通过样品的热流密度 q_c 等于
  样品两面温差 ΔT 除以厚度 R 再乘以导热系数 λ。
  断电后由冷却曲线斜率计算样品比热容 c。

核心公式:
  1. 热流密度:
     q_c = V² / (2 · F · r)
     其中 V = 加热电压, F = 有效加热面积, r = 加热电阻

  2. 导热系数:
     λ = q_c · R / (2 · ΔT)
     其中 R = 样品厚度, ΔT = 加热面温度 - 中心面温度

  3. 温度转换 (热电偶):
     ΔT = ΔU / S
     其中 S = 热电偶灵敏度系数 (mV/K), ΔU = U_加热面 - U_中心面

  4. 比热容 (冷却法):
     c = q_c · F / (m · |κ|)
     其中 m = 样品质量, κ = dT/dτ|_冷却 为冷却曲线在稳态温度处的斜率

  5. 不确定度传递 — 导热系数 λ = V²·R / (4·F·r·ΔT):
     u_r(λ) = √[ (2·u_V/V)² + (u_R/R)² + (u_F/F)² + (u_r/r)² + (u_ΔT/ΔT)² ]
     u(ΔU) 取稳态区间多点的 A 类 + 仪器 B 类合成; u_r(ΔT) ≈ u(ΔU)/|ΔU|

  6. 不确定度传递 — 比热容 c = V² / (2·r·m·|κ|):
     u_r(c) = √[ (2·u_V/V)² + (u_r/r)² + (u_m/m)² + (u_κ/|κ|)² ]
     u_κ 由冷却曲线线性拟合的斜率标准差给出
"""

from utils import (
    scientific_round,
    calculate_stats,
    input_data_group,
    linear_regression
)


# ──────────────────────────────────────────────
# 数据输入辅助函数
# ──────────────────────────────────────────────

def input_voltage_series(name, n_points=18):
    """输入 1~n_points 分钟的电压数据 (单位: uV)"""
    print(f"\n请输入 {name} 的 {n_points} 个电压值 (uV), 可用空格/逗号分隔一次输入:")

    data = []
    while len(data) < n_points:
        remaining = n_points - len(data)
        try:
            raw = input(f"  [{len(data)+1}~{len(data)+remaining}] > ").strip()
            if not raw:
                continue
            tokens = raw.replace(',', ' ').split()
            for tok in tokens:
                data.append(Decimal(tok))
                if len(data) >= n_points:
                    break
        except Exception:
            print("  输入无效，请重新输入。")

    return data


# ──────────────────────────────────────────────
# 稳态判断
# ──────────────────────────────────────────────

def find_steady_state(voltages, window=3, threshold=Decimal("0.5")):
    """
    判断电压序列何时达到稳态。
    使用滑动窗口：当连续 window 个读数的极差 < threshold (uV) 时认为稳态。
    返回稳态起始索引（从 0 开始），若未达到稳态则返回最后 window 个的起始。
    """
    for i in range(len(voltages) - window + 1):
        w = voltages[i:i + window]
        if max(w) - min(w) < threshold:
            return i
    return len(voltages) - window


# ──────────────────────────────────────────────
# 核心计算函数
# ──────────────────────────────────────────────

def compute_thermal_conductivity(
        center_uV,        # 中心面电压序列 (uV)
        heating_uV,       # 加热面电压序列 (uV)
        V_heat,           # 加热电压 (V)
        F,                # 有效加热面积 (m²)
        r,                # 加热电阻 (Ω)
        R_thickness,      # 样品厚度 (m)
        S_sensitivity,    # 热电偶灵敏度 (mV/K)
        material_name=""  # 材料名称
    ):
    """计算单一材料的导热系数，并保留稳态 ΔU 列表供不确定度分析使用"""

    n = len(center_uV)
    time_min = list(range(1, n + 1))  # 1 ~ n 分钟

    # --- 1. 转换为温度差 ΔT(t) ---
    delta_uV = [heating_uV[i] - center_uV[i] for i in range(n)]
    delta_T  = [dv / S_sensitivity for dv in delta_uV]

    # --- 2. 判断稳态 ---
    ss_idx_center  = find_steady_state(center_uV)
    ss_idx_heating = find_steady_state(heating_uV)
    ss_idx         = max(ss_idx_center, ss_idx_heating)

    # 稳态区间 ΔU 列表（A 类不确定度来源）
    steady_delta_uV = delta_uV[ss_idx:]
    delta_T_steady  = sum(steady_delta_uV) / Decimal(len(steady_delta_uV)) / S_sensitivity

    center_steady_avg  = sum(center_uV[ss_idx:])  / Decimal(len(center_uV[ss_idx:]))
    heating_steady_avg = sum(heating_uV[ss_idx:]) / Decimal(len(heating_uV[ss_idx:]))

    # --- 3. 热流密度 q_c ---
    q_c = V_heat ** 2 / (Decimal("2") * F * r)

    # --- 4. 导热系数 λ ---
    lam = q_c * R_thickness / (Decimal("2") * delta_T_steady)

    # --- 5. 加热趋近速率 dT/dτ (用于验证是否达到稳态) ---
    if n >= 3:
        last_n = min(5, n)
        x_fit = [Decimal(str(t * 60)) for t in time_min[-last_n:]]   # 秒
        y_fit = [center_uV[i] / S_sensitivity for i in range(-last_n, 0)]  # K (相对)
        dT_dtau, _, _, _ = linear_regression(x_fit, y_fit)            # K/s
    else:
        dT_dtau = Decimal("0")

    return {
        "material":          material_name,
        "q_c":               q_c,
        "delta_T_steady":    delta_T_steady,
        "lambda":            lam,
        "ss_start_min":      ss_idx + 1,
        "center_steady_uV":  center_steady_avg,
        "heating_steady_uV": heating_steady_avg,
        "dT_dtau":           dT_dtau,
        "time_min":          time_min,
        "center_uV":         center_uV,
        "heating_uV":        heating_uV,
        "delta_uV":          delta_uV,
        "delta_T":           delta_T,
        "steady_delta_uV":   steady_delta_uV,   # 稳态区间 ΔU 列表，供不确定度分析使用
    }


def compute_specific_heat(cooling_uV, S_sensitivity, q_c, F, m_sample):
    """
    由冷却曲线计算比热容 c。

    cooling_uV   : 断电后中心面电压序列 (uV), 每隔 60 s 一个点
    S_sensitivity: 热电偶灵敏度 (mV/K)
    q_c          : 热流密度 (W/m²)
    F            : 有效加热面积 (m²)
    m_sample     : 样品质量 (kg)

    返回: (c, dT_dtau_cool, u_dTdtau)
      c            — 比热容 J/(kg·K)
      dT_dtau_cool — 冷却速率绝对值 |κ| (K/s)
      u_dTdtau     — |κ| 的不确定度 (K/s), 由线性拟合给出
    """
    n      = len(cooling_uV)
    x_cool = [Decimal(str(i * 60)) for i in range(n)]     # 秒
    y_cool = [uv / S_sensitivity for uv in cooling_uV]    # 相对温度 (K)

    k, _, _, u_k = linear_regression(x_cool, y_cool)
    dT_dtau_cool = abs(k)    # 冷却时斜率为负，取绝对值
    u_dTdtau     = abs(u_k)

    c = (q_c * F / (m_sample * dT_dtau_cool)) if dT_dtau_cool != 0 else Decimal("0")
    return c, dT_dtau_cool, u_dTdtau


def compute_uncertainties(
        result,                   # dict from compute_thermal_conductivity
        dT_dtau_cool,             # 冷却速率 |κ| (K/s, Decimal, 已取绝对值)
        u_dTdtau,                 # |κ| 的不确定度 (K/s)
        m_sample,                 # 样品质量 (kg)
        delta_m,                  # 质量仪器误差 (kg)
        V_heat,   delta_V,        # 加热电压及仪器误差 (V)
        F,        delta_F,        # 面积及仪器误差 (m²)
        r,        delta_r,        # 电阻及仪器误差 (Ω)
        R_thickness, delta_R,     # 厚度及仪器误差 (m)
        delta_uV_inst,            # 电压表仪器误差 (uV)
        S_sensitivity,            # 热电偶灵敏度 (mV/K, 预留接口，暂不计入不确定度)
    ):
    """
    计算导热系数 λ 和比热容 c 的合成不确定度。

    λ = V²·R / (4·F·r·ΔT)
      u_r(λ) = √[ (2·u_V/V)² + (u_R/R)² + (u_F/F)² + (u_r/r)² + (u_ΔT/ΔT)² ]
      u(ΔU): 稳态区间多点的 A 类 + 仪器 B 类合成; u_r(ΔT) ≈ u(ΔU)/|ΔU_mean|

    c = V² / (2·r·m·|κ|)
      u_r(c) = √[ (2·u_V/V)² + (u_r/r)² + (u_m/m)² + (u_κ/|κ|)² ]
      u_κ 来自冷却曲线线性拟合
    """
    sqrt3 = Decimal(str(math.sqrt(3)))
    lam   = result["lambda"]
    q_c   = result["q_c"]

    # --- u(ΔU): A 类 + B 类 ---
    steady_delta_uV = result["steady_delta_uV"]
    delta_U_mean, u_delta_U, u_a_dU, u_b_dU, _ = calculate_stats(
        steady_delta_uV, delta_uV_inst
    )
    # u_r(ΔT) ≈ u(ΔU) / |ΔU_mean|，忽略 S 的不确定度
    ur_deltaT = (u_delta_U / abs(delta_U_mean)) if delta_U_mean != 0 else Decimal("0")

    # --- 单次测量的 B 类相对不确定度 ---
    ur_V = (delta_V / sqrt3) / V_heat
    ur_F = (delta_F / sqrt3) / F
    ur_r = (delta_r / sqrt3) / r
    ur_R = (delta_R / sqrt3) / R_thickness
    ur_m = (delta_m / sqrt3) / m_sample

    # --- u_r(λ) ---
    ur_lam_sq = (Decimal("2") * ur_V)**2 + ur_R**2 + ur_F**2 + ur_r**2 + ur_deltaT**2
    ur_lam    = Decimal(str(math.sqrt(float(ur_lam_sq))))
    u_lam     = lam * ur_lam

    # --- u_r(c) ---
    ur_cool = (u_dTdtau / dT_dtau_cool) if dT_dtau_cool != 0 else Decimal("0")
    ur_c_sq = (Decimal("2") * ur_V)**2 + ur_r**2 + ur_m**2 + ur_cool**2
    ur_c    = Decimal(str(math.sqrt(float(ur_c_sq))))

    c_val = (q_c * F / (m_sample * dT_dtau_cool)) if dT_dtau_cool != 0 else Decimal("0")
    u_c   = c_val * ur_c

    return {
        "u_lam":        u_lam,
        "ur_lam":       ur_lam,
        "u_c":          u_c,
        "ur_c":         ur_c,
        "delta_U_mean": delta_U_mean,
        "u_delta_U":    u_delta_U,
        "u_a_dU":       u_a_dU,
        "u_b_dU":       u_b_dU,
        "ur_deltaT":    ur_deltaT,
        "ur_V":         ur_V,
        "ur_F":         ur_F,
        "ur_r":         ur_r,
        "ur_R":         ur_R,
        "ur_m":         ur_m,
        "ur_cool":      ur_cool,
    }


# ──────────────────────────────────────────────
# 输出函数
# ──────────────────────────────────────────────

def print_data_table(result, S):
    """打印加热阶段数据表格"""
    n = len(result["time_min"])
    print(f"\n{'时间(min)':>10} {'中心面(uV)':>12} {'加热面(uV)':>12} {'ΔU(uV)':>10} {'ΔT(K)':>10}")
    print("-" * 60)
    for i in range(n):
        t      = result["time_min"][i]
        uc     = result["center_uV"][i]
        uh     = result["heating_uV"][i]
        du     = result["delta_uV"][i]
        dt     = result["delta_T"][i]
        marker = " ← 稳态起始" if t == result["ss_start_min"] else ""
        print(f"{t:>10} {uc:>12} {uh:>12} {du:>10} {float(dt):>10.2f}{marker}")


def print_full_result(result, c_val, dT_dtau_cool, u_result):
    """打印含不确定度的完整计算结果"""
    lam                    = result["lambda"]
    lam_final, u_lam_final = scientific_round(lam,   u_result["u_lam"])
    c_final,   u_c_final   = scientific_round(c_val, u_result["u_c"])

    W = 58
    print(f"\n{'='*W}")
    print(f"  {result['material']} — 计算结果")
    print(f"{'='*W}")
    print(f"  稳态起始时间             = 第 {result['ss_start_min']} 分钟")
    print(f"  稳态温差 ΔT              = {float(result['delta_T_steady']):.4f} K")
    print(f"  加热趋近速率 dT/dτ       = {float(result['dT_dtau']):.6f} K/s")
    print(f"  冷却速率 |κ| = |dT/dτ|  = {float(dT_dtau_cool):.6f} K/s")
    print(f"  热流密度 q_c             = {float(result['q_c']):.4f} W/m²")
    print(f"-" * W)
    print(f"  稳态 ΔU (均值)           = {float(u_result['delta_U_mean']):.3f} uV")
    print(f"    u_A(ΔU)               = {float(u_result['u_a_dU']):.4f} uV")
    print(f"    u_B(ΔU)               = {float(u_result['u_b_dU']):.4f} uV")
    print(f"    u(ΔU)                 = {float(u_result['u_delta_U']):.4f} uV")
    print(f"-" * W)
    print(f"  不确定度贡献 (相对):")
    print(f"    u_r(V)  = {float(u_result['ur_V'])*100:6.3f}%   (λ & c 共用)")
    print(f"    u_r(F)  = {float(u_result['ur_F'])*100:6.3f}%   (λ)")
    print(f"    u_r(r)  = {float(u_result['ur_r'])*100:6.3f}%   (λ & c 共用)")
    print(f"    u_r(R)  = {float(u_result['ur_R'])*100:6.3f}%   (λ)")
    print(f"    u_r(ΔT) = {float(u_result['ur_deltaT'])*100:6.3f}%   (λ)")
    print(f"    u_r(m)  = {float(u_result['ur_m'])*100:6.3f}%   (c)")
    print(f"    u_r(κ)  = {float(u_result['ur_cool'])*100:6.3f}%   (c)")
    print(f"-" * W)
    print(f"  u_r(λ) = {float(u_result['ur_lam'])*100:.2f}%   →  u(λ) = {float(u_result['u_lam']):.6f} W/(m·K)")
    print(f"  u_r(c) = {float(u_result['ur_c'])*100:.2f}%   →  u(c) = {float(u_result['u_c']):.2f} J/(kg·K)")
    print(f"{'='*W}")
    print(f"  ★ 导热系数  λ = ({lam_final} ± {u_lam_final}) W/(m·K)")
    print(f"  ★ 比热容    c = ({c_final} ± {u_c_final}) J/(kg·K)")
    print(f"{'='*W}")


# ──────────────────────────────────────────────
# 主程序
# ──────────────────────────────────────────────

def main():
    # --- 1. 实验参数设置 ---
    W = 58
    print("=" * W)
    print("  导热系数 & 比热容计算 (稳态平板法 — 一维无限大平板)")
    print("=" * W)

    # 默认实验参数
    V_HEAT_DEFAULT        = "18.00"    # 加热电压 (V)
    F_DEFAULT             = "0.006885" # 有效加热面积 = 0.85 × 0.09 × 0.09 (m²)
    R_RESISTANCE_DEFAULT  = "110"      # 加热电阻 (Ω)
    R_THICKNESS_DEFAULT   = "0.01"     # 样品厚度 (m)
    S_SENSITIVITY_DEFAULT = "0.04"     # 热电偶灵敏度 (mV/K)
    N_POINTS_DEFAULT      = 18         # 加热段数据点数
    N_COOL_DEFAULT        = 5          # 冷却段数据点数

    print(f"\n--- 实验参数 (按 Enter 使用默认值) ---")

    V_heat = Decimal(input(f"加热电压 V (V, 默认 {V_HEAT_DEFAULT}): ").strip() or V_HEAT_DEFAULT)

    F_input = input(f"有效加热面积 F (m², 默认 {F_DEFAULT} = 0.85×0.09×0.09): ").strip()
    F = Decimal(F_input) if F_input else Decimal(F_DEFAULT)

    r_input = input(f"加热电阻 r (Ω, 默认 {R_RESISTANCE_DEFAULT}): ").strip()
    r = Decimal(r_input) if r_input else Decimal(R_RESISTANCE_DEFAULT)

    R_input = input(f"样品厚度 R (m, 默认 {R_THICKNESS_DEFAULT}): ").strip()
    R_thickness = Decimal(R_input) if R_input else Decimal(R_THICKNESS_DEFAULT)

    S_input = input(f"热电偶灵敏度 S (mV/K, 默认 {S_SENSITIVITY_DEFAULT}): ").strip()
    S = Decimal(S_input) if S_input else Decimal(S_SENSITIVITY_DEFAULT)

    n_input = input(f"加热段数据点数 (默认 {N_POINTS_DEFAULT}): ").strip()
    n_points = int(n_input) if n_input else N_POINTS_DEFAULT

    n_cool_input = input(f"冷却段数据点数 (默认 {N_COOL_DEFAULT}): ").strip()
    n_cool = int(n_cool_input) if n_cool_input else N_COOL_DEFAULT

    # --- 2. 仪器误差输入 ---
    print(f"\n--- 仪器误差 (按 Enter 使用默认值) ---")
    delta_V  = Decimal(input("  加热电压仪器误差 δV (V,  默认 0.01):    ").strip() or "0.01")
    delta_F  = Decimal(input("  面积仪器误差     δF (m², 默认 0.00001): ").strip() or "0.00001")
    delta_r  = Decimal(input("  电阻仪器误差     δr (Ω,  默认 0.1):    ").strip() or "0.1")
    delta_R  = Decimal(input("  厚度仪器误差     δR (m,  默认 0.0001): ").strip() or "0.0001")
    delta_uV = Decimal(input("  电压表仪器误差   δU (uV, 默认 2.0):    ").strip() or "2.0")

    # --- 3. 逐材料数据输入 ---
    # 默认密度 (kg/m³); 样品为两块相同材料叠放
    materials = [
        ("橡胶 (Rubber)",   Decimal("1374")),
        ("有机玻璃 (PMMA)", Decimal("1196")),
    ]
    results    = []
    extra_data = []

    for mat_name, rho_default in materials:
        print(f"\n{'#'*W}")
        print(f"  材料: {mat_name}")
        print(f"{'#'*W}")

        # 加热阶段电压
        center_uV  = input_voltage_series(f"{mat_name} — 中心面电压 (加热阶段)", n_points)
        heating_uV = input_voltage_series(f"{mat_name} — 加热面电压 (加热阶段)", n_points)

        result = compute_thermal_conductivity(
            center_uV=center_uV,
            heating_uV=heating_uV,
            V_heat=V_heat,
            F=F,
            r=r,
            R_thickness=R_thickness,
            S_sensitivity=S,
            material_name=mat_name
        )

        print_data_table(result, S)

        # 比热容测量 (冷却法) — 质量由密度与几何尺寸推算
        print(f"\n--- {mat_name} — 比热容测量 (冷却法) ---")
        rho_str  = input(f"  材料密度 ρ (kg/m³, 默认 {rho_default}): ").strip()
        rho      = Decimal(rho_str) if rho_str else rho_default
        # 两块样品叠放: m = 2 × ρ × F × R
        m_sample = Decimal("2") * rho * F * R_thickness
        print(f"  → 样品质量 m = 2 × {rho} × {F} × {R_thickness} = {float(m_sample):.6f} kg")
        # δm 由 δF、δR 传递: u_r(m) = √[(u_F/F)² + (u_R/R)²], delta_m_eff = m·√[(δF/F)²+(δR/R)²]
        delta_m  = m_sample * Decimal(str(math.sqrt(
            float((delta_F / F)**2 + (delta_R / R_thickness)**2)
        )))

        # 冷却段中心面电压采用加热段中心面电压的最后几项反向填充（即从稳态开始降温）
        cooling_uV = list(reversed(center_uV[-n_cool:]))
        print(f"  → 冷却阶段中心面电压 (反向填充自加热段): {[float(x) for x in cooling_uV]} uV")

        results.append(result)
        extra_data.append({"m_sample": m_sample, "delta_m": delta_m, "cooling_uV": cooling_uV})

    # --- 4. 汇总计算与输出 ---
    print("\n" + "=" * W)
    print("                 汇 总 结 果")
    print("=" * W)

    q_c = results[0]["q_c"]
    print(f"\n  加热电压 V     = {V_heat} V")
    print(f"  有效面积 F     = {F} m²")
    print(f"  加热电阻 r     = {r} Ω")
    print(f"  样品厚度 R     = {R_thickness} m")
    print(f"  热电偶灵敏度 S = {S} mV/K")
    print(f"  热流密度 q_c   = V²/(2·F·r) = {float(q_c):.4f} W/m²")

    for res, extra in zip(results, extra_data):
        m_sample   = extra["m_sample"]
        delta_m    = extra["delta_m"]
        cooling_uV = extra["cooling_uV"]

        c_val, dT_dtau_cool, u_dTdtau = compute_specific_heat(
            cooling_uV=cooling_uV,
            S_sensitivity=S,
            q_c=res["q_c"],
            F=F,
            m_sample=m_sample,
        )

        u_result = compute_uncertainties(
            result=res,
            dT_dtau_cool=dT_dtau_cool,
            u_dTdtau=u_dTdtau,
            m_sample=m_sample,
            delta_m=delta_m,
            V_heat=V_heat,         delta_V=delta_V,
            F=F,                   delta_F=delta_F,
            r=r,                   delta_r=delta_r,
            R_thickness=R_thickness, delta_R=delta_R,
            delta_uV_inst=delta_uV,
            S_sensitivity=S,
        )

        print_full_result(res, c_val, dT_dtau_cool, u_result)

    # --- 5. 参考值对比 ---
    print("\n" + "-" * W)
    print("  参考值 (室温):")
    print(f"    橡胶:  λ ≈ 0.13–0.16 W/(m·K),  c ≈ 1000–2000 J/(kg·K)")
    print(f"    PMMA:  λ ≈ 0.17–0.25 W/(m·K),  c ≈ 1400–1500 J/(kg·K)")
    print("-" * W)

    input("\n按 Enter 退出...")


if __name__ == "__main__":
    main()
