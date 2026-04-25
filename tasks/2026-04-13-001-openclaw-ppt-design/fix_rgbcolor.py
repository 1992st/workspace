import re

path = '/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/tasks/2026-04-13-001-openclaw-ppt-design/create_ppt.py'
with open(path, 'r') as f:
    text = f.read()

# Find all RGBColor(r, g, b, alpha) and replace with manually blended dark color (on black background)
def repl(m):
    r = int(m.group(1))
    g = int(m.group(2))
    b = int(m.group(3))
    alpha = float(m.group(4))
    # Blend with black
    nr = int(r * alpha)
    ng = int(g * alpha)
    nb = int(b * alpha)
    return f"RGBColor({nr}, {ng}, {nb})"

new_text = re.sub(r"RGBColor\((\d+),\s*(\d+),\s*(\d+),\s*([0-9.]+)\)", repl, text)

with open(path, 'w') as f:
    f.write(new_text)

print("Fixed RGBColor calls in create_ppt.py")
