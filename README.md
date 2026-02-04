# FosterBot Public Skills

**Public skills repository for FosterBot AI agent.**

This repository contains public skills developed for the FosterBot orchestrator that are ready for release. Skills are available to:
- Claude Code
- Copilot CLI  
- Gemini AI

All skills follow Claude Skills best practices and are designed to work seamlessly across all three AI runtimes.

## Skill Development

Each skill is developed as a standalone module that implements the same interface across Claude, Copilot, and Gemini platforms.

### Structure

Each skill lives in its own directory:
```
/opt/skills/
├── skill-1/
│   ├── README.md
│   ├── skill_metadata.json
│   ├── claude/
│   │   └── implementation
│   ├── copilot/
│   │   └── implementation
│   └── gemini/
│       └── implementation
├── skill-2/
│   ├── README.md
│   ├── skill_metadata.json
│   └── ...
```

## Development Workflow

1. Skills begin in `/opt/foster-skills/` (private)
2. Once mature and tested, promoted to `/opt/skills/` (public)
3. Ready for distribution and community use

## Integration

Skills are registered in the FosterbotHome orchestrator and exposed to all runtimes:
- **Claude**: Via Claude Skills interface
- **Copilot CLI**: Via skill commands  
- **Gemini**: Via Gemini integration

## Best Practices

All skills follow:
- Claude Skills best practices
- Cross-platform compatibility (Claude, Copilot, Gemini)
- Comprehensive documentation
- Clear parameter definitions
- Example usage for each platform

---

**Repository**: leprachuan/skills (private - during development)
**Status**: Public release preparation
