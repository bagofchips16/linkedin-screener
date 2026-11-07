"""Fetches HR jobs in Bangalore from Adzuna and Google Jobs (SerpAPI), filters and scores them."""

import hashlib
import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone

import alerts
import job_store
from config import Settings, get_settings

HR_TITLE = re.compile(
    r"\b(hr|hrbp|human resources?|talent|people (?:operations|partner|business|culture|ops)|recruit\w*|"
    r"learning (?:and|&) development|compensation|c&b|total rewards)\b",
    re.I,
)
JUNIOR_TITLE = re.compile(r"\b(intern|internship|trainee|fresher|apprentice|associate)\b", re.I)
SENIOR_TITLE = re.compile(r"\b(senior|sr\.?|lead|head|director|vp|vice president|principal|manager|chro)\b", re.I)

_EXP_RE = re.compile(r"(\d{1,2})\s*(?:\+|plus)?\s*(?:(?:-|–|to)\s*(\d{1,2}))?\s*\+?\s*(?:years?|yrs?)\b", re.I)
_LPA_RANGE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:-|–|to)\s*(\d+(?:\.\d+)?)\s*(?:lpa|lakhs?|lacs?)", re.I)
_LPA_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:lpa|lakhs?|lacs?)", re.I)
_CRORE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:cr|crores?)\b", re.I)
_RUPEES_RE = re.compile(r"(?:₹|rs\.?|inr)\s*([\d,]{7,})", re.I)


def _http_get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "linkedin-screener-job-finder"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _safe_url(url: str | None) -> str:
    return url if url and url.lower().startswith(("http://", "https://")) else ""


def parse_salary_max_inr(text: str) -> int | None:
    """Best-case annual salary mentioned in free text, in INR."""
    values: list[float] = []
    if m := _LPA_RANGE_RE.search(text):
        values.append(float(m.group(2)) * 100_000)
    values += [float(m.group(1)) * 100_000 for m in _LPA_RE.finditer(text)]
    values += [float(m.group(1)) * 10_000_000 for m in _CRORE_RE.finditer(text)]
    values += [float(m.group(1).replace(",", "")) for m in _RUPEES_RE.finditer(text)]
    return int(max(values)) if values else None


def parse_experience_years(text: str) -> int | None:
    """Upper bound of the first 'X-Y years' requirement found."""
    m = _EXP_RE.search(text)
    if not m:
        return None
    return int(m.group(2) or m.group(1))


def _fetch_adzuna(settings: Settings, term: str) -> list[dict]:
    params = {
        "app_id": settings.adzuna_app_id,
        "app_key": settings.adzuna_app_key,
        "what": term,
        "where": "Bangalore",
        "results_per_page": 50,
        "max_days_old": 14,
        "sort_by": "date",
        "content-type": "application/json",
    }
    data = _http_get_json(f"https://api.adzuna.com/v1/api/jobs/in/search/1?{urllib.parse.urlencode(params)}")
    jobs = []
    for r in data.get("results", []):
        predicted = str(r.get("salary_is_predicted")) == "1"
        salary_max = None if predicted else (r.get("salary_max") or r.get("salary_min"))
        jobs.append({
            "title": r.get("title", ""),
            "company": (r.get("company") or {}).get("display_name", ""),
            "location": (r.get("location") or {}).get("display_name", ""),
            "url": _safe_url(r.get("redirect_url")),
            "description": r.get("description", ""),
            "salary_max": int(salary_max) if salary_max else None,
            "salary_text": "",
            "posted": r.get("created", ""),
            "source": "Adzuna",
        })
    return jobs


def _fetch_serpapi(settings: Settings, term: str) -> list[dict]:
    params = {
        "engine": "google_jobs",
        "q": f"{term} Bangalore",
        "location": "Bengaluru, Karnataka, India",
        "hl": "en",
        "chips": "date_posted:week",
        "api_key": settings.serpapi_key,
    }
    data = _http_get_json(f"https://serpapi.com/search.json?{urllib.parse.urlencode(params)}")
    jobs = []
    for r in data.get("jobs_results", []):
        ext = r.get("detected_extensions", {})
        salary_text = ext.get("salary", "")
        apply_links = r.get("apply_options") or []
        url = apply_links[0].get("link") if apply_links else r.get("share_link")
        jobs.append({
            "title": r.get("title", ""),
            "company": r.get("company_name", ""),
            "location": r.get("location", ""),
            "url": _safe_url(url),
            "description": r.get("description", ""),
            "salary_max": parse_salary_max_inr(salary_text) if salary_text else None,
            "salary_text": salary_text,
            "posted": ext.get("posted_at", ""),
            "source": "Google Jobs",
        })
    return jobs


def _enrich_and_filter(raw: dict, settings: Settings) -> dict | None:
    """Return a scored job, or None if it fails the hard filters."""
    title, desc, location = raw["title"], raw["description"], raw["location"].lower()
    text = f"{title}\n{desc}"

    if not any(c in location for c in settings.city_keywords):
        return None
    if not HR_TITLE.search(title) or JUNIOR_TITLE.search(title):
        return None

    salary = raw["salary_max"] or parse_salary_max_inr(text)
    if salary is not None and salary < settings.min_salary_inr:
        return None
    if salary is None and settings.require_salary:
        return None

    exp = parse_experience_years(text)
    if exp is not None and exp < settings.min_experience_years:
        return None

    score = 20
    score += 40 if salary is not None else 15
    score += 25 if exp is not None else 10
    score += 15 if SENIOR_TITLE.search(title) else 0

    if salary and not raw["salary_text"]:
        raw["salary_text"] = f"up to {salary / 100_000:.0f} LPA"

    job_id = hashlib.sha1(f"{title}|{raw['company']}|{location}".lower().encode()).hexdigest()
    return {
        "id": job_id,
        "title": title,
        "company": raw["company"],
        "location": raw["location"],
        "url": raw["url"],
        "source": raw["source"],
        "posted": raw["posted"],
        "salary_text": raw["salary_text"],
        "experience_years": exp,
        "score": score,
        "snippet": re.sub(r"\s+", " ", desc)[:300],
    }


def run_refresh() -> dict:
    """Fetch all sources, store unseen jobs, and email an alert for them."""
    settings = get_settings()
    errors: list[str] = []
    candidates: dict[str, dict] = {}

    fetchers = []
    if settings.adzuna_app_id and settings.adzuna_app_key:
        fetchers.append(_fetch_adzuna)
    if settings.serpapi_key:
        fetchers.append(_fetch_serpapi)

    for fetch in fetchers:
        for term in settings.search_terms:
            try:
                for raw in fetch(settings, term):
                    job = _enrich_and_filter(raw, settings)
                    if job and job["score"] >= settings.min_quality_score:
                        existing = candidates.get(job["id"])
                        if not existing or job["score"] > existing["score"]:
                            candidates[job["id"]] = job
            except Exception as exc:  # one failing source/term must not stop the rest
                errors.append(f"{fetch.__name__} '{term}': {type(exc).__name__}")

    new_jobs = job_store.add_new_jobs(list(candidates.values()))

    email_sent = False
    if new_jobs:
        try:
            alerts.send_new_jobs_email(settings, new_jobs)
            email_sent = settings.email_configured
        except Exception as exc:
            errors.append(f"email: {type(exc).__name__}")

    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "matched": len(candidates),
        "new": len(new_jobs),
        "email_sent": email_sent,
        "errors": errors,
    }
