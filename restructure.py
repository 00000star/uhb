import os
import shutil
import re
from pathlib import Path

base_dir = Path("/sdcard/Antigravity_Projects/uhb")
os.chdir(base_dir)

# 1. Rename uhb file
if os.path.exists("uhb") and os.path.isfile("uhb"):
    os.rename("uhb", "uhb_cli.py")

# 2. Create uhb directory
os.makedirs("uhb", exist_ok=True)
if os.path.exists("uhb_cli.py"):
    os.rename("uhb_cli.py", "uhb/cli.py")
    
# 3. Create __init__.py in uhb
with open("uhb/__init__.py", "w") as f:
    f.write('__version__ = "0.1.0"\n')

packages = [d for d in os.listdir(".") if d.startswith("uhb-") and os.path.isdir(d)]
deps = set()

for pkg in packages:
    module_name = pkg.replace("-", "_")
    short_name = pkg.split("-")[1]
    
    # move source
    src_dir = os.path.join(pkg, module_name)
    if os.path.exists(src_dir):
        dest_dir = os.path.join("uhb", short_name)
        shutil.move(src_dir, dest_dir)
        
    # move tests if exist
    tests_dir = os.path.join(pkg, "tests")
    if os.path.exists(tests_dir):
        dest_tests = os.path.join("tests", f"test_{short_name}")
        shutil.move(tests_dir, dest_tests)
        
    # read pyproject.toml for deps
    toml_path = os.path.join(pkg, "pyproject.toml")
    if os.path.exists(toml_path):
        with open(toml_path) as f:
            in_deps = False
            for line in f:
                if line.strip().startswith("dependencies ="):
                    in_deps = True
                    continue
                if in_deps and line.strip() == "]":
                    in_deps = False
                    continue
                if in_deps:
                    match = re.search(r'["\']([^"\']+)["\']', line)
                    if match:
                        dep = match.group(1)
                        if not dep.startswith("uhb-"):
                            deps.add(dep)
                            
    # remove pkg
    shutil.rmtree(pkg)
    
print("Collected deps:")
for d in sorted(deps):
    print(d)

