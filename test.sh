#!/bin/bash
set -e

echo "====================================="
echo "   Running Peblo Microservice Tests  "
echo "====================================="

# Set dummy env vars for test runner to prevent Pydantic validation errors
export SECRET_KEY="dummy_test_secret"
export MONGODB_URI="mongodb://localhost:27017"
export DATABASE_NAME="peblo_test"
export GROQ_API_KEYS="dummy"
export QDRANT_URL="http://localhost:6333"
export QDRANT_API_KEY="dummy"

echo -e "\n---> Testing Auth Service <---"
cd services/auth
PYTHONPATH=. pytest -v
cd ../..

echo -e "\n---> Testing Ingestion Service <---"
cd services/ingestion
PYTHONPATH=. pytest -v
cd ../..

echo -e "\n---> Testing Quiz Service <---"
cd services/quiz
PYTHONPATH=. pytest -v
cd ../..

echo -e "\n✅ All tests passed successfully!"
