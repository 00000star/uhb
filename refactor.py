import os
import re
from pathlib import Path

base_dir = Path("/sdcard/Antigravity_Projects/uhb")

modules = ["core", "benchmark", "evolution", "compiler", "dashboard", "environment", "personality", "systems", "tools", "memory", "community"]

def process_file(path):
    with open(path, "r") as f:
        content = f.read()
        
    orig_content = content
    
    # replace uhb_<module> with uhb.<module>
    for mod in modules:
        content = re.sub(r'uhb_' + mod + r'\b', f'uhb.{mod}', content)
        
    if content != orig_content:
        with open(path, "w") as f:
            f.write(content)

for root, dirs, files in os.walk(base_dir):
    if ".git" in root or "venv" in root:
        continue
    for f in files:
        if f.endswith(".py") or f.endswith("Makefile") or f.endswith(".md"):
            process_file(os.path.join(root, f))
            
print("Done refactoring imports.")
