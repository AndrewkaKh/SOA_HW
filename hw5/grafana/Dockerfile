FROM grafana/grafana:10.4.0

USER root
RUN apk add --no-cache curl && grafana-cli plugins install grafana-clickhouse-datasource
COPY grafana/provisioning /etc/grafana/provisioning
USER grafana
