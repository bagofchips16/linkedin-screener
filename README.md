# LinkedIn Screener

An HR tool to screen LinkedIn candidates against role requirements using keyword-based scoring.

## Features

- **Role Definition**: Define roles with required/preferred skills, experience range, location, and keywords
- **Profile Screening**: Paste LinkedIn profile text to score candidates
- **Bulk Upload**: Upload CSV files with multiple candidates
- **Scoring Engine**: Weighted scoring across skills, experience, location, and keywords
- **Results Dashboard**: Ranked candidates with detailed score breakdowns

## Tech Stack

- **Backend**: Python + FastAPI
- **Frontend**: React + Vite
- **Scoring**: Rule-based keyword matching (no external APIs needed)

## Setup

### Backend

```bash
cd backend
pip install -r requirements.txt
python main.py
```

The API will run on http://localhost:8000

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The app will run on http://localhost:5173

## CSV Format for Bulk Upload

```csv
name,headline,location,skills,experience_years,education,profile_text
John Smith,Senior Engineer,Bangalore India,"python,react,aws",5,B.Tech IIT,Full profile text here
```

## Scoring Weights

| Category | Weight |
|----------|--------|
| Required Skills | 40% |
| Experience Match | 25% |
| Keywords | 15% |
| Location Match | 10% |
| Preferred Skills | 10% |
