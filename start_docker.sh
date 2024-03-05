sudo neo4j stop
celery -A router.celery worker --loglevel=info
docker compose --file docker-compose.yml up --build --remove-orphans --force-recreate