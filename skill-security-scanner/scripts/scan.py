#!/usr/bin/env python3
"""
Skill Security Scanner - CLI Entry Point

Usage:
    python3 scan.py --path /opt/skills/some-skill
    python3 scan.py --path /opt/skills --all
    python3 scan.py --path /opt/skills/some-skill --format json
    python3 scan.py --path /opt/skills/some-skill --format sarif --output results.sarif
    python3 scan.py --path /opt/skills/some-skill --severity high
    python3 scan.py --list-rules
"""

import argparse
import json
import sys
import os

# Allow running from any directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from copilot.skill_scanner import SkillSecurityScanner, RULES, SEVERITY_ICONS


def main():
    parser = argparse.ArgumentParser(
        description="Scan AI agent skills for security vulnerabilities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--path", help="Path to skill directory or file to scan")
    parser.add_argument("--all", action="store_true", help="Scan all skill subdirectories under --path")
    parser.add_argument("--severity", default="low",
                        choices=["critical", "high", "medium", "low", "info"],
                        help="Minimum severity level to report (default: low)")
    parser.add_argument("--format", default="text", choices=["text", "json", "sarif"],
                        help="Output format (default: text)")
    parser.add_argument("--output", help="Save output to file instead of stdout")
    parser.add_argument("--config", help="Path to scanner_config.json")
    parser.add_argument("--list-rules", action="store_true", help="List all available detection rules")
    parser.add_argument("--exit-zero", action="store_true",
                        help="Always exit with code 0 (don't fail CI on findings)")
    args = parser.parse_args()

    scanner = SkillSecurityScanner(config_path=args.config)

    # ── List rules ─────────────────────────────────────────────────────────────
    if args.list_rules:
        print("\n📋 Available Detection Rules\n")
        print(f"{'ID':<35} {'Severity':<10} Title")
        print("─" * 85)
        for rule in RULES:
            icon = SEVERITY_ICONS.get(rule["severity"], rule["severity"])
            print(f"{rule['id']:<35} {icon:<18} {rule['title']}")
        print()
        return

    if not args.path:
        parser.error("--path is required (or --list-rules)")

    # ── Scan ───────────────────────────────────────────────────────────────────
    exit_code = 0

    if args.all:
        all_results = scanner.scan_directory(args.path, min_severity=args.severity)
        overall_pass = all(r["passed"] for r in all_results)
        if not overall_pass:
            exit_code = 1

        if args.format == "text":
            output = ""
            for result in all_results:
                import io
                from contextlib import redirect_stdout
                buf = io.StringIO()
                with redirect_stdout(buf):
                    scanner.print_report(result, min_severity=args.severity)
                output += buf.getvalue()
            summary = f"\n{'=' * 70}\n📊 Overall: {sum(1 for r in all_results if r['passed'])}/{len(all_results)} skills passed\n"
            output += summary
        elif args.format == "json":
            output = json.dumps(all_results, indent=2)
        else:
            output = json.dumps({"scans": [scanner.to_sarif(r) for r in all_results]}, indent=2)

    else:
        result = scanner.scan_skill(args.path)
        if "error" in result:
            print(f"❌ {result['error']}", file=sys.stderr)
            sys.exit(1)

        if not result["passed"]:
            exit_code = 1

        # Filter by severity for reporting
        from copilot.skill_scanner import SEVERITY_ORDER
        threshold = SEVERITY_ORDER.get(args.severity, 0)
        result["findings"] = [f for f in result["findings"]
                               if SEVERITY_ORDER.get(f["severity"], 0) >= threshold]

        if args.format == "text":
            import io
            from contextlib import redirect_stdout
            buf = io.StringIO()
            with redirect_stdout(buf):
                scanner.print_report(result, min_severity=args.severity)
            output = buf.getvalue()
        elif args.format == "json":
            output = json.dumps(result, indent=2)
        else:  # sarif
            output = json.dumps(scanner.to_sarif(result), indent=2)

    # ── Output ─────────────────────────────────────────────────────────────────
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"✅ Results saved to: {args.output}")
    else:
        print(output)

    if not args.exit_zero:
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
