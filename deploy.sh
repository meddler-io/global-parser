docker build --platform linux/amd64  --progress=plain --no-cache   -t meddler/global-parser:debug .

docker tag meddler/global-parser:debug meddler/global-parser:debug
docker push meddler/global-parser:debug



