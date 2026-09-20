from setuptools import setup, find_packages

setup(
    name="omniswarm-os",
    version="1.0.0",
    description="The Absolute Root Kernel for Edge-First AI Swarms",
    author="Polymath-Void",
    packages=find_packages(),
    install_requires=[
        "pyzmq>=24.0.0",
        "psutil>=5.9.0",
        "tornado>=6.1"
    ],
    python_requires=">=3.10",
)
