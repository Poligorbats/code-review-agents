"""
Refactorer Agent: produces improved, clean Python code based on
the Analyzer's findings and Critic's prioritized instructions.
"""
import os
import re
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


REFACTORER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert Python developer. Your task is to rewrite the 
provided Python code, fixing ALL issues identified in the critique.

Rules:
1. Fix ALL "MUST FIX" issues without exception
2. Fix "SHOULD FIX" issues where possible
3. Preserve the original functionality — do NOT change what the code does
4. Follow PEP8 style guide
5. Add type hints to all functions
6. Add brief docstrings to functions that lack them
7. Keep variable and function names meaningful

Output ONLY the improved Python code in a single ```python ... ``` block.
After the code block, add a short ## Changes Made section listing what you fixed."""),
    ("human", """Original code:
```python
{code}
```

Critique and refactoring instructions:
{critique}

Provide the refactored code."""),
])


class RefactorerAgent:
    def __init__(self):
        self.model = os.getenv("REFACTORER_MODEL", "codellama:7b")
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.llm = ChatOllama(
            model=self.model,
            base_url=self.base_url,
            temperature=0.1,
        )
        self.chain = REFACTORER_PROMPT | self.llm | StrOutputParser()

    def run(self, code: str, critique: str) -> dict:
        """Generate refactored code based on critique."""
        print(f"[Refactorer] Generating improved code with {self.model}...")

        response = self.chain.invoke({
            "code": code,
            "critique": critique,
        })

        refactored_code = self._extract_code(response)
        changes = self._extract_changes(response)

        return {
            "agent": "refactorer",
            "refactored_code": refactored_code,
            "changes_made": changes,
            "full_response": response,
        }

    def _extract_code(self, response: str) -> str:
        """Extract Python code from markdown code block."""
        pattern = r"```python\s*(.*?)```"
        match = re.search(pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()
        # Fallback: try generic code block
        pattern = r"```\s*(.*?)```"
        match = re.search(pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return response  # return raw if no code block found

    def _extract_changes(self, response: str) -> str:
        """Extract the Changes Made section."""
        if "## Changes Made" in response:
            return response.split("## Changes Made", 1)[1].strip()
        return "See refactored code above."
