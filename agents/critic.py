"""
Critic Agent: uses Chain-of-Thought reasoning to prioritize issues
found by the Analyzer and decide what MUST be fixed vs what is optional.
"""
import os
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from tools import DocSearchTool


CRITIC_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a senior software engineer doing a critical code review.
Your task is to evaluate the analysis report and PRIORITIZE issues using 
Chain-of-Thought reasoning.

For each issue, think step by step:
1. What is the actual impact of this issue? (correctness, security, performance, readability)
2. How likely is it to cause problems in production?
3. How hard is it to fix?
4. What is the priority: MUST FIX / SHOULD FIX / NICE TO HAVE?

Relevant best practices from documentation:
{docs}

Format your output as:
## Priority Assessment

### MUST FIX
- [Issue]: [CoT reasoning] → [Priority: CRITICAL/HIGH]

### SHOULD FIX  
- [Issue]: [CoT reasoning] → [Priority: MEDIUM]

### NICE TO HAVE
- [Issue]: [CoT reasoning] → [Priority: LOW]

## Refactoring Instructions
Provide clear, specific instructions for the Refactorer agent about what to fix and how."""),
    ("human", """Original code:
```python
{code}
```

Analysis report from Analyzer agent:
{analysis}

Evaluate and prioritize all issues. Provide refactoring instructions."""),
])


class CriticAgent:
    def __init__(self):
        self.model = os.getenv("CRITIC_MODEL", "codellama:7b")
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.llm = ChatOllama(
            model=self.model,
            base_url=self.base_url,
            temperature=0.2,
        )
        self.doc_tool = DocSearchTool()
        self.chain = CRITIC_PROMPT | self.llm | StrOutputParser()

    def run(self, code: str, analysis: str) -> dict:
        """Prioritize issues using CoT reasoning."""
        print(f"[Критик] Оценка проблем с {self.model}...")

        # Fetch relevant documentation
        # Extract key topics from analysis for doc search
        topics = self._extract_topics(analysis)
        docs = self.doc_tool.run(topics)

        critique = self.chain.invoke({
            "code": code,
            "analysis": analysis,
            "docs": docs,
        })

        return {
            "agent": "critic",
            "docs_used": docs,
            "critique": critique,
        }

    def _extract_topics(self, analysis: str) -> str:
        """Extract key topics from analysis for documentation search."""
        keywords = []
        lower = analysis.lower()
        if "exception" in lower or "except" in lower:
            keywords.append("exception handling")
        if "loop" in lower or "for" in lower:
            keywords.append("loop optimization")
        if "mutable" in lower or "default" in lower:
            keywords.append("mutable default arguments")
        if "complexity" in lower:
            keywords.append("cyclomatic complexity")
        if "type" in lower or "hint" in lower:
            keywords.append("type hints")
        return " ".join(keywords) if keywords else "python best practices"
