import math
from decimal import Decimal, ROUND_HALF_EVEN

"""
Speed of Sound Calculator (Successive Difference Method)
声速测量计算器 (逐差法)

参考了 Newton's rings.py 的高精度与不确定度修约逻辑。

计算公式说明:
1. 理论声速公式:
   v_t = 331.45 * sqrt(1 + t / 273.15)
   其中 t 为摄氏温度。

2. 逐差法计算波长 λ:
   本实验两组数据均为 12 个点，分成两组进行逐差：Δx_i = x_{i+6} - x_i (i=1..6)
   - 干涉法 (驻波法) 找振幅最大处：相邻两次最大处间距为 λ/2
     因此 Δx = 6 * (λ/2) = 3λ => λ = Δx_avg / 3
   - 相位法 (李萨如图像) 变为相同方向直线：相邻两次相位改变 2π，间距为 λ
     因此 Δx = 6 * λ => λ = Δx_avg / 6

3. 声速公式:
   v = f * λ

4. 不确定度传递公式:
   - Δx_avg 的 A 类不确定度: u_A(Δx_avg) = S_Δ / sqrt(M) (其中 S_Δ 为逐差后 Δx 的标准差, M=6)
   - 坐标 x 的 B 类不确定度: u_B(x) = Δ_inst / sqrt(3) (假设均匀分布)
   - 逐差平均值的 B 类不确定度传播: u_B(Δx_avg) = sqrt(2/M) * u_B(x)
   - Δx_avg 的合成不确定度: u_c(Δx_avg) = sqrt(u_A^2 + u_B^2)
   - 波长 λ 的不确定度: 
     干涉法 u(λ) = u_c(Δx_avg) / 3
     相位法 u(λ) = u_c(Δx_avg) / 6
   - 声速 v 的不确定度 (忽略 f 的极小不确定度): u(v) = f * u(λ)
"""

from utils import scientific_round

def calculate_method(method_name, f, k, delta_inst):
    print(f"\n========================================")
    print(f"        {method_name}        ")
    print(f"========================================")
    print("请输入12个坐标数据 (单位: mm)。")
    
    x_vals = []
    for i in range(1, 13):
        while True:
            try:
                val_str = input(f"x_{i:02d} = ").strip()
                if not val_str:
                    continue
                x_vals.append(Decimal(val_str))
                break
            except Exception:
                print("无效输入！请输入正确的数值。")

    # 1. 逐差计算
    M = 6
    deltas = []
    print("\n--- 逐差过程 ---")
    for i in range(M):
        diff = x_vals[i + M] - x_vals[i]
        deltas.append(diff)
        print(f"Δx_{i+1} = x_{i+M+1} - x_{i+1} = {x_vals[i+M]} - {x_vals[i]} = {diff} mm")
        
    mean_delta = sum(deltas) / Decimal(str(M))
    
    # 2. 波长与声速计算
    # 将毫米转换为米计算速度
    wavelength_mm = mean_delta / Decimal(str(k))
    wavelength_m = wavelength_mm / Decimal("1000")
    velocity = Decimal(str(f)) * wavelength_m
    
    # 3. 不确定度计算
    # u_A
    variance_delta = sum((d - mean_delta)**2 for d in deltas) / Decimal(str(M - 1))
    s_delta = Decimal(str(math.sqrt(float(variance_delta))))
    u_a_delta = s_delta / Decimal(str(math.sqrt(M)))
    
    # u_B
    u_x = delta_inst / Decimal(str(math.sqrt(3)))
    u_b_delta = Decimal(str(math.sqrt(2.0 / M))) * u_x
    
    # u_c(Δx_avg)
    u_delta_combined = Decimal(str(math.sqrt(float(u_a_delta**2 + u_b_delta**2))))
    
    # 传播到波长和声速
    u_wavelength_mm = u_delta_combined / Decimal(str(k))
    u_wavelength_m = u_wavelength_mm / Decimal("1000")
    u_velocity = Decimal(str(f)) * u_wavelength_m
    
    # 4. 修约与展示
    v_final, uv_final = scientific_round(velocity, u_velocity)
    
    print("\n--- 中间统计结果 (高精度) ---")
    print(f"平均差值 Δx_avg: {mean_delta:.6f} mm")
    print(f"Δx 的标准差 S_Δ: {s_delta:.6f} mm")
    print(f"Δx_avg 的 A 类不确定度 u_A: {u_a_delta:.6f} mm")
    print(f"Δx_avg 的 B 类不确定度 u_B: {u_b_delta:.6f} mm")
    print(f"波长 λ: {wavelength_mm:.6f} mm")
    print(f"波长的不确定度 u(λ): {u_wavelength_mm:.6f} mm")
    
    print("\n========================================")
    print(f"     {method_name} 最终结果 (四舍六入五凑偶)")
    print(f"     v = {v_final} ± {uv_final} m/s")
    print("========================================")

def main():
    print("========================================")
    print("           声速测量计算器               ")
    print("========================================")
    
    t_input = input("请输入环境温度 t (℃) [默认 24]: ").strip() or "24"
    f_input = input("请输入谐振波频率 f (Hz) [默认 37000]: ").strip() or "37000"
    delta_inst_input = input("请输入游标卡尺/测微鼓轮分度值误差 Δ_inst (mm) [默认 0.02]: ").strip() or "0.02"
    
    t = float(t_input)
    f = float(f_input)
    delta_inst = Decimal(delta_inst_input)
    
    # 计算理论声速
    v_t = 331.45 * math.sqrt(1 + t / 273.15)
    print(f"\n理论声速 v_t = {v_t:.2f} m/s (温度 {t} ℃)")
    
    while True:
        print("\n请选择计算方法:")
        print("1. 干涉法 (驻波法) - 振幅最大处")
        print("2. 相位法 (李萨如法) - 相同方向直线")
        print("3. 退出")
        choice = input("请输入选项 (1/2/3): ").strip()
        
        if choice == '1':
            # 干涉法 k = 3 (Δx_avg = 3λ)
            calculate_method("干涉法 (振幅最大处)", f, 3, delta_inst)
        elif choice == '2':
            # 相位法 k = 6 (Δx_avg = 6λ)
            calculate_method("相位法 (相同方向直线)", f, 6, delta_inst)
        elif choice == '3':
            print("退出程序。")
            break
        else:
            print("无效选项，请重新输入。")

if __name__ == "__main__":
    main()
