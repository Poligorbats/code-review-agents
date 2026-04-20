"""
Basic tests for tools and agent components.
Run with: pytest tests/
"""
import json
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.static_analysis import StaticAnalysisTool
from tools.code_executor import CodeExecutorTool


# --- StaticAnalysisTool tests ---

class TestStaticAnalysisTool:
    def setup_method(self):
        self.tool = StaticAnalysisTool()

    def test_detects_syntax_error(self):
        code = "def foo(:\n    pass"
        result = json.loads(self.tool.run(code))
        assert len(result["syntax_errors"]) > 0

    def test_detects_bare_except(self):
        code = "try:\n    x = 1\nexcept:\n    pass"
        result = json.loads(self.tool.run(code))
        assert any("bare" in issue["message"].lower() for issue in result["ast_issues"])

    def test_detects_mutable_default(self):
        code = "def foo(x=[]):\n    return x"
        result = json.loads(self.tool.run(code))
        assert any("mutable" in issue["message"].lower() for issue in result["ast_issues"])

    def test_detects_eval_usage(self):
        code = "result = eval('1+1')"
        result = json.loads(self.tool.run(code))
        assert any("eval" in issue["message"].lower() for issue in result["ast_issues"])

    def test_clean_code_has_no_ast_issues(self):
        code = "def add(a: int, b: int) -> int:\n    return a + b"
        result = json.loads(self.tool.run(code))
        assert result["syntax_errors"] == []
        assert result["ast_issues"] == []


# --- CodeExecutorTool tests ---

class TestCodeExecutorTool:
    def setup_method(self):
        self.tool = CodeExecutorTool()

    def test_runs_simple_code(self):
        code = "print('hello')"
        result = json.loads(self.tool.run(code))
        assert result["success"] is True
        assert "hello" in result["stdout"]

    def test_captures_stderr(self):
        code = "raise ValueError('test error')"
        result = json.loads(self.tool.run(code))
        assert result["success"] is False
        assert result["exit_code"] != 0

    def test_blocks_forbidden_imports(self):
        code = "import os\nprint(os.getcwd())"
        result = json.loads(self.tool.run(code))
        assert result["success"] is False
        assert "blocked" in result["stderr"].lower()

    def test_blocks_subprocess_import(self):
        code = "import subprocess\nsubprocess.run(['ls'])"
        result = json.loads(self.tool.run(code))
        assert result["success"] is False

    def test_handles_syntax_error(self):
        code = "def foo(:\n    pass"
        result = json.loads(self.tool.run(code))
        assert result["success"] is False

    def test_math_operations(self):
        code = "result = sum([1,2,3,4,5])\nprint(result)"
        result = json.loads(self.tool.run(code))
        assert result["success"] is True
        assert "15" in result["stdout"]
