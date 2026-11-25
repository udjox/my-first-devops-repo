# Версия Go соответствует методичке. Зависимости кэшируются отдельно от кода.
FROM golang:1.22-alpine AS builder
WORKDIR /build
COPY backend/go.mod backend/go.sum ./
RUN go mod download
COPY backend/ ./
RUN CGO_ENABLED=0 GOOS=linux go build -trimpath -ldflags="-s -w" -o /out/app .

# Компилятор и shell не попадают в runtime; приложение работает без прав root.
FROM gcr.io/distroless/static-debian12:nonroot
WORKDIR /app
COPY --from=builder /out/app /app/app
COPY frontend/ /app/static/
ENV HTTP_PORT=8080 STATIC_DIR=/app/static
USER 65532:65532
EXPOSE 8080
# Проверка здоровья выполняется самим бинарником: curl и shell не требуются.
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 CMD ["/app/app", "healthcheck"]
ENTRYPOINT ["/app/app"]
