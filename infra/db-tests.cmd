@echo off
setlocal
pushd "%~dp0"

set "TEST_PROJECT=geoservice-db-tests"

docker compose -p "%TEST_PROJECT%" -f docker-compose.test.yml down -v --remove-orphans
if errorlevel 1 goto :initial_cleanup_failed

docker compose -p "%TEST_PROJECT%" -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from backend_db_tests
set "TEST_EXIT=%ERRORLEVEL%"

docker compose -p "%TEST_PROJECT%" -f docker-compose.test.yml down -v --remove-orphans
set "CLEANUP_EXIT=%ERRORLEVEL%"

popd
if not "%TEST_EXIT%"=="0" exit /b %TEST_EXIT%
exit /b %CLEANUP_EXIT%

:initial_cleanup_failed
set "CLEANUP_EXIT=%ERRORLEVEL%"
popd
exit /b %CLEANUP_EXIT%
