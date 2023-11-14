sudo neo4j stop
docker-compose --file local-docker-compose.yml up --build --remove-orphans --force-recreate --always-recreate-dep 
