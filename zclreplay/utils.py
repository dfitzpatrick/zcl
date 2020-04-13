def zc_bunker_type(index: int) -> str:
    marine = [
        1,2,3,4,5,6,8,15,16,23,24,31,32,39,40,47,48,55,57,58,59,60,61,62
        ]
    reaper = [
        9,10,11,12,13,14,17,22,25,30,33,38,41,46,49,50,51,52,53,54
    ]
    marauder = [
        18,19,20,21,26,29,34,37,42,43,44,45,
    ]
    ghost = [
        27,28,35,36
    ]
    if index in marine:
        return "Marine"
    elif index in reaper:
        return "Reaper"
    elif index in marauder:
        return "Marauder"
    elif index in ghost:
        return "Ghost"
    else:
        return "Unknown"

def rgb_to_hsl(r, g, b):
    r = float(r)
    g = float(g)
    b = float(b)
    high = max(r, g, b)
    low = min(r, g, b)
    h, s, v = ((high + low) / 2,)*3

    if high == low:
        h = 0.0
        s = 0.0
    else:
        d = high - low
        s = d / (2 - high - low) if l > 0.5 else d / (high + low)
        h = {
            r: (g - b) / d + (6 if g < b else 0),
            g: (b - r) / d + 2,
            b: (r - g) / d + 4,
        }[high]
        h /= 6

    return h, s, v