sudo neo4j stop
docker-compose up --file local-docker-compose.yml --build --remove-orphans --force-recreate --always-recreate-dep 
