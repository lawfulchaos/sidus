docker-compose -f docker-compose.test.yml up -d --build
docker logs --tail=1000 -f async_backend_test
docker-compose down
exit $rc