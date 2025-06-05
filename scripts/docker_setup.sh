#!/usr/bin/env bash

if [ ! "$(docker ps -q -f name=tin_django)" ]; then
    echo "Container 'tin_django' not found. Please run 'docker compose up' first."
    exit 1
fi

docker exec tin_django /bin/sh -c "cd /app && python manage.py migrate && python manage.py create_debug_users --noinput"
echo
echo "Done! Visit http://localhost:8000 to access the development server."
echo "The default password for all users is 'jasongrace'."
