#!/bin/bash
# Test AI Service locally in Docker

set -e

echo "🚀 Testing AI Service locally in Docker..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from env.sample..."
    if [ -f env.sample ]; then
        cp env.sample .env
        echo "📝 Please edit .env file with your API keys"
        exit 1
    else
        echo "❌ No env.sample file found. Cannot proceed."
        exit 1
    fi
fi

# Build Docker image
echo "🔨 Building Docker image..."
docker build -t ai-service:local .

# Run container
echo "🏃 Starting container..."
docker run -d \
    --name ai-service-test \
    -p 8000:8000 \
    --env-file .env \
    -e ENV=development \
    -e LOG_LEVEL=info \
    -e CORS_ENABLED=true \
    -e CORS_ALLOWED_ORIGINS=* \
    ai-service:local

# Wait for service to be ready
echo "⏳ Waiting for service to start..."
sleep 5

# Health check
echo "🏥 Checking health..."
for i in {1..10}; do
    if curl -f http://localhost:8000/healthz > /dev/null 2>&1; then
        echo "✅ Service is healthy!"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "❌ Service failed to start"
        docker logs ai-service-test
        docker rm -f ai-service-test
        exit 1
    fi
    sleep 2
done

# Test endpoints
echo "🧪 Testing endpoints..."

# Test health endpoint
echo "  - Testing /healthz..."
curl -s http://localhost:8000/healthz | jq . || echo "  ⚠️  Health check response (jq not installed)"

# Test agents endpoint
echo "  - Testing /v1/agents..."
curl -s http://localhost:8000/v1/agents | jq . || curl -s http://localhost:8000/v1/agents

# Test metrics endpoint
echo "  - Testing /metrics..."
curl -s http://localhost:8000/metrics | head -20

echo ""
echo "✅ Service is running!"
echo "📍 Access at: http://localhost:8000"
echo "📊 Metrics at: http://localhost:8000/metrics"
echo "🏥 Health at: http://localhost:8000/healthz"
echo ""
echo "To stop: docker rm -f ai-service-test"
echo "To view logs: docker logs -f ai-service-test"

