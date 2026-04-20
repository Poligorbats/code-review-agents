"""
Static analysis tool: uses AST + pylint + radon to detect code issues.
"""
import ast
import subprocess
import tempfile
import os
import json
from typing import Any
from langchain_core.tools import BaseTool


class StaticAnalysisTool(BaseTool):
    name: str = "static_analysis"
    description: str = (
        "Analyzes Python code for syntax errors, style issues, and complexity. "
        "Input: Python code as a string. "
        "Output: JSON with issues found."
    )

    def _run(self, code: str) -> str:
        results = {
            "syntax_errors": [],
            "pylint_issues": [],
            "complexity": [],
            "ast_issues": [],
        }

        # 1. AST syntax check
        try:
            tree = ast.parse(code)
            results["ast_issues"] = self._check_ast(tree)
        except SyntaxError as e:
            results["syntax_errors"].append({
                "line": e.lineno,
                "message": str(e.msg),
                "text": e.text,
            })
            return json.dumps(results, ensure_ascii=False, indent=2)

        # 2. pylint analysis
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            tmp_path = f.name

        try:
            proc = subprocess.run(
                [
                    "pylint",
                    tmp_path,
                    "--output-format=json",
                    "--disable=C0114,C0115,C0116",  # ignore missing docstrings
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if proc.stdout.strip():
                issues = json.loads(proc.stdout)
                results["pylint_issues"] = [
                    {
                        "line": i["line"],
                        "type": i["type"],
                        "message": i["message"],
                        "symbol": i["symbol"],
                    }
                    for i in issues
                ]
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
            results["pylint_issues"] = [{"message": "pylint not available or timed out"}]
        finally:
            os.unlink(tmp_path)

        # 3. Complexity via radon
        try:
            proc = subprocess.run(
                ["radon", "cc", "-s", "-j", "-"],
                input=code,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if proc.stdout.strip():
                radon_data = json.loads(proc.stdout)
                for _file, blocks in radon_data.items():
                    for block in blocks:
                        if block.get("complexity", 0) > 5:
                            results["complexity"].append({
                                "name": block.get("name"),
                                "complexity": block.get("complexity"),
                                "rank": block.get("rank"),
                                "line": block.get("lineno"),
                            })
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
            pass

        return json.dumps(results, ensure_ascii=False, indent=2)

    def _check_ast(self, tree: ast.AST) -> list[dict]:
        """Check for common AST-level issues."""
        issues = []
        for node in ast.walk(tree):
            # Bare except
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                issues.append({
                    "line": node.lineno,
                    "message": "Bare 'except:' clause catches all exceptions including SystemExit",
                    "type": "warning",
                })
            # Mutable default arguments
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for default in node.args.defaults:
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        issues.append({
                            "line": node.lineno,
                            "message": f"Mutable default argument in function '{node.name}'",
                            "type": "warning",
                        })
            # Use of eval/exec
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in ("eval", "exec"):
                    issues.append({
                        "line": node.lineno,
                        "message": f"Use of '{node.func.id}' is dangerous",
                        "type": "error",
                    })
        return issues

    async def _arun(self, code: str) -> str:
        return self._run(code)
