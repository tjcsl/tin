<p align="center">
  <img src="docs/source/_static/tin-logo.gif" width="500">
</p>
<br>
<p align="center">
  <i>An autograder for Computer Science Classes</i>
  <br>
  <br>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json"></a>
  <img src="https://github.com/tjcsl/tin/actions/workflows/ci.yml/badge.svg">
  <a href="https://github.com/pre-commit/pre-commit"><img src="https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit"></a>
  <a href='https://coveralls.io/github/tjcsl/tin'><img src='https://coveralls.io/repos/github/tjcsl/tin/badge.svg' alt='Coverage Status' /></a>
  <a href="https://wakatime.com/badge/github/tjcsl/tin"><img src="https://wakatime.com/badge/github/tjcsl/tin.svg" alt="wakatime"></a>
</p>
<hr>

## History
Previously, teachers in TJHSST CS classes had to manually run student code. As you can imagine,
this was both time consuming, and dangerous. In order to solve this problem, Tin was invented
to safely run student code submissions.

## Architecture
Tin is a Django application backed by PostgreSQL and SQLite. We use Celery (with a RabbitMQ broker) to process tasks.

## Features
* Teacher management view for courses
* Uploads for teacher's grader scripts
* Customized containers for grader scripts

## Developing
Check out the most up to date installation instructions at [Tin's Documentation](https://tjcsl.github.io/tin/)!
