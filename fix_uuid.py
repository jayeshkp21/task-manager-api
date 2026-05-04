import os
import re

files = [
    "src/tasks/service.py",
    "src/tasks/routes.py",
    "src/projects/service.py",
    "src/projects/routes.py",
    "src/comments/routes.py"
]

for f in files:
    with open(f, "r") as file:
        content = file.read()
    
    # Replace project_uid: str, task_uid: str, etc.
    content = re.sub(r'(\b\w+_uid):\s*str\b', r'\1: uuid.UUID', content)
    
    # ensure import uuid
    if "import uuid" not in content:
        content = "import uuid\n" + content
        
    with open(f, "w") as file:
        file.write(content)
