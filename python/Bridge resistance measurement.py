import math
from decimal import Decimal
from utils import (
    scientific_round,
    calculate_stats,
    input_decimal,
    input_int
)

"""
Wheatstone Bridge Resistance Measurement Calculator
电桥法测量电阻计算器

参考了表面张力系数计算器的高精度与不确定度修约逻辑。

公式说明:
1. 惠斯通电桥平衡条件 (Bridge Balance Equation):
   当检流计示数为零时，电桥平衡：
   Rx / R0 = R1 / R2
   即:
   Rx = R0 * (R1 / R2)    （也写作 Rx = R0 * C，C = R1/R2 为比例臂比值）
   
   其中:
   Rx  : 待测电阻
   R0  : 比较臂标准电阻（电桥读数）
   R1/R2 : 比例臂之比，取 1:1, 1:10, 10:1

2. 灵敏度公式 (Bridge Sensitivity):
   S = Δn / (ΔR0 / R0)
   
   其中:
   S    : 电桥灵敏度（格/相对变化量）
   Δn   : 检流计偏转格数（通常取 5 小格）
   ΔR0  : 使检流计偏转 Δn 格时 R0 的改变量
          ΔR0 = |R0' - R0|，R0' 为偏转 5 格时的读数
   R0   : 平衡时的标准电阻读数

   也可写为:
   S = Δn * R0 / ΔR0

3. 不确定度传递公式 (Uncertainty Propagation):
   Rx = R0 * C  (C 为比例臂比值)
   
   (a) R0 的不确定度:
       u(R0) = sqrt( u_A(R0)^2 + u_B(R0)^2 )
       其中:
       u_A(R0) = s(R0) / sqrt(n)   (A 类不确定度, s 为标准偏差)
       u_B(R0) = Δ_inst / sqrt(3)  (B 类不确定度, Δ_inst 为仪器误差限)
   
   (b) 仪器误差限 Δ_inst 的确定 (与灵敏度有关):
       Δ_inst = R0 / S
       即由灵敏度决定的电桥最小可分辨电阻变化量
   
   (c) 比例臂 C 视为精确值（标准电阻箱），则:
       u(Rx) = C * u(R0)
       
   (d) 相对不确定度:
       u_r(Rx) = u(Rx) / Rx = u(R0) / R0
   
   (e) 修约规则:
       不确定度保留一位有效数字，四舍六入五凑偶
       Rx 末位与不确定度对齐
"""


def measure_one_ratio(ratio_label, C_value, R_nominal, n_measurements):
    """
    对单一比例臂进行测量与分析
    
    参数:
        ratio_label: 比例臂标签，如 "1:1"
        C_value: 比例臂比值 C = R1/R2
        R_nominal: 标定电阻标称值 (Ω)
        n_measurements: 测量次数
    """
    C = Decimal(str(C_value))
    
    print(f"\n{'─'*50}")
    print(f"  比例臂 Rx:R0 = {ratio_label}，比例因子 C = {C_value}")
    print(f"  标定电阻标称值: {R_nominal} Ω")
    print(f"{'─'*50}")
    
    # --- 输入平衡时的 R0 读数 ---
    print(f"\n请输入 {n_measurements} 次平衡时的 R0 读数 (Ω):")
    R0_data = []
    for i in range(n_measurements):
        while True:
            try:
                val = input(f"  第 {i+1} 次 R0 = ").strip()
                if not val: continue
                R0_data.append(Decimal(val))
                break
            except Exception:
                print("  输入无效，请输入数字。")
    
    # --- 输入偏差 5 小格时的 R0' ---
    print(f"\n请输入偏转 5 小格时的 R0' 读数 (Ω):")
    R0_prime = input_decimal("  R0'")
    delta_n = Decimal("5")  # 检流计偏转格数
    
    # --- 计算 R0 的平均值 ---
    R0_mean = sum(R0_data) / Decimal(len(R0_data))
    
    # --- 计算灵敏度 ---
    # S = Δn * R0 / |R0' - R0|
    delta_R0 = abs(R0_prime - R0_mean)
    if delta_R0 == 0:
        print("  ⚠ 警告: R0' = R0，无法计算灵敏度，请检查数据！")
        S = Decimal("Infinity")
        delta_inst = Decimal("0")
    else:
        S = delta_n * R0_mean / delta_R0
        # 仪器误差限 (由灵敏度决定)
        # Δ_inst = R0 / S = |R0' - R0| / Δn = ΔR0 / 5
        delta_inst = R0_mean / S
    
    # --- 不确定度分析 ---
    R0_mean_final, u_R0, u_a_R0, u_b_R0, _ = calculate_stats(R0_data, str(delta_inst))
    
    # Rx = C * R0
    Rx_mean = C * R0_mean_final
    u_Rx = C * u_R0
    
    # 相对不确定度
    if Rx_mean != 0:
        u_r_Rx = u_Rx / Rx_mean
    else:
        u_r_Rx = Decimal("0")
    
    # --- 修约 ---
    Rx_final, u_Rx_final = scientific_round(Rx_mean, u_Rx)
    
    # --- 输出结果 ---
    print(f"\n{'═'*50}")
    print(f"  结果 (比例臂 {ratio_label}, 标定 {R_nominal} Ω)")
    print(f"{'═'*50}")
    
    # 打印 R0 测量数据表
    print(f"\n  R0 测量数据:")
    for i, val in enumerate(R0_data):
        print(f"    第 {i+1} 次: {val} Ω")
    
    print(f"\n  R0 平均值      = {R0_mean_final:.4f} Ω")
    print(f"  R0'           = {R0_prime} Ω")
    print(f"  ΔR0 = |R0'-R0| = {delta_R0:.4f} Ω")
    print(f"  偏转格数 Δn    = {delta_n} 格")
    print(f"{'─'*50}")
    print(f"  灵敏度 S = Δn·R0/ΔR0 = {S:.2f}")
    print(f"  仪器误差限 Δ_inst = R0/S = {delta_inst:.4f} Ω")
    print(f"{'─'*50}")
    print(f"  u_A(R0)        = {u_a_R0:.6f} Ω")
    print(f"  u_B(R0)        = {u_b_R0:.6f} Ω")
    print(f"  u(R0)          = {u_R0:.6f} Ω")
    print(f"{'─'*50}")
    print(f"  Rx = C × R0    = {C} × {R0_mean_final:.4f} = {Rx_mean:.4f} Ω")
    print(f"  u(Rx) = C × u(R0) = {u_Rx:.6f} Ω")
    print(f"  相对不确定度 u_r = {u_r_Rx*100:.2f}%")
    print(f"{'─'*50}")
    print(f"  ★ 最终结果: Rx = {Rx_final} ± {u_Rx_final} Ω")
    print(f"{'═'*50}")
    
    return {
        "ratio_label": ratio_label,
        "C": C,
        "R_nominal": R_nominal,
        "R0_data": R0_data,
        "R0_mean": R0_mean_final,
        "R0_prime": R0_prime,
        "delta_R0": delta_R0,
        "S": S,
        "delta_inst": delta_inst,
        "u_a_R0": u_a_R0,
        "u_b_R0": u_b_R0,
        "u_R0": u_R0,
        "Rx_mean": Rx_mean,
        "u_Rx": u_Rx,
        "u_r_Rx": u_r_Rx,
        "Rx_final": Rx_final,
        "u_Rx_final": u_Rx_final
    }

def main():
    print("════════════════════════════════════════════════")
    print("        电桥法测量电阻计算器 (Wheatstone Bridge)")
    print("════════════════════════════════════════════════")
    print()
    print("实验原理:")
    print("  惠斯通电桥平衡条件: Rx = R0 × C  (C = R1/R2)")
    print("  灵敏度: S = Δn × R0 / ΔR0")
    print("  不确定度: u(Rx) = C × u(R0), u(R0) = √(u_A² + u_B²)")
    print()
    
    # --- 1. 基本参数 ---
    n_meas = input_int("每组测量次数 n", default=5)
    
    # --- 2. 定义测量方案 ---
    # 标定电阻: 10kΩ 和 2kΩ
    # 比例臂:  1:1, 1:10, 10:1
    # 注意: 2kΩ 不会有 1:10 的比例臂 (因为 R0 = Rx/(C) 会超出电阻箱量程)
    
    calibration_plan = [
        # (标定电阻标称值, 比例臂标签, C 值)
        # ---- 10kΩ 标定 ----
        ("10000", "1:1",  1),
        ("10000", "10:1", 10),
        # ---- 2kΩ 标定 ----
        ("2000",  "1:1",  1),
        ("2000",  "10:1", 10),
        # ---- 200Ω 标定 ----
        ("200",   "1:1",  1),
        ("200",   "1:10", 0.1),
        ("200",   "10:1", 10),
    ]
    
    print(f"\n{'━'*55}")
    print("  测量方案如下:")
    print(f"{'━'*55}")
    print(f"  {'序号':<6}{'标定电阻':>10}{'比例臂 Rx:R0':>14}{'C = R1/R2':>12}")
    print(f"  {'─'*46}")
    for idx, (R_nom, ratio, C_val) in enumerate(calibration_plan, 1):
        print(f"  {idx:<6}{R_nom + ' Ω':>10}{ratio:>14}{C_val:>12}")
    print(f"{'━'*55}")
    print()
    print("  注: 2kΩ 标定不进行 1:10 比例臂测量")
    print("      (R0 = 2000/0.1 = 20000 Ω，超出电阻箱量程)")
    print()
    
    # --- 3. 逐项测量 ---
    all_results = []
    
    for idx, (R_nom, ratio_label, C_val) in enumerate(calibration_plan, 1):
        print(f"\n{'▓'*55}")
        print(f"  第 {idx} 组: 标定 {R_nom} Ω，比例臂 Rx:R0 = {ratio_label}")
        print(f"{'▓'*55}")
        
        result = measure_one_ratio(ratio_label, C_val, R_nom, n_meas)
        all_results.append(result)
        
        if idx < len(calibration_plan):
            input("\n按回车继续下一组测量...")
    
    # --- 4. 汇总表 ---
    print("\n")
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                          测 量 结 果 汇 总 表                              ║")
    print("╠══════════════════════════════════════════════════════════════════════════════╣")
    
    header = (f"  {'标定':>6} {'比例臂':>8} {'R0均值(Ω)':>12} "
              f"{'S(灵敏度)':>10} {'Δ_inst(Ω)':>10} "
              f"{'Rx(Ω)':>12} {'u(Rx)(Ω)':>10} {'u_r(%)':>8}")
    print(header)
    print(f"  {'─'*74}")
    
    for res in all_results:
        S_str = f"{res['S']:.1f}" if res['S'] != Decimal("Infinity") else "∞"
        line = (f"  {res['R_nominal']:>6} {res['ratio_label']:>8} "
                f"{res['R0_mean']:>12.4f} {S_str:>10} "
                f"{res['delta_inst']:>10.4f} "
                f"{res['Rx_mean']:>12.4f} {res['u_Rx']:>10.6f} "
                f"{res['u_r_Rx']*100:>7.2f}%")
        print(line)
    
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    
    # --- 5. 灵敏度分析总结 ---
    print("\n")
    print("┌──────────────────────────────────────────────┐")
    print("│            灵 敏 度 分 析 总 结              │")
    print("├──────────────────────────────────────────────┤")
    
    for res in all_results:
        S_str = f"{res['S']:.2f}" if res['S'] != Decimal("Infinity") else "∞"
        print(f"│ 标定 {res['R_nominal']:>5}Ω  比例臂 {res['ratio_label']:>4}  "
              f"S = {S_str:>8}  │")
    
    print("├──────────────────────────────────────────────┤")
    
    # 找灵敏度最大和最小
    finite_results = [r for r in all_results if r['S'] != Decimal("Infinity")]
    if finite_results:
        best = max(finite_results, key=lambda r: r['S'])
        worst = min(finite_results, key=lambda r: r['S'])
        print(f"│ 最高灵敏度: 标定{best['R_nominal']:>5}Ω 比例臂{best['ratio_label']:>4}  │")
        print(f"│   S = {best['S']:.2f}                              │")
        print(f"│ 最低灵敏度: 标定{worst['R_nominal']:>5}Ω 比例臂{worst['ratio_label']:>4}  │")
        print(f"│   S = {worst['S']:.2f}                              │")
    
    print("├──────────────────────────────────────────────┤")
    print("│ 分析:                                        │")
    print("│ · 灵敏度 S 越大，测量精度越高               │")
    print("│ · S = Δn·R0/ΔR0                             │")
    print("│ · 比例臂比值影响灵敏度                      │")
    print("│ · 合理选择比例臂可优化测量精度              │")
    print("└──────────────────────────────────────────────┘")
    
    # --- 6. 最终修约结果汇总 ---
    print("\n")
    print("╔═══════════════════════════════════════════════════╗")
    print("║           最 终 结 果 (修约后)                   ║")
    print("╠═══════════════════════════════════════════════════╣")
    
    for res in all_results:
        print(f"║ 标定 {res['R_nominal']:>5}Ω  比例臂 {res['ratio_label']:>4}:              ║")
        print(f"║   Rx = {res['Rx_final']} ± {res['u_Rx_final']} Ω              ║")
        print(f"║   (相对不确定度 {res['u_r_Rx']*100:.2f}%)                      ║")
        print(f"╟───────────────────────────────────────────────────╢")
    
    print("╚═══════════════════════════════════════════════════╝")

if __name__ == "__main__":
    main()
