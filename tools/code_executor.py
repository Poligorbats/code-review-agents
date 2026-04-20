"""
Safe code execution tool using subprocess with timeout and isolation.
"""
import subprocess
import tempfile
import os
import json
from langchain_core.tools import BaseTool


FORBIDDEN_IMPORTS = {
    "os", "sys", "subprocess", "shutil", "socket",
    "requests", "urllib", "http", "ftplib", "smtplib",
    "pickle", "shelve", "importlib",
}


class CodeExecutorTool(BaseTool):
    name: str = "code_executor"
    description: str = (
        "Executes Python code in a sandboxed subprocess and returns stdout, stderr, "
        "and exit code. Use to verify that code runs correctly or to run tests. "
        "Input: Python code as a string."
    )
    timeout: int = 10

    def _is_safe(self, code: str) -> tuple[bool, str]:
        """Basic safety check before execution."""
        import ast
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, f"Syntax error: {e}"

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    if root in FORBIDDEN_IMPORTS:
                        return False, f"Forbidden import: {alias.name}"
            if isinstance(node, ast.ImportFrom):
                if node.module:
                    root = node.module.split(".")[0]
                    if root in FORBIDDEN_IMPORTS:
                        return False, f"Forbidden import from: {node.module}"
        return True, ""

    def _run(self, code: str) -> str:
        safe, reason = self._is_safe(code)
        if not safe:
            return json.dumps({
                "success": False,
                "stdout": "",
                "stderr": f"Execution blocked: {reason}",
                "exit_code": -1,
            })

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            tmp_path = f.name

        try:
            proc = subprocess.run(
                ["python", tmp_path],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            return json.dumps({
                "success": proc.returncode == 0,
                "stdout": proc.stdout[:2000],
                "stderr": proc.stderr[:1000],
                "exit_code": proc.returncode,
            }, ensure_ascii=False)
        except subprocess.TimeoutExpired:
            return json.dumps({
                "success": False,
                "stdout": "",
                "stderr": f"Execution timed out after {self.timeout}s",
                "exit_code": -1,
            })
        finally:
            os.unlink(tmp_path)

    async def _arun(self, code: str) -> str:
        return self._run(code)
