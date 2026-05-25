"""
LinkedIn Profile Screening Engine.
Scores candidates against role requirements using keyword matching,
skill overlap, experience fit, and location matching.
"""

import re
from typing import Optional


def parse_profile_text(text: str) -> dict:
    """
    Parse unstructured LinkedIn profile text into structured candidate data.
    Extracts name, skills, experience years, location, education, and headline.
    """
    lines = [line.strip() for line in text.strip().split("\n") if line.strip()]

    candidate = {
        "name": "",
        "headline": "",
        "location": "",
        "skills": [],
        "experience_years": 0,
        "education": "",
        "profile_text": text,
    }

    if lines:
        candidate["name"] = lines[0]

    if len(lines) > 1:
        candidate["headline"] = lines[1]

    # Extract location
    location_patterns = [
        r"(?:location|based in|located in|from)[:\s]+(.+)",
        r"([\w\s]+,\s*[\w\s]+(?:,\s*\w+)?)\s*$",
    ]
    for line in lines:
        for pattern in location_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match and len(match.group(1)) < 50:
                candidate["location"] = match.group(1).strip()
                break

    # Extract experience years
    exp_patterns = [
        r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)",
        r"experience[:\s]*(\d+)\+?\s*(?:years?|yrs?)",
    ]
    for line in lines:
        for pattern in exp_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                candidate["experience_years"] = int(match.group(1))
                break

    # Extract skills from "Skills:" section or comma-separated lists
    skills_section = False
    for line in lines:
        if re.match(r"skills?\s*[:\-]", line, re.IGNORECASE):
            skills_section = True
            skill_text = re.sub(r"skills?\s*[:\-]\s*", "", line, flags=re.IGNORECASE)
            if skill_text:
                candidate["skills"].extend([s.strip() for s in re.split(r"[,;|•·]", skill_text) if s.strip()])
            continue
        if skills_section:
            if re.match(r"\w+\s*[:\-]", line) and not re.match(r"skills?\s*[:\-]", line, re.IGNORECASE):
                skills_section = False
            else:
                candidate["skills"].extend([s.strip() for s in re.split(r"[,;|•·]", line) if s.strip()])

    # Extract education
    edu_keywords = ["bachelor", "master", "phd", "mba", "b.tech", "m.tech", "b.e", "m.e",
                    "b.s", "m.s", "b.sc", "m.sc", "university", "college", "institute"]
    for line in lines:
        if any(kw in line.lower() for kw in edu_keywords):
            candidate["education"] = line
            break

    # If no skills found, try to extract from the full text
    if not candidate["skills"]:
        common_skills = extract_common_skills(text)
        candidate["skills"] = common_skills

    return candidate


def extract_common_skills(text: str) -> list[str]:
    """Extract commonly recognized tech/business skills from text."""
    skill_keywords = [
        "python", "java", "javascript", "typescript", "react", "angular", "vue",
        "node.js", "express", "django", "flask", "fastapi", "spring", "aws",
        "azure", "gcp", "docker", "kubernetes", "terraform", "ci/cd",
        "machine learning", "deep learning", "nlp", "data science", "sql",
        "nosql", "mongodb", "postgresql", "redis", "elasticsearch",
        "agile", "scrum", "product management", "project management",
        "leadership", "communication", "team management", "strategic planning",
        "marketing", "sales", "analytics", "tableau", "power bi",
        "figma", "sketch", "ui/ux", "design", "html", "css",
        "git", "linux", "networking", "security", "devops",
        "c++", "c#", ".net", "rust", "go", "swift", "kotlin",
        "microservices", "rest api", "graphql", "testing", "qa",
    ]

    found = []
    text_lower = text.lower()
    for skill in skill_keywords:
        if skill in text_lower:
            found.append(skill)
    return found


def score_candidate(candidate: dict, role: dict) -> dict:
    """
    Score a candidate against role requirements.
    Returns breakdown of scores and a total score (0-100).
    """
    scores = {
        "skills_required_score": 0,
        "skills_preferred_score": 0,
        "experience_score": 0,
        "location_score": 0,
        "keyword_score": 0,
        "total_score": 0,
        "matched_required_skills": [],
        "missing_required_skills": [],
        "matched_preferred_skills": [],
        "recommendation": "",
    }

    # --- Skills Matching (50% weight) ---
    required_skills = [s.lower().strip() for s in role.get("required_skills", [])]
    preferred_skills = [s.lower().strip() for s in role.get("preferred_skills", [])]
    candidate_skills = [s.lower().strip() for s in candidate.get("skills", [])]

    # Also check profile text for skills
    profile_text = (candidate.get("profile_text") or "").lower()
    headline = (candidate.get("headline") or "").lower()
    combined_text = f"{profile_text} {headline}"

    # Required skills matching
    matched_required = []
    missing_required = []
    for skill in required_skills:
        if skill in candidate_skills or skill in combined_text:
            matched_required.append(skill)
        else:
            # Fuzzy partial match
            if any(skill in cs or cs in skill for cs in candidate_skills):
                matched_required.append(skill)
            else:
                missing_required.append(skill)

    scores["matched_required_skills"] = matched_required
    scores["missing_required_skills"] = missing_required

    if required_skills:
        scores["skills_required_score"] = round((len(matched_required) / len(required_skills)) * 100)

    # Preferred skills matching
    matched_preferred = []
    for skill in preferred_skills:
        if skill in candidate_skills or skill in combined_text:
            matched_preferred.append(skill)
        elif any(skill in cs or cs in skill for cs in candidate_skills):
            matched_preferred.append(skill)

    scores["matched_preferred_skills"] = matched_preferred

    if preferred_skills:
        scores["skills_preferred_score"] = round((len(matched_preferred) / len(preferred_skills)) * 100)

    # --- Experience Matching (25% weight) ---
    candidate_exp = candidate.get("experience_years", 0)
    min_exp = role.get("min_years_experience", 0)
    max_exp = role.get("max_years_experience")

    if min_exp == 0 and max_exp is None:
        scores["experience_score"] = 100
    elif max_exp is None:
        if candidate_exp >= min_exp:
            scores["experience_score"] = 100
        elif candidate_exp >= min_exp - 1:
            scores["experience_score"] = 75
        elif candidate_exp >= min_exp - 2:
            scores["experience_score"] = 50
        else:
            scores["experience_score"] = max(0, 25 - (min_exp - candidate_exp) * 5)
    else:
        if min_exp <= candidate_exp <= max_exp:
            scores["experience_score"] = 100
        elif candidate_exp > max_exp:
            over = candidate_exp - max_exp
            scores["experience_score"] = max(50, 100 - over * 10)
        else:
            under = min_exp - candidate_exp
            scores["experience_score"] = max(0, 100 - under * 25)

    # --- Location Matching (10% weight) ---
    role_location = (role.get("location") or "").lower().strip()
    candidate_location = (candidate.get("location") or "").lower().strip()

    if not role_location:
        scores["location_score"] = 100  # No location requirement
    elif not candidate_location:
        scores["location_score"] = 50  # Unknown location
    elif role_location in candidate_location or candidate_location in role_location:
        scores["location_score"] = 100
    else:
        # Check partial match (same country/state)
        role_parts = set(role_location.replace(",", " ").split())
        candidate_parts = set(candidate_location.replace(",", " ").split())
        overlap = role_parts & candidate_parts
        if overlap:
            scores["location_score"] = 60
        else:
            scores["location_score"] = 20

    # --- Keyword Matching (15% weight) ---
    keywords = [k.lower().strip() for k in role.get("keywords", [])]
    if keywords:
        matched_keywords = sum(1 for kw in keywords if kw in combined_text or kw in " ".join(candidate_skills))
        scores["keyword_score"] = round((matched_keywords / len(keywords)) * 100)
    else:
        scores["keyword_score"] = 100  # No keywords defined

    # --- Total Score ---
    total = (
        scores["skills_required_score"] * 0.40
        + scores["skills_preferred_score"] * 0.10
        + scores["experience_score"] * 0.25
        + scores["location_score"] * 0.10
        + scores["keyword_score"] * 0.15
    )
    scores["total_score"] = round(total)

    # --- Recommendation ---
    if scores["total_score"] >= 80:
        scores["recommendation"] = "Strong Match"
    elif scores["total_score"] >= 60:
        scores["recommendation"] = "Good Match"
    elif scores["total_score"] >= 40:
        scores["recommendation"] = "Partial Match"
    else:
        scores["recommendation"] = "Weak Match"

    return scores
