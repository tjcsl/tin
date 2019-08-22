#!/bin/bash
cd "$(dirname -- "$(dirname -- "$(readlink -f "$0")")")"

flake8 tin && isort --recursive --check tin && pylint tin
