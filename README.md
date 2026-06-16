# Studium - AI Quiz Platform

Studium is a modern, AI-powered quiz platform built with a microservices architecture. It enables teachers to upload educational PDFs, instantly generates quizzes using LLMs, and allows students to take adaptive quizzes tailored to their performance.

## System Architecture

Studium routes external requests through an Nginx API Gateway to three distinct, specialized microservices. All services connect to a shared MongoDB instance, and the ingestion service interacts with external LLMs and Vector databases.

![System Architecture](assets/System_Architecture.png)

## Setup & Local Development

### 1. Configure Environment Variables

Create a `.env` file in the root directory (you can copy `.env.example` if it exists). The environment variables must be populated to connect to the databases and external APIs.

```env
# MongoDB Connection (Shared Datastore)
MONGODB_URI=mongodb+srv://<your_username>:<your_password>@<your_cluster>.mongodb.net/
DATABASE_NAME=Studium

# Qdrant Vector DB (For Ingestion & Deduplication)
QDRANT_URL=https://<your_cluster>.aws.cloud.qdrant.io:6333
QDRANT_API_KEY=<your_qdrant_api_key>

# LLM APIs (Comma separated for key rotation to avoid rate limits)
GROQ_API_KEYS=key1,key2,key3

# JWT Security (Used to issue and verify access tokens)
SECRET_KEY=your-super-secret-jwt-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### 2. Install Dependencies (For Local Testing)

If you wish to run the automated tests or develop logic directly on your host machine without Docker, install the python dependencies using a virtual environment:

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install microservice dependencies
pip install -r services/auth/requirements.txt
pip install -r services/ingestion/requirements.txt
pip install -r services/quiz/requirements.txt

# Install testing utilities
pip install pytest httpx pytest-asyncio
```

### 3. Run the Backend (Docker)

The production-ready way to run the entire backend stack (including all three microservices and the Nginx gateway) is using Docker Compose:

```bash
docker-compose up --build
```

The API Gateway will be available at `http://localhost`. All requests should be sent to this base URL, and Nginx will route them to the appropriate underlying microservice.

### 4. How to Test Endpoints

We provide comprehensive, automated unit tests for every microservice using `pytest` and FastAPI's `TestClient` to test the endpoints and internal logic.

To run the complete set of tests across all microservices, run the provided bash script:

```bash
# Ensure your virtual environment is activated
source venv/bin/activate

# Execute the test suite script
./test.sh
```

Alternatively, to run tests for an individual microservice, you can navigate into its directory and run pytest manually (ensure your `PYTHONPATH` allows resolution of the `app` module):

```bash
# Example: Testing the Ingestion Service individually
cd services/ingestion
PYTHONPATH=. pytest -v
```

---

## Architectural Decisions & Trade-offs

1. **Microservices over Monolith:** This pattern isolates compute-heavy workloads (PDF parsing, LLM generation) from read-heavy workloads (serving adaptive quizzes). A spike in document ingestion won't degrade the response time for students actively taking tests.
2. **Qdrant for Deduplication:** Using a vector database allows for *semantic* deduplication. Instead of just preventing exact file duplicates via hashing, Qdrant prevents the system from storing redundant questions if a teacher uploads two entirely different PDFs that cover the exact same subject matter.
3. **Rolling Window Adaptive Difficulty:** Rather than a naive correct=up/wrong=down algorithm, difficulty is calculated using a rolling window of recent performance. This prevents a single accidental wrong answer from instantly punishing the student with drastically harder or easier subsequent questions.
4. **Auth Service Code Duplication:** The JWT validation logic and user models are currently duplicated across the Auth, Ingestion, and Quiz services. In production we'd extract auth into a shared internal package published to a private PyPI registry, since gateway-level validation would require the gateway to decode JWTs and adds a single point of failure.
5. **In-Memory Cache vs Redis:** The Quiz service utilizes a simple in-memory `TTLCache` to speed up question retrieval. While a distributed cache like Redis is necessary in production (to survive container restarts and share state across horizontal replicas), the in-memory cache was intentionally chosen here to simplify the local deployment footprint for reviewers.
