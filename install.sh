#!/bin/bash
echo "Installing OmniOS..."
pip install -e .
echo "OmniOS Installation Complete. Boot the daemon via 'python3 omniswarm-py/omniswarm_daemon.py &'"
