#!/usr/bin/env bash
# Member 1. Snapshot of container resource usage + configured limits (evidence for the video).
docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.PIDs}}'
echo; docker inspect $(docker compose ps -q) --format '{{.Name}} mem_limit={{.HostConfig.Memory}} nano_cpus={{.HostConfig.NanoCpus}} pids={{.HostConfig.PidsLimit}}'
