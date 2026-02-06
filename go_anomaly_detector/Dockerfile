FROM golang:1.21-alpine AS builder

WORKDIR /build

# Install build dependencies
RUN apk add --no-cache git

# Copy go module files
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build the binary
RUN CGO_ENABLED=0 GOOS=linux go build -o anomaly_detector .

# Final stage
FROM alpine:latest

RUN apk --no-cache add ca-certificates tzdata

WORKDIR /app

# Copy binary from builder
COPY --from=builder /build/anomaly_detector .

# Create data directory for Parquet files
RUN mkdir -p /app/data/reported_measures_archive

ENV TZ=Europe/Madrid

CMD ["/app/anomaly_detector"]
