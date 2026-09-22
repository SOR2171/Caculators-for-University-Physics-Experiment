import math
from decimal import Decimal

def calculate_stats(data_list, delta_inst):
    """
    计算一组数据的平均值、A类、B类及合成不确定度。
    支持输入 list of Decimal 或 list of float/str/int。
    
    返回: (mean, u_combined, u_a, u_b, s)
    """
    n = len(data_list)
    decimal_data = [Decimal(str(x)) for x in data_list]
    mean = sum(decimal_data) / Decimal(n)
    
    if n > 1:
        variance = sum((x - mean)**2 for x in decimal_data) / Decimal(n - 1)
        s = Decimal(str(math.sqrt(float(variance))))
        u_a = s / Decimal(str(math.sqrt(n)))
    else:
        s = Decimal("0")
        u_a = Decimal("0")
        
    u_b = Decimal(str(delta_inst)) / Decimal(str(math.sqrt(3)))
    u_combined = Decimal(str(math.sqrt(float(u_a**2 + u_b**2))))
    
    return mean, u_combined, u_a, u_b, s

def linear_regression(x_list, y_list):
    """
    最小二乘法线性回归: y = k·x + b
    返回: (k, b, r, u_k)
    u_k = |k| · √[(1/r² − 1) / (n − 2)]
    支持 input numbers as Decimal or float.
    """
    n = len(x_list)
    x_dec = [Decimal(str(x)) for x in x_list]
    y_dec = [Decimal(str(y)) for y in y_list]
    
    x_mean = sum(x_dec) / Decimal(n)
    y_mean = sum(y_dec) / Decimal(n)
    
    L_xx = sum((x - x_mean)**2 for x in x_dec)
    L_yy = sum((y - y_mean)**2 for y in y_dec)
    L_xy = sum((x_dec[i] - x_mean) * (y_dec[i] - y_mean) for i in range(n))
    
    k = L_xy / L_xx if L_xx != 0 else Decimal("0")
    b = y_mean - k * x_mean
    
    denom = Decimal(str(math.sqrt(float(L_xx * L_yy)))) if L_xx * L_yy > 0 else Decimal("1")
    r = L_xy / denom
    
    r_float = float(r)
    if abs(r_float) < 1.0 and n > 2:
        u_k_float = float(abs(k)) * math.sqrt((1.0 / (r_float**2) - 1.0) / (n - 2))
    else:
        u_k_float = 0.0
    u_k = Decimal(str(u_k_float))
    
    return k, b, r, u_k
