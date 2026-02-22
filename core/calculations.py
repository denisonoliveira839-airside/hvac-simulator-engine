import math

def motor_current(power_cv, voltage=380, efficiency=0.9, pf=0.85):
    power_w = power_cv * 736
    current = power_w / (math.sqrt(3) * voltage * efficiency * pf)
    return round(current, 2)

def total_current(motors, resistance_kw=0):
    motor_total = sum(motors)
    resistance_current = (resistance_kw * 1000) / (math.sqrt(3) * 380) if resistance_kw > 0 else 0
    return round(motor_total + resistance_current, 2)

def breaker_selection(current):
    standard = [16, 20, 25, 32, 40, 50, 63, 80, 100]
    for b in standard:
        if current <= b:
            return b
    return standard[-1]
