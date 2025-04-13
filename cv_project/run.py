import os
import sys
import traceback

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(project_root, "src"))

from src.main import main

try:
    main()
except Exception as e:
    print(f"Error in run.py: {e}")
    error_log_path = os.path.join(project_root, "error_log.txt")
    with open(error_log_path, "a") as f:
        f.write(f"Error: {e}\n{traceback.format_exc()}\n")
    raise