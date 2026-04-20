"""
Analyzer Agent: detects bugs, code smells, and style issues using
static analysis tools + LLM reasoning.
"""
import os
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from tools import StaticAnalysisTool


ANALYZER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert Python code analyzer. Your task is to thoroughly analyze 
the provided Python code and identify ALL issues including:
- Bugs and logical errors
- Security vulnerabilities  
- Performance problems
- Code smells and anti-patterns
- Style violations (PEP8)
- Naming issues

You also have access to static analysis results (AST + pylint + complexity metrics).

Format your response as a structured report with sections:
1. CRITICAL ISSUES (bugs, security)
2. WARNINGS (performance, smells)  
3. STYLE ISSUES (PEP8, naming)
4. SUMMARY (overall quality score 1-10 and brief assessment)

Be specific — include line numbers when possible."""),
    ("human", """Analyze this Python code:

```python
{code}
```

Static analysis results:
{static_results}

Provide a detailed analysis report."""),
])


class AnalyzerAgent:
    def __init__(self):
        self.model = os.getenv("ANALYZER_MODEL", "codellama:7b")
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.llm = ChatOllama(
            model=self.model,
            base_url=self.base_url,
            temperature=0.1,  # low temp for precise analysis
        )
        self.static_tool = StaticAnalysisTool()
        self.chain = ANALYZER_PROMPT | self.llm | StrOutputParser()

    def run(self, code: str) -> dict:
        """Run static analysis + LLM analysis on the provided code."""
        print(f"[Анализатор] Запуск статического анализа с {self.model}...")

        # Step 1: static tools
        static_results = self.static_tool.run(code)

        # Step 2: LLM analysis
        analysis = self.chain.invoke({
            "code": code,
            "static_results": static_results,
        })

        return {
            "agent": "analyzer",
            "static_results": static_results,
            "analysis": analysis,
        }
