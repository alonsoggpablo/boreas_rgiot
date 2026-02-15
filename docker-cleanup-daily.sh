#!/bin/bash
# docker-cleanup-daily.sh
# Deletes all unused Docker data daily and logs the result

date >> /var/log/docker-cleanup.log
docker system prune -af --volumes >> /var/log/docker-cleanup.log 2>&1
echo "Cleanup complete." >> /var/log/docker-cleanup.log
