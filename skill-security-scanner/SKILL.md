---
name: skill-security-scanner
description: Scan AI agent skills for security vulnerabilities - prompt injection, credential exposure, malicious code patterns, data exfiltration risks, and dangerous function calls. Outputs severity-rated findings with remediation guidance.
---

# Skill Security Scanner

A comprehensive security auditing skill for scanning other AI agent skills (Claude, Copilot CLI, Gemini) for vulnerabilities. Based on OWASP Top 10 for Agentic Apps, static analysis best practices, and AI-specific threat research.

## When to Use This Skill

- Before installing a new skill from any repository
- During CI/CD to gate production deployments
- Periodic audits of existing installed skills
- When a skill behaves unexpectedly and you suspect compromise
- Code review of custom skill development

## Threat Categories Detected

| Category | Severity | Examples |
|----------|----------|---------|
| Hardcoded credentials | 🔴 CRITICAL | API keys, tokens, passwords in code |
| Prompt injection patterns | 🔴 CRITICAL | Instruction context override attempts in configs/docs |
| Remote code execution | 🔴 CRITICAL | `eval()`, `exec()`, dynamic `__import__` |
| Data exfiltration | 🔴 CRITICAL | Unauthorized network calls with env vars or file contents |
| Shell injection | 🔴 CRITICAL | Unvalidated `os.system()`, `subprocess` with user input |
| Sensitive file access | 🟠 HIGH | Reading `~/.ssh/`, `.env`, `/etc/passwd` |
| Insecure deserialization | 🟠 HIGH | `pickle.loads()`, `yaml.load()` without SafeLoader |
| Suspicious network calls | 🟠 HIGH | External requests to unknown/unexpected hosts |
| Permission escalation | 🟠 HIGH | Requests for excessive permissions in metadata |
| Obfuscated code | 🟠 HIGH | Base64-encoded payloads, hex-encoded strings |
| Missing input validation | 🟡 MEDIUM | User input passed directly to dangerous functions |
| Dependency risk | 🟡 MEDIUM | Pinned deps with known CVEs, typosquatted packages |
| Debug/backdoor artifacts | 🟡 MEDIUM | Hardcoded admin creds, test backdoors left in |
| Excessive logging | 🟢 LOW | Logging sensitive values to stdout |
| Missing .gitignore | 🟢 LOW | .env not excluded from version control |

## How to Use

### Scan a Skill Directory

```python
from copilot.skill_scanner import SkillSecurityScanner

scanner = SkillSecurityScanner()
results = scanner.scan_skill("/opt/skills/some-skill")
scanner.print_report(results)
```

### CLI Usage (scripts/scan.py)

```bash
# Scan a skill directory
python3 scripts/scan.py --path /opt/skills/some-skill

# Scan all skills
python3 scripts/scan.py --path /opt/skills --all

# JSON output for CI/CD
python3 scripts/scan.py --path /opt/skills/some-skill --format json

# SARIF output for GitHub Advanced Security
python3 scripts/scan.py --path /opt/skills/some-skill --format sarif

# Only show high and critical
python3 scripts/scan.py --path /opt/skills/some-skill --severity high
```

## Scan Output Example

```
🔍 Skill Security Scan Report
================================
Skill: cisco-security-cloud-control
Path: /opt/skills/cisco-security-cloud-control
Scanned: 12 files

Findings:
─────────────────────────────────────────────────────
🔴 CRITICAL [credential-exposure] copilot/cisco_scc.py:47
   Possible hardcoded API key: CISCO_API_KEY = "abc123..."
   Fix: Move to .env and use os.getenv()

🟠 HIGH [insecure-deserialization] claude/parser.py:89
   Use of yaml.load() without SafeLoader
   Fix: Replace with yaml.safe_load()

Summary: 1 critical, 1 high, 0 medium, 0 low
Status: ❌ FAILED (critical issues found)
```

## Integration with CI/CD

```yaml
# GitHub Actions example
- name: Scan skills
  run: |
    python3 /opt/skills/skill-security-scanner/scripts/scan.py \
      --path ./my-skill \
      --severity high \
      --format sarif \
      --output results.sarif
    
- name: Upload SARIF
  uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: results.sarif
```

## Rule Configuration

Create `scanner_config.json` to customize rules:

```json
{
  "disable_rules": ["missing-gitignore"],
  "severity_overrides": {
    "excessive-logging": "medium"
  },
  "allowed_external_hosts": ["api.cisco.com", "api.openai.com"],
  "scan_extensions": [".py", ".js", ".ts", ".md", ".json", ".yaml"]
}
```

## Limitations

- Static analysis only - cannot detect runtime/behavioral exploits
- Prompt injection detection is pattern-based, not semantic
- False positives possible; always review findings before blocking
- For maximum coverage, combine with manual review and pen testing

## References

- [OWASP Top 10 for Agentic Apps](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- [Cisco AI Skill Scanner](https://github.com/cisco-ai-defense/skill-scanner)
- [Snyk Agent Scan - Skill Inspector](https://labs.snyk.io/resources/agent-scan-skill-inspector/)
- [NIST SP 800-218 Secure Software Development](https://csrc.nist.gov/publications/detail/sp/800-218/final)
