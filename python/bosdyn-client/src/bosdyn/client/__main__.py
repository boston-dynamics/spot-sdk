"""Command-line tool for interacting with robot services"""
import sys
from .command_line import main

if __name__ == "__main__":
    if not main():
        sys.exit(1)
