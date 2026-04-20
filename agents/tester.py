"""
Tester Agent: generates pytest tests for the refactored code,
runs them via CodeExecutorTool, and reports results.
"""
import os
import re
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from tools import CodeExecutorTool
import json


TESTER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a Python testing expert. Your task is to write comprehensive 
pytest tests for the provided code.

Requirements:
1. Write tests for ALL public functions
2. Include edge cases: empty input, None values, boundary values, invalid input
3. Test that the refactored code produces same results as expected
4. Use pytest conventions: functions named test_*, use assert statements
5. Include at least 3-5 test cases per function
6. Add a brief comment explaining each test

Output ONLY valid Python code with pytest tests in a single ```python ... ``` block.
The code being tested will be imported or included inline — use the functions directly."""),
    ("human", """Code to test:
```python
{code}
```

Write comprehensive pytest tests for this code."""),
])


class TesterAgent:
    def __init__(self):
        self.model = os.getenv("TESTER_MODEL", "codellama:7b")
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.llm = ChatOllama(
            model=self.model,
            base_url=self.base_url,
            temperature=0.1,
        )
        self.executor = CodeExecutorTool()
        self.chain = TESTER_PROMPT | self.llm | StrOutputParser()

    def run(self, original_code: str, refactored_code: str) -> dict:
        """Generate tests and execute them against refactored code."""
        print(f"[Tester] Generating tests with {self.model}...")

        # Generate tests
        response = self.chain.invoke({"code": refactored_code})
        test_code = self._extract_code(response)

        # Combine refactored code + tests for execution
        full_code = self._prepare_execution_code(refactored_code, test_code)

        # Run tests
        print("[Tester] Running generated tests...")
        execution_result = json.loads(self.executor.run(full_code))

        # Parse test results
        passed, failed, errors = self._parse_test_results(execution_result)

        return {
            "agent": "tester",
            "test_code": test_code,
            "execution_result": execution_result,
            "tests_passed": passed,
            "tests_failed": failed,
            "test_errors": errors,
            "success": execution_result.get("success", False),
        }

    def _extract_code(self, response: str) -> str:
        """Extract Python code from markdown code block."""
        pattern = r"```python\s*(.*?)```"
        match = re.search(pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()
        pattern = r"```\s*(.*?)```"
        match = re.search(pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return response

    def _prepare_execution_code(self, refactored_code: str, test_code: str) -> str:
        """Combine code and tests for inline execution (without pytest runner)."""
        # For sandbox execution, run tests as plain functions
        combined = f"""
{refactored_code}

# ---- TESTS ----
{test_code}

# Run all test functions
import traceback
passed = 0
failed = 0
test_funcs = [name for name in dir() if name.startswith('test_')]
for name in test_funcs:
    func = eval(name)
    try:
        func()
        print(f"PASSED: {{name}}")
        passed += 1
    except Exception as e:
        print(f"FAILED: {{name}} — {{e}}")
        failed += 1

print(f"\\nResults: {{passed}} passed, {{failed}} failed")
"""
        return combined

    def _parse_test_results(self, execution_result: dict) -> tuple[int, int, list]:
        """Parse test output to count passed/failed."""
        stdout = execution_result.get("stdout", "")
        passed = stdout.count("PASSED:")
        failed = stdout.count("FAILED:")
        errors = [
            line for line in stdout.split("\n")
            if line.startswith("FAILED:")
        ]
        return passed, failed, errors
