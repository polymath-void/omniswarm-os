import sys
import os
from setuptools import setup, find_packages

is_termux = "com.termux" in os.environ.get("PREFIX", "") or hasattr(sys, 'getandroidapilevel')

install_reqs = [
    "pyzmq>=24.0.0",
    "tornado>=6.1",
    "websockets>=11.0"
]

if not is_termux:
    install_reqs.append("psutil>=5.9.0")

setup(
    name="omniswarm-os",
    version="1.1.0",
    description="The Universal Decentralized Operating System for Edge-First AI Agent Swarms",
    author="Polymath-Void",
    packages=find_packages(),
    install_requires=install_reqs,
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "omnios-cli=omnios_cli:main",
        ],
    },
)
