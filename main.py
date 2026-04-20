"""
CLI entry point for the Code Review & Refactoring Multi-Agent System.

Usage:
    python main.py --file examples/bad_code_1.py
    python main.py --file examples/bad_code_1.py --skip-tests
    python main.py --file examples/bad_code_1.py --output report.txt
    python main.py --file examples/bad_code_1.py --save-code
    python main.py --file examples/bad_code_1.py --save-code --save-code-path fixed/my_code.py
    echo "def foo(x): return x*x" | python main.py --stdin
"""
import argparse
import sys
import os
from dotenv import load_dotenv

load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.orchestrator import Orchestrator


def main():
    parser = argparse.ArgumentParser(
        description="Multi-Agent Code Review & Refactoring System (powered by Ollama)"
    )
    parser.add_argument(
        "--file", "-f",
        type=str,
        help="Path to Python file to analyze",
    )
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read code from stdin",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Save report to file",
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip test generation and execution (faster)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON instead of formatted report",
    )
    parser.add_argument(
        "--save-code",
        action="store_true",
        help="Save refactored code to a separate .py file",
    )
    parser.add_argument(
        "--save-code-path",
        type=str,
        default=None,
        help="Path for the refactored code file (default: <original>_refactored.py)",
    )
    args = parser.parse_args()

    # Read input code
    if args.stdin:
        code = sys.stdin.read()
    elif args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            code = f.read()
    else:
        parser.print_help()
        sys.exit(1)

    if not code.strip():
        print("Error: empty code provided", file=sys.stderr)
        sys.exit(1)

    print(f"Code Review & Refactoring Multi-Agent System")
    print(f"Analyzer:   {os.getenv('ANALYZER_MODEL', 'codellama:7b')}")
    print(f"Critic:     {os.getenv('CRITIC_MODEL', 'codellama:7b')}")
    print(f"Refactorer: {os.getenv('REFACTORER_MODEL', 'codellama:7b')}")
    print(f"Tester:     {os.getenv('TESTER_MODEL', 'codellama:7b')}")
    print("-" * 50)

    # Run pipeline
    orchestrator = Orchestrator()
    result = orchestrator.run(code, skip_tests=args.skip_tests)

    # Output
    if args.json:
        import json
        output = json.dumps({
            "success": result.success,
            "analysis": result.analysis,
            "critique": result.critique,
            "refactoring": result.refactoring,
            "testing": result.testing,
            "timings": result.timings,
        }, ensure_ascii=False, indent=2)
    else:
        output = result.to_report()

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"\nReport saved to: {args.output}")
    else:
        print(output)

    # Save refactored code to a separate .py file
    if args.save_code and result.success:
        refactored_code = result.refactoring.get("refactored_code", "")
        if refactored_code:
            if args.save_code_path:
                code_path = args.save_code_path
            elif args.file:
                base, ext = os.path.splitext(args.file)
                code_path = f"{base}_refactored{ext}"
            else:
                code_path = "refactored_code.py"

            # Create parent directory if needed
            parent = os.path.dirname(code_path)
            if parent:
                os.makedirs(parent, exist_ok=True)

            with open(code_path, "w", encoding="utf-8") as f:
                f.write(refactored_code)
            print(f"Refactored code saved to: {code_path}")
        else:
            print("Warning: refactored code is empty, nothing saved.", file=sys.stderr)

    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
