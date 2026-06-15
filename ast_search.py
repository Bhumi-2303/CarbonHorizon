import ast
import os

for root, _, files in os.walk("backend"):
    for f in files:
        if f.endswith(".py"):
            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8") as file:
                try:
                    tree = ast.parse(file.read(), filename=path)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Assign):
                            for target in node.targets:
                                if isinstance(target, ast.Tuple) and len(target.elts) == 5:
                                    print(f"Found 5-tuple assignment in {path} at line {node.lineno}")
                except Exception as e:
                    pass
