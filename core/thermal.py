def thermal_load(motor_count, inverter=False):
    base_loss = motor_count * 25
    if inverter:
        base_loss += motor_count * 50
    return base_loss

def ventilation_required(thermal_w):
    if thermal_w < 200:
        return "Ventilação natural suficiente"
    elif thermal_w < 500:
        return "Recomendado ventilador forçado"
    else:
        return "Necessário exaustor ou ar-condicionado de painel"
