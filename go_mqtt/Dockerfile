# Go MQTT Subscriber Dockerfile (TEST BUILD CONTEXT - 2026-02-12)
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY . .
RUN go mod tidy && go build -o go_mqtt_subscriber .

FROM alpine:3.18
WORKDIR /app
COPY --from=builder /app/go_mqtt_subscriber ./
CMD ["./go_mqtt_subscriber"]
