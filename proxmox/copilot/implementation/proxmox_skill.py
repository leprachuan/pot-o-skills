#!/usr/bin/env python3
"""Proxmox skill CLI for Copilot runtime.

Thin wrapper that delegates to the shared Claude implementation.
"""
import sys
from pathlib import Path

# Reuse Claude implementation
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "claude" / "implementation"))
from proxmox_skill import main

if __name__ == "__main__":
    main()
