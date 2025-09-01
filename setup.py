#!/usr/bin/env python3
"""
Minimal setup.py for backward compatibility with older pip/setuptools versions.
The main configuration is in pyproject.toml.
"""

from setuptools import setup

# This setup.py exists for compatibility with older build tools
# All configuration is in pyproject.toml
if __name__ == "__main__":
    setup()