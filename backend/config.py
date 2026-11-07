"""Settings loaded from environment variables, with an optional backend/.env file."""

import os
from dataclasses import dataclass

_ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")


def _load_env_file() -> None:
    if not os.path.exists(_ENV_PATH):
        return
    with open(_ENV_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env_file()


@dataclass(frozen=True)
class Settings:
    adzuna_app_id: str
    adzuna_app_key: str
    serpapi_key: str
    search_terms: list[str]
    city_keywords: tuple[str, ...]
    min_experience_years: int
    min_salary_inr: int
    require_salary: bool
    min_quality_score: int
    poll_minutes: int
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    alert_to: str

    @property
    def has_sources(self) -> bool:
        return bool((self.adzuna_app_id and self.adzuna_app_key) or self.serpapi_key)

    @property
    def email_configured(self) -> bool:
        return bool(self.smtp_host and self.smtp_user and self.smtp_password and self.alert_to)


def get_settings() -> Settings:
    env = os.environ.get
    terms = [t.strip() for t in env("JOB_SEARCH_TERMS", "HR Manager,HR Business Partner,Talent Acquisition,Head of HR,People Operations").split(",") if t.strip()]
    return Settings(
        adzuna_app_id=env("ADZUNA_APP_ID", ""),
        adzuna_app_key=env("ADZUNA_APP_KEY", ""),
        serpapi_key=env("SERPAPI_KEY", ""),
        search_terms=terms,
        city_keywords=("bangalore", "bengaluru"),
        min_experience_years=int(env("MIN_EXPERIENCE_YEARS", "3")),
        min_salary_inr=int(env("MIN_SALARY_LPA", "35")) * 100_000,
        require_salary=env("REQUIRE_SALARY", "false").lower() == "true",
        min_quality_score=int(env("MIN_QUALITY_SCORE", "50")),
        poll_minutes=max(15, int(env("POLL_MINUTES", "60"))),
        smtp_host=env("SMTP_HOST", ""),
        smtp_port=int(env("SMTP_PORT", "587")),
        smtp_user=env("SMTP_USER", ""),
        smtp_password=env("SMTP_PASSWORD", ""),
        alert_to=env("ALERT_EMAIL_TO", ""),
    )
