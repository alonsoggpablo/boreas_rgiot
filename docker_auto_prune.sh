#!/bin/bash
# Prune all unused Docker resources (containers, images, volumes, networks)
docker system prune -a --volumes --force
