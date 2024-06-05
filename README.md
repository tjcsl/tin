<p align="center">
  <img src="./assets/tin-logo.gif" width="500">
</p>
<br>
<p align="center">
  <i>An autograder for Computer Science Classes</i>
  <br>
  <br>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json"></a>
  <img src="https://github.com/tjcsl/tin/actions/workflows/ci.yml/badge.svg">
  <a href="https://github.com/pre-commit/pre-commit"><img src="https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit"></a>
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
To work on Tin, you'll need the following:
* `pipenv`
* `git`
* A Github account

First, [fork](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo#forking-a-repository) Tin.
Then you can clone Tin onto your local computer with
```bash
git clone https://github.com/your_github_username/tin
```
After that, install dependencies:
```bash
pipenv install --dev
```

And finally, apply the database migrations and create some users.

Note: if you're on Windows, replace `python3` with `python` in the commands below
```bash
python3 manage.py migrate
python3 create_debug_users.py
```
Now you can run the Tin development server!
```bash
python3 manage.py runserver
```
Head over to [http://127.0.0.1:8000](http://127.0.0.1:8000), and
login with the username `admin` and the password you just entered.

## Data Backup
```bash
python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e admin -e auth.Permission > export_YYYY_MM_DD.json
# copy to local machine
iconv -f ISO-8859-1 -t UTF-8 export_YYYY_MM_DD.json > export_YYYY_MM_DD_utf8.json
python manage.py loaddata export_YYYY_MM_DD_utf8.json
```
