
FROM golang:1.20-alpine as builder
WORKDIR /app
COPY go.mod .
COPY datadis_api_read.go .
COPY sigfox_api_read.go .
COPY wireless_api_read.go .
# Ensure dependencies are downloaded and go.sum is generated
RUN go mod tidy
RUN go build -o datadis_api_read datadis_api_read.go
RUN go build -o sigfox_api_read sigfox_api_read.go
RUN go build -o wireless_api_read wireless_api_read.go

FROM alpine:3.18
WORKDIR /app
COPY --from=builder /app/datadis_api_read .
COPY --from=builder /app/sigfox_api_read .
COPY --from=builder /app/wireless_api_read .

# Set default PG_CONN, can be overridden
ENV PG_CONN=postgres://boreas_user:boreas_password@db:5432/boreas_db?sslmode=disable

# Add crontab
RUN apk add --no-cache dumb-init curl postgresql-client busybox-suid
COPY crontab.txt /etc/crontabs/root

CMD ["dumb-init", "crond", "-f", "-d", "8"]
