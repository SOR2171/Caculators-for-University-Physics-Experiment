import math
from decimal import Decimal, ROUND_HALF_EVEN

def get_decimal_places(data_strings):
    """获取输入数据中小数点后的位数，用于自适应展示"""
    max_places = 0
    for s in data_strings:
        if '.' in s:
            places = len(s.split('.')[1])
            max_places = max(max_places, places)
    return max_places

def scientific_round(value, uncertainty):
    """
    按照“四舍六入五凑偶”修约：
    1. 不确定度 u 保留一位有效数字
    2. 平均值/结果末位与 u 对齐
    """
    if uncertainty <= 0:
        return str(value), "0"
    
    d_val = Decimal(str(value))
    d_unc = Decimal(str(uncertainty))
    
    u_float = float(d_unc)
    first_digit_pos = math.floor(math.log10(u_float))
    prec = Decimal('1e' + str(first_digit_pos))
    
    u_final = d_unc.quantize(prec, rounding=ROUND_HALF_EVEN)
    val_final = d_val.quantize(prec, rounding=ROUND_HALF_EVEN)
    
    return val_final, u_final

def parse_angle_to_minutes(s):
    """
    将输入解析为内部统一单位：分钟（Decimal）。
    支持格式：
    1. 'D.M' -> D度M分 (例如 '120.15' -> 120*60 + 15 = 7215分)
    2. 'D' (纯数字无点) -> D度 (例如 '120' -> 120*60 = 7200分)
    3. 'D.M.S' -> D度M分S秒 (例如 '120.15.30' -> 7215.5分)
    """
    parts = s.split('.')
    if len(parts) == 1:
        return Decimal(parts[0]) * 60
    elif len(parts) == 2:
        return Decimal(parts[0]) * 60 + Decimal(parts[1])
    else:
        res = Decimal(parts[0]) * 60 + Decimal(parts[1])
        if len(parts) >= 3:
            res += Decimal(parts[2]) / 60
        return res

def format_minutes_as_angle(minutes, prec=None):
    """
    将总分钟数转换为 D° M' 格式，支持保持对齐精度。
    """
    neg = minutes < 0
    minutes = abs(minutes)
    
    d = int(minutes // 60)
    m = minutes % 60
    
    if m >= 60:
        d += 1
        m -= 60
        
    if prec is not None and prec < 1:
        places = abs(prec.as_tuple().exponent)
        m_str = format(m, f'.{places}f')
    else:
        if m == int(m):
            m_str = str(int(m))
        else:
            m_str = format(m, 'f').rstrip('0').rstrip('.')
            
    return f"{'-' if neg else ''}{d}°{m_str}'"
