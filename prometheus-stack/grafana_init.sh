#!/bin/bash
# Copy dashboard from mounted volume to provisioning directory on startup
cp /tmp/grafana_dashboard_iaq_measures.json /etc/grafana/provisioning/dashboards/ 2>/dev/null || true
cp /tmp/dashboards_provisioning.yaml /etc/grafana/provisioning/dashboards/ 2>/dev/null || true
ls -lah /etc/grafana/provisioning/dashboards/
