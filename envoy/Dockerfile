FROM alpine:latest AS builder
RUN apk add --no-cache curl unzip
RUN curl -L -o coraza.zip https://github.com/corazawaf/coraza-proxy-wasm/releases/download/0.6.0/coraza-proxy-wasm-0.6.0.zip
RUN unzip coraza.zip -d /coraza

FROM envoyproxy/envoy:v1.30.0
COPY --from=builder /coraza/coraza-proxy-wasm.wasm /etc/envoy/coraza-proxy-wasm.wasm
RUN chmod +r /etc/envoy/coraza-proxy-wasm.wasm
