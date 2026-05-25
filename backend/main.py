from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import csv
import io
import os
from screener import score_candidate, parse_profile_text

app = FastAPI(title="LinkedIn Screener API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


@app.get("/", include_in_schema=False)
def serve_frontend():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

# In-memory storage
roles_db: dict = {}
candidates_db: dict = {}
role_counter = 0
candidate_counter = 0


class RoleRequirement(BaseModel):
    title: str
    required_skills: list[str]
    preferred_skills: list[str] = []
    min_years_experience: int = 0
    max_years_experience: Optional[int] = None
    location: Optional[str] = None
    education: Optional[str] = None
    keywords: list[str] = []


class CandidateProfile(BaseModel):
    name: str
    headline: Optional[str] = None
    location: Optional[str] = None
    skills: list[str] = []
    experience_years: int = 0
    education: Optional[str] = None
    profile_text: Optional[str] = None


class ProfileTextInput(BaseModel):
    role_id: int
    profile_text: str


@app.get("/")
def health_check():
    return {"status": "ok", "message": "LinkedIn Screener API is running"}


@app.post("/roles")
def create_role(role: RoleRequirement):
    global role_counter
    role_counter += 1
    roles_db[role_counter] = role.model_dump()
    return {"id": role_counter, "role": roles_db[role_counter]}


@app.get("/roles")
def list_roles():
    return [{"id": k, **v} for k, v in roles_db.items()]


@app.get("/roles/{role_id}")
def get_role(role_id: int):
    if role_id not in roles_db:
        return {"error": "Role not found"}, 404
    return {"id": role_id, **roles_db[role_id]}


@app.delete("/roles/{role_id}")
def delete_role(role_id: int):
    if role_id in roles_db:
        del roles_db[role_id]
    return {"message": "Role deleted"}


@app.post("/candidates/screen")
def screen_candidate_text(input_data: ProfileTextInput):
    """Screen a candidate by pasting their LinkedIn profile text."""
    if input_data.role_id not in roles_db:
        return {"error": "Role not found"}, 404

    role = roles_db[input_data.role_id]
    candidate = parse_profile_text(input_data.profile_text)
    result = score_candidate(candidate, role)

    global candidate_counter
    candidate_counter += 1
    candidates_db[candidate_counter] = {
        "candidate": candidate,
        "role_id": input_data.role_id,
        "score": result,
    }

    return {"id": candidate_counter, "candidate": candidate, "score": result}


@app.post("/candidates/screen-structured")
def screen_candidate_structured(candidate: CandidateProfile, role_id: int):
    """Screen a candidate with structured data."""
    if role_id not in roles_db:
        return {"error": "Role not found"}, 404

    role = roles_db[role_id]
    candidate_dict = candidate.model_dump()
    result = score_candidate(candidate_dict, role)

    global candidate_counter
    candidate_counter += 1
    candidates_db[candidate_counter] = {
        "candidate": candidate_dict,
        "role_id": role_id,
        "score": result,
    }

    return {"id": candidate_counter, "candidate": candidate_dict, "score": result}


@app.post("/candidates/bulk-upload")
async def bulk_upload(role_id: int, file: UploadFile = File(...)):
    """Upload a CSV file with multiple candidates to screen."""
    if role_id not in roles_db:
        return {"error": "Role not found"}, 404

    role = roles_db[role_id]
    content = await file.read()
    decoded = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(decoded))

    results = []
    global candidate_counter

    for row in reader:
        candidate = {
            "name": row.get("name", "Unknown"),
            "headline": row.get("headline", ""),
            "location": row.get("location", ""),
            "skills": [s.strip() for s in row.get("skills", "").split(",") if s.strip()],
            "experience_years": int(row.get("experience_years", 0)),
            "education": row.get("education", ""),
            "profile_text": row.get("profile_text", ""),
        }
        result = score_candidate(candidate, role)

        candidate_counter += 1
        candidates_db[candidate_counter] = {
            "candidate": candidate,
            "role_id": role_id,
            "score": result,
        }
        results.append({"id": candidate_counter, "candidate": candidate, "score": result})

    # Sort by total score descending
    results.sort(key=lambda x: x["score"]["total_score"], reverse=True)
    return {"candidates": results, "total": len(results)}


@app.get("/candidates")
def list_candidates(role_id: Optional[int] = None):
    """List all screened candidates, optionally filtered by role."""
    items = []
    for k, v in candidates_db.items():
        if role_id is None or v["role_id"] == role_id:
            items.append({"id": k, **v})
    items.sort(key=lambda x: x["score"]["total_score"], reverse=True)
    return items


@app.delete("/candidates/{candidate_id}")
def delete_candidate(candidate_id: int):
    if candidate_id in candidates_db:
        del candidates_db[candidate_id]
    return {"message": "Candidate deleted"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
