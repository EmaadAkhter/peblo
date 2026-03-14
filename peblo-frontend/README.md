# Peblo Frontend — Quiz Platform UI

A React + Vite application for teachers to upload PDFs and generate quizzes, and for students to take adaptive quizzes.

## Setup

```bash
cd peblo-frontend
npm install
cp .env.example .env   # edit if your backend runs on a different port
npm run dev
```

> **Prerequisite:** The Peblo backend must be running at the URL specified in `.env` (default: `http://localhost:8000`).

## Views

### Teacher View 🎓
- Upload PDFs with grade and subject metadata
- Monitor ingestion status (auto-polls every 4s)
- Trigger quiz generation for completed sources

### Student View 📖
- Pick a topic from a grid of emoji cards
- Take a quiz with 3 question types (MCQ, True/False, Fill in the Blank)
- See results with an animated score ring and difficulty progression
- Difficulty adjusts automatically per topic using the backend's adaptive engine

## Student ID

On first visit as a student, the app asks for a name. This is stored in `localStorage` under key `peblo_student_id` and used for adaptive difficulty tracking. Clear it from browser DevTools to reset.

## Tech Stack

- React 18 + Vite
- CSS Modules with custom properties (no Tailwind)
- Lucide React icons
- Google Fonts: Nunito + Fraunces

## Screenshots

<!-- Add your screenshots here -->
