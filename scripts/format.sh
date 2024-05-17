#!/bin/bash
cd "$(dirname -- "$(dirname -- "$(readlink -f "$0")")")"

echo "This script is now deprecated, please use pre-commit instead"
echo "To run pre-commit before commiting, do 'pre-commit install'"

for cmd in black autopep8 isort; do
    if [[ ! -x "$(which "$cmd")" ]]; then
        echo "Could not find $cmd. Please make sure that black, autopep8, and isort are all installed."
        exit 1
    fi
done

# Order is important. There are a few things that black and autopep8 disagree on, and I side
# with autopep8 on those.
black tin && autopep8 --in-place --recursive tin && isort tin
