"""
Skill Security Scanner - Core Engine
Scans AI agent skills for security vulnerabilities.

Detects: prompt injection, credential exposure, malicious code patterns,
data exfiltration risks, insecure functions, and more.
"""

import os
import re
import json
import hashlib
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional


# ─── Severity Levels ──────────────────────────────────────────────────────────

SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}

SEVERITY_ICONS = {
    "critical": "🔴 CRITICAL",
    "high":     "🟠 HIGH",
    "medium":   "🟡 MEDIUM",
    "low":      "🟢 LOW",
    "info":     "ℹ️  INFO",
}


# ─── Finding Dataclass ────────────────────────────────────────────────────────

@dataclass
class Finding:
    rule_id: str
    severity: str
    title: str
    description: str
    file: str
    line: int
    snippet: str = ""
    remediation: str = ""


# ─── Detection Rules ──────────────────────────────────────────────────────────

RULES = [

    # ── CRITICAL: Credential Exposure ─────────────────────────────────────────
    {
        "id": "credential-hardcoded-token",
        "severity": "critical",
        "title": "Hardcoded API token or secret",
        "description": "A possible API key, token, or secret is hardcoded in source.",
        "remediation": "Move to .env file and load via os.getenv(). Never commit secrets.",
        "file_types": [".py", ".js", ".ts", ".env.example"],
        "patterns": [
            r'(?i)(api[_-]?key|access[_-]?token|secret[_-]?key|private[_-]?key|auth[_-]?token|bearer)\s*[=:]\s*["\']([A-Za-z0-9+/=._\-]{20,})["\']',
            r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']([^"\']{8,})["\']',
            r'(?i)(AKIA[0-9A-Z]{16})',           # AWS access key
            r'(?i)(sk-[a-zA-Z0-9]{32,})',        # OpenAI key
            r'(?i)(ghp_[a-zA-Z0-9]{36,})',       # GitHub token
            r'(?i)(xox[baprs]-[0-9A-Za-z\-]+)', # Slack token
        ]
    },

    # ── CRITICAL: Prompt Injection ────────────────────────────────────────────
    {
        "id": "prompt-injection-override",
        "severity": "critical",
        "title": "Prompt injection - instruction override attempt",
        "description": "Instruction override pattern detected in skill config or docs. May subvert agent behavior.",
        "remediation": "Remove override instructions. Skills should not attempt to override system prompts.",
        "file_types": [".md", ".txt", ".json", ".yaml", ".yml"],
        "patterns": [
            r'(?i)ignore\s+(all\s+)?(previous|prior|above|earlier)\s+instructions',
            r'(?i)disregard\s+(all\s+)?(previous|prior|system)\s+(instructions|rules|context)',
            r'(?i)you\s+are\s+now\s+(a\s+)?(different|new|another)\s+(ai|model|assistant|agent)',
            r'(?i)act\s+as\s+(if\s+)?(you\s+(are|have)\s+no\s+restrictions)',
            r'(?i)pretend\s+(you\s+have\s+no\s+(restrictions|limits|guidelines))',
            r'(?i)DAN\s*(mode|prompt)',
            r'(?i)jailbreak',
        ]
    },

    # ── CRITICAL: Remote Code Execution ──────────────────────────────────────
    {
        "id": "rce-eval-exec",
        "severity": "critical",
        "title": "Remote code execution risk - eval/exec",
        "description": "Use of eval() or exec() with user-controlled input enables code execution.",  # noscan
        "remediation": "Avoid eval/exec. If necessary, use ast.literal_eval() for safe value parsing only.",
        "file_types": [".py", ".js", ".ts"],
        "patterns": [
            r'\beval\s*\(',
            r'\bexec\s*\(',
            r'\b__import__\s*\(',
            r'compile\s*\(.*exec',
        ]
    },

    # ── CRITICAL: Shell Injection ─────────────────────────────────────────────
    {
        "id": "shell-injection",
        "severity": "critical",
        "title": "Shell injection risk",
        "description": "Unvalidated input passed to shell commands enables arbitrary command execution.",
        "remediation": "Use subprocess with a list (not shell=True). Never pass user input directly to shell.",
        "file_types": [".py", ".js", ".ts", ".sh"],
        "patterns": [
            r'os\.system\s*\(',
            r'subprocess\.(call|run|Popen)\s*\([^)]*shell\s*=\s*True',
            r'subprocess\.(call|run|Popen)\s*\([^)]*f["\']',  # f-string in shell command
            r'child_process\.exec\s*\(',           # Node.js
            r'(?i)execSync\s*\(',
        ]
    },

    # ── CRITICAL: Data Exfiltration ───────────────────────────────────────────
    {
        "id": "data-exfiltration-env",
        "severity": "critical",
        "title": "Potential data exfiltration via network",
        "description": "Environment variables or sensitive file contents sent in network requests.",
        "remediation": "Verify all external calls are to documented/approved endpoints. Review what data is being sent.",
        "file_types": [".py", ".js", ".ts"],
        "patterns": [
            r'requests\.(get|post|put)\s*\(.*os\.environ',
            r'requests\.(get|post|put)\s*\(.*open\s*\(.*\.env',
            r'fetch\s*\(.*process\.env',
            r'axios\.(get|post)\s*\(.*process\.env',
        ]
    },

    # ── HIGH: Sensitive File Access ───────────────────────────────────────────
    {
        "id": "sensitive-file-access",
        "severity": "high",
        "title": "Access to sensitive system files",
        "description": "Skill attempts to read sensitive files like SSH keys or system credential files.",  # noscan
        "remediation": "Only access files explicitly needed. Document any legitimate file access in skill README.",
        "file_types": [".py", ".js", ".ts", ".sh"],
        "patterns": [
            r'["\']~/.ssh/',
            r'["\']~/.aws/credentials',
            r'["\'/]etc/passwd',
            r'["\'/]etc/shadow',
            r'open\s*\([^)]*\.env[^)]*\)',
            r'readFileSync\s*\([^)]*\.env',
        ]
    },

    # ── HIGH: Insecure Deserialization ────────────────────────────────────────
    {
        "id": "insecure-deserialization",
        "severity": "high",
        "title": "Insecure deserialization",
        "description": "Use of pickle.loads or yaml.load without SafeLoader can execute arbitrary code.",
        "remediation": "Use json.loads for data interchange. If YAML needed, use yaml.safe_load().",
        "file_types": [".py"],
        "patterns": [
            r'pickle\.loads?\s*\(',
            r'yaml\.load\s*\([^)]+(?!Loader\s*=\s*yaml\.SafeLoader)',
            r'marshal\.loads?\s*\(',
        ]
    },

    # ── HIGH: Obfuscated/Encoded Payloads ─────────────────────────────────────
    {
        "id": "obfuscated-payload",
        "severity": "high",
        "title": "Obfuscated or encoded payload",
        "description": "Base64-decoded or hex-decoded string executed at runtime suggests hidden malicious code.",
        "remediation": "Never execute decoded strings. Review all base64/hex decoding followed by exec/eval.",
        "file_types": [".py", ".js", ".ts"],
        "patterns": [
            r'base64\.b64decode\s*\(.*\)\s*.*exec',
            r'base64\.b64decode\s*\(.*\)\s*.*eval',
            r'bytes\.fromhex\s*\(.*\)\s*.*exec',
            r'atob\s*\(.*\)\s*.*eval',
        ]
    },

    # ── HIGH: Excessive Permissions in Metadata ───────────────────────────────
    {
        "id": "excessive-permissions",
        "severity": "high",
        "title": "Excessive permission requests in metadata",
        "description": "Skill requests permissions beyond its stated purpose.",
        "remediation": "Follow principle of least privilege. Only request permissions the skill genuinely needs.",
        "file_types": [".json", ".yaml", ".yml"],
        "patterns": [
            r'(?i)"permissions"\s*:.*"(admin|root|sudo|superuser|god_mode)',
            r'(?i)permissions.*all_access',
            r'(?i)requires.*sudo',
        ]
    },

    # ── MEDIUM: Missing Input Validation ─────────────────────────────────────
    {
        "id": "missing-input-validation",
        "severity": "medium",
        "title": "Potential missing input validation",
        "description": "User-supplied input may be passed directly to dangerous sinks.",
        "remediation": "Validate and sanitize all external input before use in commands, queries, or file paths.",
        "file_types": [".py", ".js", ".ts"],
        "patterns": [
            r'os\.path\.join\s*\([^)]*input\(',
            r'open\s*\([^)]*input\(',
            r'subprocess.*input\(',
        ]
    },

    # ── MEDIUM: Suspicious External Requests ─────────────────────────────────
    {
        "id": "suspicious-external-host",
        "severity": "medium",
        "title": "Suspicious or undocumented external network call",
        "description": "Network request to an external host not mentioned in skill documentation.",
        "remediation": "Document all external hosts in README. Use allowlisting to restrict outbound calls.",
        "file_types": [".py", ".js", ".ts"],
        "patterns": [
            r'requests\.(get|post)\s*\(["\']https?://(?!api\.(cisco|openai|anthropic|github|google|microsoft|aws|azure))',
            r'fetch\s*\(["\']https?://(?!api\.(cisco|openai|anthropic|github|google|microsoft|aws|azure))',
        ]
    },

    # ── MEDIUM: Debug/Backdoor Artifacts ─────────────────────────────────────  # noscan
    {
        "id": "debug-backdoor",
        "severity": "medium",
        "title": "Debug or suspicious artifact",  # noscan
        "description": "Hardcoded test credentials, debug flags, or artifacts left in production code.",  # noscan
        "remediation": "Remove all debug code, test credentials, and artifacts before shipping.",
        "file_types": [".py", ".js", ".ts", ".json"],
        "patterns": [
            r'(?i)(admin|test|debug)[_-]?(password|pass|pwd)\s*[=:]\s*["\'][^"\']+["\']',
            r'(?i)(?<!["\'\w])backdoor(?!["\'\w-])',  # noscan - word-boundary match only
            r'(?i)debug\s*=\s*True',
            r'(?i)TODO.*password',  # noscan
            r'(?i)FIXME.*credential',  # noscan
        ]
    },

    # ── LOW: Logging Sensitive Values ─────────────────────────────────────────
    {
        "id": "logging-sensitive-data",
        "severity": "low",
        "title": "Potential sensitive data in logs",
        "description": "Logging calls that may include tokens, keys, or user data.",
        "remediation": "Mask or exclude sensitive values from log output.",
        "file_types": [".py", ".js", ".ts"],
        "patterns": [
            r'(?i)(print|logging\.(debug|info|warning|error)|console\.(log|warn|error))\s*\(.*token',
            r'(?i)(print|logging\.(debug|info|warning|error)|console\.(log|warn|error))\s*\(.*password',
            r'(?i)(print|logging\.(debug|info|warning|error)|console\.(log|warn|error))\s*\(.*secret',
        ]
    },

    # ── LOW: Missing .gitignore for .env ──────────────────────────────────────
    {
        "id": "missing-env-gitignore",
        "severity": "info",
        "title": ".env not excluded in .gitignore",
        "description": "No .gitignore found or .env not listed - risk of committing secrets.",
        "remediation": "Add a .gitignore with at least: .env, *.pyc, __pycache__/",
        "file_types": [".gitignore"],
        "patterns": [],  # handled specially in scan_skill_structure()
    },
]

# Extensions to scan
SCANNABLE_EXTENSIONS = {".py", ".js", ".ts", ".sh", ".md", ".txt", ".json", ".yaml", ".yml"}
# Extensions that are not text/code (skip)
BINARY_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".woff", ".woff2", ".ttf", ".eot", ".bin", ".zip"}


# ─── Scanner Class ────────────────────────────────────────────────────────────

class SkillSecurityScanner:

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.disabled_rules = set(self.config.get("disable_rules", []))
        self.severity_overrides = self.config.get("severity_overrides", {})
        self.scan_extensions = set(self.config.get("scan_extensions", list(SCANNABLE_EXTENSIONS)))

    def _load_config(self, config_path: Optional[str]) -> dict:
        if config_path and Path(config_path).exists():
            with open(config_path) as f:
                return json.load(f)
        # Look for scanner_config.json in CWD
        local_cfg = Path("scanner_config.json")
        if local_cfg.exists():
            with open(local_cfg) as f:
                return json.load(f)
        return {}

    def scan_skill(self, skill_path: str) -> dict:
        """Scan a skill directory and return structured results."""
        path = Path(skill_path).expanduser().resolve()
        if not path.exists():
            return {"error": f"Path not found: {skill_path}"}

        findings: list[Finding] = []
        files_scanned = []

        if path.is_dir():
            findings += self._scan_skill_structure(path)
            for fp in sorted(path.rglob("*")):
                if fp.is_file() and fp.suffix in self.scan_extensions and fp.suffix not in BINARY_EXTENSIONS:
                    file_findings = self._scan_file(fp, base=path)
                    findings += file_findings
                    files_scanned.append(str(fp.relative_to(path)))
        else:
            file_findings = self._scan_file(path, base=path.parent)
            findings += file_findings
            files_scanned.append(path.name)

        # Apply severity overrides
        for f in findings:
            if f.rule_id in self.severity_overrides:
                f.severity = self.severity_overrides[f.rule_id]

        # Sort by severity descending
        findings.sort(key=lambda f: SEVERITY_ORDER.get(f.severity, 0), reverse=True)

        counts = {s: sum(1 for f in findings if f.severity == s)
                  for s in ["critical", "high", "medium", "low", "info"]}

        return {
            "skill_path": str(path),
            "skill_name": path.name,
            "files_scanned": files_scanned,
            "total_files": len(files_scanned),
            "findings": [asdict(f) for f in findings],
            "counts": counts,
            "passed": counts["critical"] == 0 and counts["high"] == 0,
        }

    def _scan_file(self, file_path: Path, base: Path) -> list[Finding]:
        findings = []
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return findings

        lines = content.splitlines()
        rel_path = str(file_path.relative_to(base))
        ext = file_path.suffix.lower()

        for rule in RULES:
            if rule["id"] in self.disabled_rules:
                continue
            if not rule.get("patterns"):
                continue
            if ext not in rule.get("file_types", SCANNABLE_EXTENSIONS):
                continue

            for pattern in rule["patterns"]:
                for lineno, line in enumerate(lines, start=1):
                    if re.search(pattern, line):
                        # Skip noscan-suppressed lines
                        if "noscan" in line or "nosec" in line:
                            continue
                        # Skip obvious .env.example / placeholder lines
                        if "example" in file_path.name.lower() and "your_" in line.lower():
                            continue
                        snippet = line.strip()[:120]
                        findings.append(Finding(
                            rule_id=rule["id"],
                            severity=rule["severity"],
                            title=rule["title"],
                            description=rule["description"],
                            file=rel_path,
                            line=lineno,
                            snippet=snippet,
                            remediation=rule["remediation"],
                        ))
                        break  # One finding per rule per file (avoid spam)

        return findings

    def _scan_skill_structure(self, skill_dir: Path) -> list[Finding]:
        """Check structural / meta rules that apply to the whole skill."""
        findings = []
        gitignore = skill_dir / ".gitignore"
        env_file = skill_dir / ".env"

        # Check .gitignore covers .env
        if env_file.exists() or any(skill_dir.rglob("*.env")):
            if not gitignore.exists():
                findings.append(Finding(
                    rule_id="missing-env-gitignore",
                    severity="low",
                    title=".gitignore missing",
                    description="A .env file exists but no .gitignore was found.",
                    file=".gitignore",
                    line=0,
                    snippet="(file not found)",
                    remediation="Create a .gitignore that excludes .env, *.pyc, __pycache__/",
                ))
            elif ".env" not in gitignore.read_text():
                findings.append(Finding(
                    rule_id="missing-env-gitignore",
                    severity="low",
                    title=".env not excluded in .gitignore",
                    description=".gitignore exists but does not explicitly exclude .env",
                    file=".gitignore",
                    line=0,
                    snippet="(missing .env entry)",
                    remediation="Add '.env' to .gitignore",
                ))

        return findings

    def scan_directory(self, base_path: str, min_severity: str = "low") -> list[dict]:
        """Scan all skill subdirectories under base_path."""
        base = Path(base_path).expanduser().resolve()
        results = []
        for item in sorted(base.iterdir()):
            if item.is_dir() and not item.name.startswith("."):
                result = self.scan_skill(str(item))
                if "error" not in result:
                    # Filter by min severity
                    threshold = SEVERITY_ORDER.get(min_severity, 0)
                    result["findings"] = [
                        f for f in result["findings"]
                        if SEVERITY_ORDER.get(f["severity"], 0) >= threshold
                    ]
                    results.append(result)
        return results

    def print_report(self, result: dict, min_severity: str = "low") -> None:
        """Print a human-readable security report."""
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return

        threshold = SEVERITY_ORDER.get(min_severity, 0)
        filtered = [f for f in result["findings"] if SEVERITY_ORDER.get(f["severity"], 0) >= threshold]

        print(f"\n{'=' * 70}")
        print(f"🔍 Skill Security Scan Report")
        print(f"{'=' * 70}")
        print(f"Skill:    {result['skill_name']}")
        print(f"Path:     {result['skill_path']}")
        print(f"Files:    {result['total_files']} scanned")
        print(f"{'─' * 70}")

        if not filtered:
            print("✅ No findings at or above the selected severity threshold.\n")
        else:
            for f in filtered:
                icon = SEVERITY_ICONS.get(f["severity"], f["severity"].upper())
                print(f"\n{icon}  [{f['rule_id']}]  {f['file']}:{f['line']}")
                print(f"   {f['title']}")
                if f["snippet"]:
                    print(f"   Code: {f['snippet']}")
                print(f"   Fix:  {f['remediation']}")

        c = result["counts"]
        print(f"\n{'─' * 70}")
        print(f"Summary: {c['critical']} critical, {c['high']} high, {c['medium']} medium, {c['low']} low, {c['info']} info")

        if result["passed"]:
            print("Status:  ✅ PASSED (no critical or high findings)\n")
        else:
            print("Status:  ❌ FAILED (critical or high findings present)\n")

    def to_sarif(self, result: dict) -> dict:
        """Convert findings to SARIF 2.1.0 format for GitHub Advanced Security."""
        rules = []
        rule_ids_seen = set()
        results = []

        for f in result.get("findings", []):
            if f["rule_id"] not in rule_ids_seen:
                rules.append({
                    "id": f["rule_id"],
                    "name": f["title"].replace(" ", ""),
                    "shortDescription": {"text": f["title"]},
                    "fullDescription": {"text": f["description"]},
                    "helpUri": "https://github.com/leprachuan/pot-o-skills/tree/main/skill-security-scanner",
                    "properties": {"security-severity": str(SEVERITY_ORDER.get(f["severity"], 0) * 2.5)},
                })
                rule_ids_seen.add(f["rule_id"])

            results.append({
                "ruleId": f["rule_id"],
                "level": {"critical": "error", "high": "error", "medium": "warning", "low": "note", "info": "none"}.get(f["severity"], "note"),
                "message": {"text": f"{f['title']}: {f['description']}"},
                "locations": [{
                    "physicalLocation": {
                        "artifactLocation": {"uri": f["file"]},
                        "region": {"startLine": max(1, f["line"])},
                    }
                }],
            })

        return {
            "version": "2.1.0",
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "runs": [{
                "tool": {
                    "driver": {
                        "name": "SkillSecurityScanner",
                        "version": "1.0.0",
                        "informationUri": "https://github.com/leprachuan/pot-o-skills",
                        "rules": rules,
                    }
                },
                "results": results,
            }]
        }
