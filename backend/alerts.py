"""Email digest for newly found jobs."""

import smtplib
from email.message import EmailMessage

from config import Settings


def send_new_jobs_email(settings: Settings, jobs: list[dict]) -> None:
    if not jobs or not settings.email_configured:
        return

    lines = []
    for job in sorted(jobs, key=lambda j: j["score"], reverse=True):
        salary = job["salary_text"] or "Salary not disclosed"
        lines.append(
            f"{job['title']} - {job['company']}\n"
            f"  {job['location']} | {salary} | Score {job['score']}\n"
            f"  {job['url']}\n"
        )

    msg = EmailMessage()
    msg["Subject"] = f"{len(jobs)} new HR job(s) in Bangalore"
    msg["From"] = settings.smtp_user
    msg["To"] = settings.alert_to
    msg.set_content("\n".join(lines))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)
