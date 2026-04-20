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
        lines.append("CODE REVIEW & REFACTORING REPORT")
        lines.append("=" * 60)

        if self.error:
            lines.append(f"\nERROR: {self.error}")
            return "\n".join(lines)

        # Analysis section
        lines.append("\n## ANALYSIS")
        lines.append(self.analysis.get("analysis", "N/A"))

        # Critique section
        lines.append("\n## CRITIQUE & PRIORITIES")
        lines.append(self.critique.get("critique", "N/A"))

        # Refactoring section
        lines.append("\n## REFACTORED CODE")
        lines.append("```python")
        lines.append(self.refactoring.get("refactored_code", "N/A"))
        lines.append("```")
        lines.append("\n### Changes Made")
        lines.append(self.refactoring.get("changes_made", "N/A"))

        # Testing section
        lines.append("\n## TEST RESULTS")
        t = self.testing
        passed = t.get("tests_passed", 0)
        failed = t.get("tests_failed", 0)
        lines.append(f"Tests passed: {passed} | Tests failed: {failed}")
        if t.get("test_errors"):
            lines.append("Failed tests:")
            for err in t["test_errors"]:
                lines.append(f"  {err}")
        lines.append("\nGenerated test code:")
        lines.append("```python")
        lines.append(t.get("test_code", "N/A"))
        lines.append("```")

        # Timings
        lines.append("\n## PERFORMANCE")
        for agent, duration in self.timings.items():
            lines.append(f"  {agent}: {duration:.1f}s")
        total = sum(self.timings.values())
        lines.append(f"  Total: {total:.1f}s")

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
            print("\n[Orchestrator] Step 1/4: Analyzing code...")
            t0 = time.time()
            result.analysis = self.analyzer.run(code)
            result.timings["analyzer"] = time.time() - t0

            # Step 2: Critic
            print("\n[Orchestrator] Step 2/4: Critiquing analysis...")
            t0 = time.time()
            result.critique = self.critic.run(
                code=code,
                analysis=result.analysis["analysis"],
            )
            result.timings["critic"] = time.time() - t0

            # Step 3: Refactorer
            print("\n[Orchestrator] Step 3/4: Refactoring code...")
            t0 = time.time()
            result.refactoring = self.refactorer.run(
                code=code,
                critique=result.critique["critique"],
            )
            result.timings["refactorer"] = time.time() - t0

            # Step 4: Tester
            if not skip_tests:
                print("\n[Orchestrator] Step 4/4: Generating and running tests...")
                t0 = time.time()
                result.testing = self.tester.run(
                    original_code=code,
                    refactored_code=result.refactoring["refactored_code"],
                )
                result.timings["tester"] = time.time() - t0
            else:
                print("\n[Orchestrator] Step 4/4: Skipping tests (skip_tests=True)")
                result.testing = {"tests_passed": 0, "tests_failed": 0, "test_code": ""}

            result.success = True
            print("\n[Orchestrator] Pipeline completed successfully!")

        except Exception as e:
            result.error = str(e)
            result.success = False
            print(f"\n[Orchestrator] Pipeline failed: {e}")

        return result
