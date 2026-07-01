docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml --profile dev down
docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml --profile dev up -d --build
pause
