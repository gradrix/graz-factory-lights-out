#!/bin/sh
set -eu
cd /home/gradrix/gflo-browser-probe
app=gflo-browser-probe-app
browser=gflo-browser-probe-chromium
cleanup(){ docker rm -f "$browser" "$app" >/dev/null 2>&1 || true; }
# Refuse to replace any pre-existing container, even one with our name.
if docker inspect "$app" >/dev/null 2>&1 || docker inspect "$browser" >/dev/null 2>&1; then echo 'owned names already occupied'; exit 2; fi
trap cleanup EXIT INT TERM
docker run -d --name "$app" --label gflo.probe=browser-boundary --runtime=runc --network=none --read-only --user=1000:1000 --cap-drop=ALL --security-opt=no-new-privileges --pids-limit=64 --memory=128m --cpus=0.25 --ipc=private --shm-size=16m -v "$PWD/app.cjs:/app.cjs:ro" sha256:88f8ba583a884279252779bbe221bf1ff2c61cf236cc973f8ca97676ae6d07f0 node /app.cjs > app-id.txt
docker create --name "$browser" --label gflo.probe=browser-boundary --runtime=runc --network="container:$app" --read-only --user=1000:1000 --cap-drop=ALL --security-opt=no-new-privileges --security-opt="seccomp=$PWD/seccomp.json" --init --pids-limit=256 --memory=1g --memory-swap=1g --cpus=2 --ipc=private --shm-size=256m --tmpfs=/tmp:rw,nosuid,size=256m -e HOME=/tmp -e DEBUG=pw:browser -v "$PWD:/probe:ro" mcr.microsoft.com/playwright@sha256:bc6ab0d6d44ff4826e4cb8c1e6d801e185bfc42bb0753f8e2a30efc70db054c7 timeout 60 node /probe/probe.cjs > browser-id.txt
docker inspect "$browser" "$app" > containers.json
set +e
docker start -a "$browser" > result.log 2>&1
result=$?
set -e
docker inspect "$browser" "$app" > completed-containers.json
printf '%s\n' "$result" > result.exit
exit "$result"
