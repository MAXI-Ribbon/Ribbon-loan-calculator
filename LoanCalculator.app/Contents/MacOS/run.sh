#!/bin/bash
export TK_SILENCE_DEPRECATION=1
SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd ../../.. && pwd )
cd "$SCRIPT_DIR"
/usr/bin/python3 "$SCRIPT_DIR/loan_calculator.py"
