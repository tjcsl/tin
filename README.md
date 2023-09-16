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

## Data Backup

```bash
python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e admin -e auth.Permission > export_YYYY_MM_DD.json
# copy to local machine
iconv -f ISO-8859-1 -t UTF-8 export_YYYY_MM_DD.json > export_YYYY_MM_DD_utf8.json
python manage.py loaddata export_YYYY_MM_DD_utf8.json
```
