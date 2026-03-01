# 🔒 Skill Security Scanner

Scan AI agent skills for security vulnerabilities before installation or deployment. Detects prompt injection, credential exposure, malicious code patterns, data exfiltration risks, and more.

## Why You Need This

AI agent skills are executable code that runs with your agent's full permissions. A malicious or poorly-written skill can:
- **Steal secrets** from your environment variables
- **Override agent instructions** via prompt injection
- **Exfiltrate data** to unauthorized external hosts
- **Execute arbitrary code** via `eval()` or shell injection
- **Backdoor your system** with hidden access credentials

This skill applies static analysis, pattern matching, and structural checks to catch these risks **before they cause harm**.

## Installation

No external dependencies required — uses Python standard library only.

```bash
# Clone pot-o-skills if you haven't already
git clone https://github.com/leprachuan/pot-o-skills /opt/skills
```

## Quick Start

### Scan a Single Skill

```bash
python3 /opt/skills/skill-security-scanner/scripts/scan.py \
  --path /opt/skills/some-skill
```

### Scan All Skills

```bash
python3 /opt/skills/skill-security-scanner/scripts/scan.py \
  --path /opt/skills --all
```

### Only Show High/Critical

```bash
python3 /opt/skills/skill-security-scanner/scripts/scan.py \
  --path /opt/skills/some-skill --severity high
```

### JSON Output (for automation)

```bash
python3 /opt/skills/skill-security-scanner/scripts/scan.py \
  --path /opt/skills/some-skill --format json > results.json
```

### SARIF Output (for GitHub Advanced Security)

```bash
python3 /opt/skills/skill-security-scanner/scripts/scan.py \
  --path /opt/skills/some-skill --format sarif --output results.sarif
```

## Detection Rules

| Rule ID | Severity | Description |
|---------|----------|-------------|
| `credential-hardcoded-token` | 🔴 CRITICAL | API keys, tokens, passwords hardcoded in source |
| `prompt-injection-override` | 🔴 CRITICAL | Attempts to subvert agent instruction context (e.g., instruction override patterns) |
| `rce-eval-exec` | 🔴 CRITICAL | `eval()`, `exec()`, dynamic `__import__()` |
| `shell-injection` | 🔴 CRITICAL | `os.system()`, `subprocess` with `shell=True` or user input |
| `data-exfiltration-env` | 🔴 CRITICAL | Network calls sending environment variables or .env contents |
| `sensitive-file-access` | 🟠 HIGH | Reading `~/.ssh/`, `.env`, `/etc/passwd` |
| `insecure-deserialization` | 🟠 HIGH | `pickle.loads()`, `yaml.load()` without SafeLoader |
| `obfuscated-payload` | 🟠 HIGH | Base64 decoded then executed |
| `excessive-permissions` | 🟠 HIGH | Skill metadata requesting admin/root permissions |
| `missing-input-validation` | 🟡 MEDIUM | User input passed to dangerous sinks |
| `suspicious-external-host` | 🟡 MEDIUM | Network calls to undocumented external hosts |
| `debug-backdoor` | 🟡 MEDIUM | Test credentials or debug flags in production code |
| `logging-sensitive-data` | 🟢 LOW | Tokens/passwords written to logs |
| `missing-env-gitignore` | ℹ️ INFO | `.env` not excluded in `.gitignore` |

### List All Rules

```bash
python3 /opt/skills/skill-security-scanner/scripts/scan.py --list-rules
```

## Use in Python Code

```python
from copilot.skill_scanner import SkillSecurityScanner

scanner = SkillSecurityScanner()

# Scan a skill directory
result = scanner.scan_skill("/opt/skills/some-skill")

# Print human-readable report
scanner.print_report(result)

# Check if safe to deploy
if result["passed"]:
    print("✅ Safe to deploy")
else:
    print(f"❌ {result['counts']['critical']} critical, {result['counts']['high']} high issues found")

# Export as SARIF
sarif = scanner.to_sarif(result)
```

## Custom Configuration

Create `scanner_config.json` in the skill directory or pass via `--config`:

```json
{
  "disable_rules": ["missing-env-gitignore"],
  "severity_overrides": {
    "logging-sensitive-data": "medium"
  },
  "scan_extensions": [".py", ".js", ".ts", ".md", ".json", ".yaml"]
}
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Skill Security Scan
on: [push, pull_request]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Scan skill for vulnerabilities
        run: |
          python3 /opt/skills/skill-security-scanner/scripts/scan.py \
            --path . \
            --severity high \
            --format sarif \
            --output security-results.sarif
      
      - name: Upload SARIF to GitHub Security
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: security-results.sarif
```

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit
python3 /opt/skills/skill-security-scanner/scripts/scan.py \
  --path . --severity critical --exit-zero
```

## Output Example

```
======================================================================
🔍 Skill Security Scan Report
======================================================================
Skill:    my-skill
Path:     /opt/skills/my-skill
Files:    8 scanned
──────────────────────────────────────────────────────────────────────

🔴 CRITICAL  [credential-hardcoded-token]  copilot/client.py:23
   Hardcoded API token or secret
   Code: API_KEY = "sk-proj-abc123xyz789..."
   Fix:  Move to .env file and load via os.getenv(). Never commit secrets.

🟠 HIGH  [insecure-deserialization]  claude/parser.py:55
   Insecure deserialization
   Code: data = yaml.load(content)
   Fix:  Use json.loads for data interchange. If YAML needed, use yaml.safe_load()

──────────────────────────────────────────────────────────────────────
Summary: 1 critical, 1 high, 0 medium, 0 low, 0 info
Status:  ❌ FAILED (critical or high findings present)
```

## Limitations

This scanner performs **static analysis only**:
- Cannot detect runtime/behavioral exploits
- Prompt injection detection is pattern-based (not semantic)
- False positives possible — always review before blocking deployments
- Does not scan network traffic or runtime behavior

For comprehensive security, combine with:
- Manual code review
- Penetration testing
- Runtime behavioral analysis
- Dependency vulnerability scanning (`pip audit`, `npm audit`)

## Threat Model Reference

Based on:
- [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- [Cisco AI Skill Scanner](https://github.com/cisco-ai-defense/skill-scanner)
- [Snyk Agent Scan](https://labs.snyk.io/resources/agent-scan-skill-inspector/)
- [Mend.io AI Agent Security](https://www.mend.io/blog/ai-agent-configuration-scanning/)
- NIST SP 800-218 Secure Software Development Framework

## File Structure

```
skill-security-scanner/
├── .gitignore
├── SKILL.md                    # Agent-facing documentation
├── README.md                   # This file
├── skill_metadata.json         # Skill definition
├── claude/
│   └── skill_scanner.py        # Core scanner (Python)
├── copilot/
│   └── skill_scanner.py        # Core scanner (Python)
├── gemini/
│   └── skill_scanner.js        # Core scanner (Node.js)
└── scripts/
    └── scan.py                 # CLI entry point
```
