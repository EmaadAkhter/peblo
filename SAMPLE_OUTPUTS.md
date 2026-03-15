# Sample API Inputs & Outputs

## POST /auth/register

**Input:**
```json
{
  "username": "teacher@example.com",
  "password": "password123",
  "role": "teacher"
}
```

**Output:**
```json
{
  "id": "U_0001",
  "username": "teacher@example.com",
  "role": "teacher",
  "grade": null
}
```

## POST /auth/login

**Input:**
```
username=teacher@example.com&password=password123
```

**Output:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZWFjaGVyQGV4YW1wbGUuY29tIiwicm9sZSI6InRlYWNoZXIiLCJleHAiOjE3NDIxNjU0MjF9...",
  "token_type": "bearer"
}
```

## GET /auth/me

**Input:**
```
Authorization: Bearer <access_token>
```

**Output:**
```json
{
  "id": "U_0001",
  "username": "teacher@example.com",
  "role": "teacher",
  "grade": null
}
```

## POST /ingest

**Input:**
```
Content-Type: multipart/form-data

file: biology_grade5.pdf
grade: 5
subject: Science
topic: (optional)
```

**Output:**
```json
{
  "source_id": "SRC_001",
  "status": "processing"
}
```

## GET /ingest/{source_id}/status

**Input:**
```
GET /ingest/SRC_001/status
Authorization: Bearer <access_token>
```

**Output:**
```json
{
  "source_id": "SRC_001",
  "status": "completed",
  "filename": "biology_grade5.pdf",
  "chunk_count": 12
}
```

## GET /ingest/sources

**Input:**
```
GET /ingest/sources
Authorization: Bearer <access_token>
```

**Output:**
```json
[
  {
    "source_id": "SRC_002",
    "filename": "math_fractions.pdf",
    "grade": 4,
    "subject": "Math",
    "uploaded_at": "2026-03-15T10:30:00.000000",
    "status": "completed",
    "chunk_count": 8
  },
  {
    "source_id": "SRC_001",
    "filename": "biology_grade5.pdf",
    "grade": 5,
    "subject": "Science",
    "uploaded_at": "2026-03-15T09:15:00.000000",
    "status": "completed",
    "chunk_count": 12
  }
]
```

## POST /generate-quiz

**Input:**
```json
{
  "source_id": "SRC_001",
  "chunk_ids": null
}
```

**Output:**
```json
{
  "status": "generating",
  "source_id": "SRC_001"
}
```

## GET /topics

**Input:**
```
GET /topics
Authorization: Bearer <access_token>
```

**Output:**
```json
[
  { "topic": "Cell Biology", "subject": "Science" },
  { "topic": "Fractions", "subject": "Math" },
  { "topic": "Photosynthesis", "subject": "Science" }
]
```

## GET /quiz

**Input:**
```
GET /quiz?topic=Cell+Biology&limit=3&student_id=U_0002
Authorization: Bearer <access_token>
```

**Output:**
```json
[
  {
    "id": "Q_SRC001_CH01_001",
    "source_chunk_id": "SRC_001_CH_01",
    "source_id": "SRC_001",
    "subject": "Science",
    "topic": "Cell Biology",
    "grade": 5,
    "type": "MCQ",
    "question": "What is the basic unit of life?",
    "options": ["Atom", "Cell", "Molecule", "Organ"],
    "answer": "Cell",
    "difficulty": "easy",
    "quality_score": 0.95
  },
  {
    "id": "Q_SRC001_CH01_002",
    "source_chunk_id": "SRC_001_CH_01",
    "source_id": "SRC_001",
    "subject": "Science",
    "topic": "Cell Biology",
    "grade": 5,
    "type": "TrueFalse",
    "question": "All living organisms are made up of cells.",
    "options": ["True", "False"],
    "answer": "True",
    "difficulty": "easy",
    "quality_score": 0.92
  },
  {
    "id": "Q_SRC001_CH01_003",
    "source_chunk_id": "SRC_001_CH_01",
    "source_id": "SRC_001",
    "subject": "Science",
    "topic": "Cell Biology",
    "grade": 5,
    "type": "FillInTheBlank",
    "question": "The _____ is the powerhouse of the cell.",
    "options": null,
    "answer": "Mitochondria",
    "difficulty": "medium",
    "quality_score": 0.88
  }
]
```

## POST /submit-answer

**Input:**
```json
{
  "question_id": "Q_SRC001_CH01_001",
  "selected_answer": "Cell"
}
```

**Output:**
```json
{
  "is_correct": true,
  "correct_answer": "Cell",
  "new_difficulty": "medium",
  "topic": "Cell Biology"
}
```

## GET /analytics/students

**Input:**
```
GET /analytics/students
Authorization: Bearer <access_token>
```

**Output:**
```json
[
  {
    "student_id": "U_0002",
    "student_name": "alice",
    "topic": "Cell Biology",
    "subject": "Science",
    "total_questions": 8,
    "correct_answers": 6,
    "score_percentage": 75.0,
    "last_activity": "2026-03-15T11:42:00.000000",
    "answers": [
      {
        "question_text": "What is the basic unit of life?",
        "selected_answer": "Cell",
        "correct_answer": "Cell",
        "is_correct": true
      }
    ]
  }
]
```

## DELETE /ingest/{source_id}

**Input:**
```
DELETE /ingest/SRC_001
Authorization: Bearer <access_token>
```

**Output:**
```json
{
  "deleted": true,
  "source_id": "SRC_001",
  "chunks_deleted": 12,
  "questions_deleted": 34
}
```

## DELETE /quiz/{question_id}

**Input:**
```
DELETE /quiz/Q_SRC001_CH01_001
Authorization: Bearer <access_token>
```

**Output:**
```json
{
  "deleted": true,
  "question_id": "Q_SRC001_CH01_001"
}
```
