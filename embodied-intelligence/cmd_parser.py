import re
import numpy as np

def parse_instruction(text, env=None):
    text = text.lower().strip()

    presets = {
        "home": np.array([0.45, 0.0, 0.35]),
        "left": np.array([0.35, 0.15, 0.30]),
        "right": np.array([0.35, -0.15, 0.30]),
        "high": np.array([0.45, 0.0, 0.45]),
        "low": np.array([0.45, 0.0, 0.25]),
    }

    for name, pos in presets.items():
        if name in text:
            return {"action": "goto", "target": pos, "label": name}

    coords = re.findall(r'([XYZ])\s*([-+]?\d*\.?\d+)', text, re.IGNORECASE)
    if len(coords) >= 3:
        pos = np.array([0.45, 0.0, 0.35])
        for axis, val_str in coords:
            val = float(val_str)
            if axis.lower() == 'x':
                pos[0] = max(0.20, min(0.70, val))
            elif axis.lower() == 'y':
                pos[1] = max(-0.30, min(0.30, val))
            elif axis.lower() == 'z':
                pos[2] = max(0.15, min(0.60, val))
        return {"action": "goto", "target": pos, "label": "custom"}

    if "重置" in text or "复位" in text:
        return {"action": "reset"}

    return {"action": "unknown", "text": text}