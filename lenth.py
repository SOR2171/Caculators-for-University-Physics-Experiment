import math
from decimal import Decimal, ROUND_HALF_EVEN

from utils import get_decimal_places, scientific_round

def calc_uncertainty(data_strs, res_str="0.05"):
    # 转换为 Decimal 进行高精度计算
    data = [Decimal(s) for s in data_strs]
    res = Decimal(res_str)
    n = len(data)
    
    # 1. 计算平均值
    places = get_decimal_places(data_strs)
    sum_val = sum(data)
    mean = sum_val / n
    # 修改：平均值修约使用“四舍六入五凑偶”
    mean_final = mean.quantize(Decimal('1.' + '0' * places), rounding=ROUND_HALF_EVEN)
    
    # 2. 计算标准差 s
    variance = sum((x - mean) ** 2 for x in data) / (n - 1)
    s = Decimal(str(math.sqrt(float(variance))))
    
    # 3. A类不确定度 u_A
    u_A = s / Decimal(str(math.sqrt(n)))
    
    # 4. B类不确定度 u_B (仪器误差)
    u_B = res / Decimal(str(math.sqrt(3)))
    
    # 5. 合成不确定度 u
    u = Decimal(str(math.sqrt(float(u_A**2 + u_B**2))))
    
    return mean_final, s, u_A, u_B, u

def format_final_result(mean, u):
    """
    按照“四舍六入五凑偶”修约：
    1. 不确定度 u 保留一位有效数字
    2. 平均值末位与 u 对齐
    """
    mean_final, u_final = scientific_round(mean, u)
    return f"f = {mean_final} ± {u_final}"

if __name__ == "__main__":
    # ... (后续输入输出逻辑保持不变)
    print("请输入数据，用空格分隔：")
    raw_input = input().split()
    
    print("请输入仪器分度值（默认 0.05）：")
    res_input = input().strip() or "0.05"
    
    mean_f, s, u_A, u_B, u = calc_uncertainty(raw_input, res_input)
    
    print("\n--- 中间计算过程 (高精度展示) ---")
    print(f"平均值 (原始精度): {mean_f}")
    print(f"标准差 s: {s:.6f}")
    print(f"A类不确定度 u_A: {u_A:.6f}")
    print(f"B类不确定度 u_B: {u_B:.6f}")
    print(f"合成不确定度 u: {u:.6f}")
    
    print("\n--- 最终修约结果 (四舍六入五凑偶) ---")
    print(format_final_result(mean_f, u))