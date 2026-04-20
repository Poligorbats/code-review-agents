"""
Documentation search tool using ChromaDB vector store + Ollama embeddings.
Provides relevant Python/best-practices documentation for the agents.
"""
import os
from langchain_core.tools import BaseTool
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document


# Built-in knowledge base: Python best practices snippets
KNOWLEDGE_BASE = [
    ("Use list comprehensions instead of for-loops for simple transformations. "
     "Example: squares = [x**2 for x in range(10)] is better than a for-loop appending to a list."),
    ("Avoid mutable default arguments in function definitions. "
     "Use None as default and assign inside the function: def f(x, lst=None): lst = lst or []"),
    ("Use context managers (with statement) for file operations to ensure proper cleanup. "
     "Example: with open('file.txt') as f: data = f.read()"),
    ("Prefer specific exception handling over bare except. "
     "Use: except ValueError as e instead of: except:"),
    ("Use f-strings for string formatting in Python 3.6+. "
     "Example: f'Hello {name}' is cleaner than 'Hello %s' % name or 'Hello {}'.format(name)"),
    ("Follow PEP8 naming conventions: snake_case for variables/functions, "
     "PascalCase for classes, UPPER_CASE for constants."),
    ("Extract repeated code into functions to follow the DRY principle (Don't Repeat Yourself)."),
    ("Use type hints to improve code readability and enable static analysis. "
     "Example: def greet(name: str) -> str:"),
    ("Cyclomatic complexity above 10 is a warning sign — split complex functions into smaller ones."),
    ("Use enumerate() instead of range(len()) when you need both index and value in a loop."),
    ("Prefer pathlib.Path over os.path for file path manipulation in Python 3.4+."),
    ("Use dataclasses or NamedTuple instead of plain dicts for structured data."),
    ("Write unit tests for each function, especially edge cases: empty input, None, large values."),
    ("Use pytest fixtures and parametrize to avoid test code duplication."),
    ("Avoid global variables — pass data through function arguments and return values."),
]


class DocSearchTool(BaseTool):
    name: str = "doc_search"
    description: str = (
        "Searches Python best-practices documentation for relevant guidelines. "
        "Input: a question or topic (e.g. 'how to handle exceptions', 'list vs loop'). "
        "Output: relevant documentation snippets."
    )
    _vectorstore: object = None

    def _get_vectorstore(self):
        if self._vectorstore is not None:
            return self._vectorstore

        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        embeddings = OllamaEmbeddings(
            model="nomic-embed-text",
            base_url=base_url,
        )
        docs = [Document(page_content=text) for text in KNOWLEDGE_BASE]
        self._vectorstore = Chroma.from_documents(
            docs,
            embedding=embeddings,
            collection_name="python_best_practices",
        )
        return self._vectorstore

    def _run(self, query: str) -> str:
        try:
            store = self._get_vectorstore()
            results = store.similarity_search(query, k=3)
            snippets = [f"- {doc.page_content}" for doc in results]
            return "\n".join(snippets)
        except Exception as e:
            # Fallback: keyword search in knowledge base
            query_lower = query.lower()
            matched = [
                f"- {text}"
                for text in KNOWLEDGE_BASE
                if any(word in text.lower() for word in query_lower.split())
            ]
            return "\n".join(matched[:3]) if matched else "No relevant documentation found."

    async def _arun(self, query: str) -> str:
        return self._run(query)
