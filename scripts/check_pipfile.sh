#!/bin/bash

if ! command -v pipenv &> /dev/null
then
  echo "Please install pipenv with your distributions package manager"
  exit 1
fi

set -e
pipenv verify
