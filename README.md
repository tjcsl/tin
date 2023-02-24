# Tin: Turn-In

The ultimate grader solution for TJHSST Aritifical Intelligence classes.

## History
Previously, teachers in TJHSST AI classes had to manually run student code.

## Architecture
Tin is a Django application backed by PostgreSQL and SQLite. We use Celery (with a RabbitMQ broker) to process tasks.

## Features
* Teacher management view for courses
* Uploads for teacher's grader scripts
* Customized containers for grader scripts
