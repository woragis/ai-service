#!/bin/bash

# Test script for AI service agents
# Make sure Docker Desktop is running and containers are up:
# docker-compose -f docker-compose.test.yml up -d

echo "Waiting for services to be ready..."
sleep 10

echo ""
echo "=== Testing Health Endpoint ==="
curl -s http://localhost:8000/healthz | jq .

echo ""
echo "=== Testing Agents List ==="
curl -s http://localhost:8000/v1/agents | jq .

echo ""
echo "=== Testing Economist Agent with OpenAI ==="
curl -s -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "economist",
    "input": "What are the key factors affecting inflation?",
    "provider": "openai"
  }' | jq .

echo ""
echo "=== Testing Strategist Agent with OpenAI ==="
curl -s -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "strategist",
    "input": "How should a company approach market expansion?",
    "provider": "openai"
  }' | jq .

echo ""
echo "=== Testing Entrepreneur Agent with OpenAI ==="
curl -s -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "entrepreneur",
    "input": "What are the most important things to consider when starting a business?",
    "provider": "openai"
  }' | jq .

echo ""
echo "=== Testing Startup Agent with OpenAI ==="
curl -s -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "startup",
    "input": "How do I validate my startup idea?",
    "provider": "openai"
  }' | jq .

echo ""
echo "=== Testing Auto Agent Selection with OpenAI ==="
curl -s -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "auto",
    "input": "What is the best pricing strategy for a SaaS product?",
    "provider": "openai"
  }' | jq .

echo ""
echo "=== All tests completed ==="

