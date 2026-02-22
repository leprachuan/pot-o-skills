/**
 * Skill Security Scanner - Gemini/Node.js Runtime
 * Scans AI agent skills for security vulnerabilities.
 */

const fs = require('fs');
const path = require('path');

const SEVERITY_ORDER = { critical: 4, high: 3, medium: 2, low: 1, info: 0 };

const SEVERITY_ICONS = {
  critical: '🔴 CRITICAL',
  high:     '🟠 HIGH',
  medium:   '🟡 MEDIUM',
  low:      '🟢 LOW',
  info:     'ℹ️  INFO',
};

const RULES = [
  {
    id: 'credential-hardcoded-token',
    severity: 'critical',
    title: 'Hardcoded API token or secret',
    description: 'A possible API key, token, or secret is hardcoded in source.',
    remediation: 'Move to .env file and load via process.env. Never commit secrets.',
    fileTypes: ['.py', '.js', '.ts'],
    patterns: [
      /(?:api[_-]?key|access[_-]?token|secret[_-]?key|auth[_-]?token)\s*[=:]\s*["']([A-Za-z0-9+/=._\-]{20,})["']/i,
      /(?:password|passwd|pwd)\s*[=:]\s*["']([^"']{8,})["']/i,
      /AKIA[0-9A-Z]{16}/,
      /sk-[a-zA-Z0-9]{32,}/,
      /ghp_[a-zA-Z0-9]{36,}/,
    ],
  },
  {
    id: 'prompt-injection-override',
    severity: 'critical',
    title: 'Prompt injection - instruction override attempt',
    description: 'Instruction override pattern detected. May subvert agent behavior.',
    remediation: 'Remove override instructions from skill docs and configs.',
    fileTypes: ['.md', '.txt', '.json', '.yaml', '.yml'],
    patterns: [
      /ignore\s+(?:all\s+)?(?:previous|prior|above|earlier)\s+instructions/i,
      /disregard\s+(?:all\s+)?(?:previous|prior|system)\s+(?:instructions|rules)/i,
      /you\s+are\s+now\s+(?:a\s+)?(?:different|new|another)\s+(?:ai|model|assistant)/i,
      /DAN\s*(?:mode|prompt)/i,
      /jailbreak/i,
    ],
  },
  {
    id: 'rce-eval-exec',
    severity: 'critical',
    title: 'Remote code execution risk - eval/exec',
    description: 'Dynamic code execution risk in skill code.',  // noscan
    remediation: 'Avoid eval/exec entirely in skill code.',
    fileTypes: ['.js', '.ts'],
    patterns: [
      /\beval\s*\(/,
      /new\s+Function\s*\(/,
      /child_process\.exec\s*\(/,
      /execSync\s*\(/,
    ],
  },
  {
    id: 'sensitive-file-access',
    severity: 'high',
    title: 'Access to sensitive system files',
    description: 'Skill attempts to read SSH keys, .env, or system files.',
    remediation: 'Only access files explicitly needed by the skill.',
    fileTypes: ['.js', '.ts'],
    patterns: [
      /['"]~\/.ssh\//,
      /['"]~\/.aws\/credentials/,
      /readFileSync\s*\([^)]*\.env/,
      /readFile\s*\([^)]*\.env/,
    ],
  },
  {
    id: 'obfuscated-payload',
    severity: 'high',
    title: 'Obfuscated or encoded payload',
    description: 'Base64-decoded string executed at runtime.',
    remediation: 'Never execute decoded strings.',
    fileTypes: ['.js', '.ts'],
    patterns: [
      /atob\s*\(.*\)\s*.*eval/,
      /Buffer\.from\s*\(.*base64.*\).*eval/,
    ],
  },
  {
    id: 'logging-sensitive-data',
    severity: 'low',
    title: 'Potential sensitive data in logs',
    description: 'Logging calls that may include tokens or passwords.',
    remediation: 'Mask or exclude sensitive values from logs.',
    fileTypes: ['.js', '.ts'],
    patterns: [
      /console\.(log|warn|error)\s*\(.*token/i,
      /console\.(log|warn|error)\s*\(.*password/i,
      /console\.(log|warn|error)\s*\(.*secret/i,
    ],
  },
];

const SCANNABLE_EXTENSIONS = new Set(['.py', '.js', '.ts', '.sh', '.md', '.txt', '.json', '.yaml', '.yml']);


class SkillSecurityScanner {
  constructor(config = {}) {
    this.config = config;
    this.disabledRules = new Set(config.disable_rules || []);
  }

  scanSkill(skillPath) {
    const resolvedPath = path.resolve(skillPath);
    if (!fs.existsSync(resolvedPath)) {
      return { error: `Path not found: ${skillPath}` };
    }

    const findings = [];
    const filesScanned = [];
    const stat = fs.statSync(resolvedPath);

    if (stat.isDirectory()) {
      this._walkDir(resolvedPath).forEach(fp => {
        const ext = path.extname(fp).toLowerCase();
        if (SCANNABLE_EXTENSIONS.has(ext)) {
          const fileFindings = this._scanFile(fp, resolvedPath);
          findings.push(...fileFindings);
          filesScanned.push(path.relative(resolvedPath, fp));
        }
      });
    } else {
      const fileFindings = this._scanFile(resolvedPath, path.dirname(resolvedPath));
      findings.push(...fileFindings);
      filesScanned.push(path.basename(resolvedPath));
    }

    findings.sort((a, b) => (SEVERITY_ORDER[b.severity] || 0) - (SEVERITY_ORDER[a.severity] || 0));

    const counts = { critical: 0, high: 0, medium: 0, low: 0, info: 0 };
    findings.forEach(f => { if (counts[f.severity] !== undefined) counts[f.severity]++; });

    return {
      skillPath: resolvedPath,
      skillName: path.basename(resolvedPath),
      filesScanned,
      totalFiles: filesScanned.length,
      findings,
      counts,
      passed: counts.critical === 0 && counts.high === 0,
    };
  }

  _scanFile(filePath, base) {
    const findings = [];
    let content;
    try {
      content = fs.readFileSync(filePath, 'utf8');
    } catch {
      return findings;
    }

    const lines = content.split('\n');
    const relPath = path.relative(base, filePath);
    const ext = path.extname(filePath).toLowerCase();

    for (const rule of RULES) {
      if (this.disabledRules.has(rule.id)) continue;
      if (!rule.patterns.length) continue;
      if (rule.fileTypes && !rule.fileTypes.includes(ext)) continue;

      for (const pattern of rule.patterns) {
        for (let i = 0; i < lines.length; i++) {
          if (pattern.test(lines[i])) {
            findings.push({
              ruleId: rule.id,
              severity: rule.severity,
              title: rule.title,
              description: rule.description,
              file: relPath,
              line: i + 1,
              snippet: lines[i].trim().substring(0, 120),
              remediation: rule.remediation,
            });
            break; // One finding per rule per file
          }
        }
      }
    }
    return findings;
  }

  _walkDir(dir) {
    const results = [];
    const items = fs.readdirSync(dir, { withFileTypes: true });
    for (const item of items) {
      if (item.name.startsWith('.') || item.name === 'node_modules' || item.name === '__pycache__') continue;
      const full = path.join(dir, item.name);
      if (item.isDirectory()) results.push(...this._walkDir(full));
      else results.push(full);
    }
    return results;
  }

  printReport(result, minSeverity = 'low') {
    if (result.error) { console.log(`❌ Error: ${result.error}`); return; }

    const threshold = SEVERITY_ORDER[minSeverity] || 0;
    const filtered = result.findings.filter(f => (SEVERITY_ORDER[f.severity] || 0) >= threshold);

    console.log('\n' + '='.repeat(70));
    console.log('🔍 Skill Security Scan Report');
    console.log('='.repeat(70));
    console.log(`Skill:    ${result.skillName}`);
    console.log(`Path:     ${result.skillPath}`);
    console.log(`Files:    ${result.totalFiles} scanned`);
    console.log('─'.repeat(70));

    if (!filtered.length) {
      console.log('✅ No findings at or above the selected severity threshold.\n');
    } else {
      for (const f of filtered) {
        const icon = SEVERITY_ICONS[f.severity] || f.severity.toUpperCase();
        console.log(`\n${icon}  [${f.ruleId}]  ${f.file}:${f.line}`);
        console.log(`   ${f.title}`);
        if (f.snippet) console.log(`   Code: ${f.snippet}`);
        console.log(`   Fix:  ${f.remediation}`);
      }
    }

    const c = result.counts;
    console.log('\n' + '─'.repeat(70));
    console.log(`Summary: ${c.critical} critical, ${c.high} high, ${c.medium} medium, ${c.low} low, ${c.info} info`);
    console.log(`Status:  ${result.passed ? '✅ PASSED' : '❌ FAILED'}\n`);
  }
}

module.exports = { SkillSecurityScanner };

// CLI usage: node skill_scanner.js /path/to/skill
if (require.main === module) {
  const [,, skillPath] = process.argv;
  if (!skillPath) {
    console.error('Usage: node skill_scanner.js <skill-path>');
    process.exit(1);
  }
  const scanner = new SkillSecurityScanner();
  const result = scanner.scanSkill(skillPath);
  scanner.printReport(result);
  process.exit(result.passed ? 0 : 1);
}
