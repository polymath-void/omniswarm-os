import sys
from setuptools import setup, find_packages

install_reqs = [
    "pyzmq>=24.0.0",
    "tornado>=6.1"
]

if not hasattr(sys, 'getandroidapilevel'):
    install_reqs.append("psutil>=5.9.0")

setup(
    name="omniswarm-os",
    version="1.0.0",
    description="The Absolute Root Kernel for Edge-First AI Swarms",
    author="Polymath-Void",
    packages=find_packages(),
    install_requires=install_reqs,
    python_requires=">=3.10",
)
