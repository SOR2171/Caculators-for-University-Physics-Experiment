import math
from decimal import Decimal

from utils import (
    parse_angle_to_minutes,
    format_minutes_as_angle,
    scientific_round
)

def calc_uncertainty(data_strs, res_str="1"):
    # 转换为分钟进行高精度计算
    data = [parse_angle_to_minutes(s) for s in data_strs]
    res = Decimal(res_str)  # 仪器误差，单位：分
    n = len(data)
    
    # 1. 计算平均值
    sum_val = sum(data)
    mean = sum_val / n
    
    # 2. 计算标准差 s
    if n > 1:
        variance = sum((x - mean) ** 2 for x in data) / (n - 1)
        s = Decimal(str(math.sqrt(float(variance))))
    else:
        s = Decimal('0')
    
    # 3. A类不确定度 u_A
    u_A = s / Decimal(str(math.sqrt(n)))
    
    # 4. B类不确定度 u_B (仪器误差)
    u_B = res / Decimal(str(math.sqrt(3)))
    
    # 5. 合成不确定度 u
    u = Decimal(str(math.sqrt(float(u_A**2 + u_B**2))))
    
    return mean, s, u_A, u_B, u

def format_final_result(mean_minutes, u_minutes):
    """
    按照“四舍六入五凑偶”修约：
    1. 不确定度 u 保留一位有效数字
    2. 平均值末位与 u 对齐
    """
    u_float = float(u_minutes)
    if u_float == 0:
        return f"θ = {format_minutes_as_angle(mean_minutes)} ± 0'"
        
    first_digit_pos = math.floor(math.log10(u_float))
    prec = Decimal('1e' + str(first_digit_pos))
    
    mean_final_val, u_final = scientific_round(mean_minutes, u_minutes)
    
    mean_str = format_minutes_as_angle(mean_final_val, prec)
    u_str = f"{u_final}'"
    
    return f"θ = {mean_str} ± {u_str}"

if __name__ == "__main__":
    print("=== 角度不确定度计算器 ===")
    print("输入格式: '度.分' (如 120.15 表示 120°15')，多个数据用空格隔开。")
    
    try:
        user_input = input("请输入数据：").split()
        if not user_input:
            print("未输入数据！")
        else:
            res_input = input("请输入仪器分度值 (单位: 分，默认 1)：").strip() or "1"
            
            mean_v, s, u_A, u_B, u = calc_uncertainty(user_input, res_input)
            
            print("\n--- 中间计算过程 ---")
            print(f"平均值: {format_minutes_as_angle(mean_v)} ({mean_v:.4f}')")
            print(f"标准差 s: {s:.6f}'")
            print(f"A类不确定度 u_A: {u_A:.6f}'")
            print(f"B类不确定度 u_B: {u_B:.6f}'")
            print(f"合成不确定度 u: {u:.6f}'")
            
            print("\n--- 最终修约结果 (四舍六入五凑偶) ---")
            print(format_final_result(mean_v, u))
            
    except Exception as e:
        print(f"错误: {e}")