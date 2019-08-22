#!/bin/bash
cd "$(dirname -- "$(dirname -- "$(readlink -f "$0")")")"

# Order is important. There are a few things that black and autopep8 disagree on, and I side
# with autopep8 on those.
black tin && autopep8 --in-place --recursive tin && isort --recursive tin
