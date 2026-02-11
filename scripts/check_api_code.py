"""
Check what code is actually loaded in files_api
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import api.files_api
import inspect

# Get the upload_file function
upload_func = api.files_api.upload_file

# Get source code
source = inspect.getsource(upload_func)

# Find the entity_id line
for i, line in enumerate(source.split('\n'), 1):
    if 'entity_id=' in line and 'entity_id if' in line:
        print(f"Line {i}: {line}")
        break
else:
    print("ERROR: Could not find entity_id assignment line!")
    print("\nSearching for any entity_id assignment:")
    for i, line in enumerate(source.split('\n'), 1):
        if 'entity_id=' in line:
            print(f"Line {i}: {line}")
