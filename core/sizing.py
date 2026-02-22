def busbar_size(current, density=1.5):
    section = current / density
    width = 20
    thickness = round(section / width, 2)
    return width, thickness
