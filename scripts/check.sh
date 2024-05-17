#!/bin/bash
cd "$(dirname -- "$(dirname -- "$(readlink -f "$0")")")"

echo "This script is now deprecated, please use pre-commit instead."
echo "To run pre-commit before commiting, do 'pre-commit install'"

for cmd in flake8 isort pylint; do
    if [[ ! -x "$(which "$cmd")" ]]; then
        echo "Could not find $cmd. Please make sure that flake8, isort, and pylint are all installed."
        exit 1
    fi
done

flake8 tin && isort tin && pylint tin
