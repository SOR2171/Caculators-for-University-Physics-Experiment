from decimal import Decimal

def input_float(prompt, default=None):
    """输入一个浮点数值，支持默认值"""
    while True:
        try:
            suffix = f" (默认 {default})" if default is not None else ""
            val = input(f"{prompt}{suffix}: ").strip()
            if not val and default is not None:
                return float(default)
            if not val:
                continue
            return float(val)
        except Exception:
            print("  输入无效，请输入数字。")

def input_decimal(prompt, default=None):
    """输入一个 Decimal 值，支持默认值"""
    while True:
        try:
            suffix = f" (默认 {default})" if default is not None else ""
            val = input(f"{prompt}{suffix}: ").strip()
            if not val and default is not None:
                return Decimal(str(default))
            if not val:
                continue
            return Decimal(val)
        except Exception:
            print("  输入无效，请输入数字。")

def input_int(prompt, default=None):
    """输入一个整数，支持默认值"""
    while True:
        try:
            suffix = f" (默认 {default})" if default is not None else ""
            val = input(f"{prompt}{suffix}: ").strip()
            if not val and default is not None:
                return default
            if not val:
                continue
            return int(val)
        except Exception:
            print("  输入无效，请输入整数。")

def input_data_group(name, count, unit=""):
    """输入一组重复测量的数值"""
    prompt_unit = f" (单位: {unit})" if unit else ""
    print(f"\n请输入 {name} 的 {count} 次测量值{prompt_unit}:")
    data = []
    for i in range(count):
        while True:
            try:
                val = input(f"第 {i+1} 次 = ").strip()
                if not val: continue
                data.append(Decimal(val))
                break
            except Exception:
                print("输入无效，请输入数字。")
    return data
