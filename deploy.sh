sudo git pull
docker build  --progress=plain --no-cache  --build-arg WATCHDOG_VERSION=$(date +%Y.%m.%d.%H.%M.%S)  -t meddler/global-parser:debug .

docker tag meddler/global-parser:debug meddler/global-parser:debug
docker push meddler/global-parser:debug



