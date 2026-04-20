"""
Orchestrator: coordinates the full multi-agent pipeline.
Pipeline: Analyzer → Critic → Refactorer → Tester → Report
"""
import json
import time
from dataclasses import dataclass, field
from agents.analyzer import AnalyzerAgent
from agents.critic import CriticAgent
from agents.refactorer import RefactorerAgent
from agents.tester import TesterAgent


@dataclass
class PipelineResult:
    original_code: str
    analysis: dict = field(default_factory=dict)
    critique: dict = field(default_factory=dict)
    refactoring: dict = field(default_factory=dict)
    testing: dict = field(default_factory=dict)
    timings: dict = field(default_factory=dict)
    success: bool = False
    error: str = ""

    def to_report(self) -> str:
        """Format pipeline result as a human-readable report."""
        lines = []
        lines.append("=" * 60)
        lines.append("ОТЧЁТ О ПРОВЕРКЕ И РЕФАКТОРИНГЕ КОДА")
        lines.append("=" * 60)

        if self.error:
            lines.append(f"\nОШИБКА: {self.error}")
            return "\n".join(lines)

        # Analysis section
        lines.append("\n## АНАЛИЗ")
        lines.append(self.analysis.get("analysis", "Н/Д"))

        # Critique section
        lines.append("\n## КРИТИКА И ПРИОРИТЕТЫ")
        lines.append(self.critique.get("critique", "Н/Д"))

        # Refactoring section
        lines.append("\n## РЕФАКТОРИРОВАННЫЙ КОД")
        lines.append("```python")
        lines.append(self.refactoring.get("refactored_code", "Н/Д"))
        lines.append("```")
        lines.append("\n### Внесённые изменения")
        lines.append(self.refactoring.get("changes_made", "Н/Д"))

        # Testing section
        lines.append("\n## РЕЗУЛЬТАТЫ ТЕСТОВ")
        t = self.testing
        passed = t.get("tests_passed", 0)
        failed = t.get("tests_failed", 0)
        lines.append(f"Тестов пройдено: {passed} | Тестов провалено: {failed}")
        if t.get("test_errors"):
            lines.append("Провалившиеся тесты:")
            for err in t["test_errors"]:
                lines.append(f"  {err}")
        lines.append("\nСгенерированный код тестов:")
        lines.append("```python")
        lines.append(t.get("test_code", "Н/Д"))
        lines.append("```")

        # Timings
        lines.append("\n## ПРОИЗВОДИТЕЛЬНОСТЬ")
        for agent, duration in self.timings.items():
            lines.append(f"  {agent}: {duration:.1f}с")
        total = sum(self.timings.values())
        lines.append(f"  Итого: {total:.1f}с")

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)


class Orchestrator:
    def __init__(self):
        self.analyzer = AnalyzerAgent()
        self.critic = CriticAgent()
        self.refactorer = RefactorerAgent()
        self.tester = TesterAgent()

    def run(self, code: str, skip_tests: bool = False) -> PipelineResult:
        """
        Run the full multi-agent pipeline on the provided code.

        Args:
            code: Python source code to analyze and refactor
            skip_tests: if True, skip the testing step (faster)

        Returns:
            PipelineResult with all agent outputs
        """
        result = PipelineResult(original_code=code)

        try:
            # Step 1: Analyzer
            print("\n[Оркестратор] Шаг 1/4: Анализ кода...")
            t0 = time.time()
            result.analysis = self.analyzer.run(code)
            result.timings["analyzer"] = time.time() - t0

            # Step 2: Critic
            print("\n[Оркестратор] Шаг 2/4: Критика анализа...")
            t0 = time.time()
            result.critique = self.critic.run(
                code=code,
                analysis=result.analysis["analysis"],
            )
            result.timings["critic"] = time.time() - t0

            # Step 3: Refactorer
            print("\n[Оркестратор] Шаг 3/4: Рефакторинг кода...")
            t0 = time.time()
            result.refactoring = self.refactorer.run(
                code=code,
                critique=result.critique["critique"],
            )
            result.timings["refactorer"] = time.time() - t0

            # Step 4: Tester
            if not skip_tests:
                print("\n[Оркестратор] Шаг 4/4: Генерация и запуск тестов...")
                t0 = time.time()
                result.testing = self.tester.run(
                    original_code=code,
                    refactored_code=result.refactoring["refactored_code"],
                )
                result.timings["tester"] = time.time() - t0
            else:
                print("\n[Оркестратор] Шаг 4/4: Пропуск тестов (skip_tests=True)")
                result.testing = {"tests_passed": 0, "tests_failed": 0, "test_code": ""}

            result.success = True
            print("\n[Оркестратор] Пайплайн успешно завершён!")

        except Exception as e:
            result.error = str(e)
            result.success = False
            print(f"\n[Оркестратор] Пайплайн завершился с ошибкой: {e}")

        return result
