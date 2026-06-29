import logging

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

SENDGRID_API = "https://api.sendgrid.com/v3/mail/send"


async def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """Send an email via SendGrid."""
    if not settings.sendgrid_api_key:
        logger.warning("SendGrid API key not configured, skipping email")
        return False

    payload = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": settings.sendgrid_from_email, "name": settings.app_name},
        "subject": subject,
        "content": [{"type": "text/html", "value": html_content}],
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                SENDGRID_API,
                headers={
                    "Authorization": f"Bearer {settings.sendgrid_api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            if resp.status_code in (200, 201, 202):
                return True
            logger.error(f"SendGrid error {resp.status_code}: {resp.text}")
            return False
    except Exception as e:
        logger.error(f"Email send error: {e}")
        return False


def build_grant_alert_email(grants: list[dict], keywords: list[str]) -> str:
    """Build HTML email for grant alerts."""
    grant_rows = ""
    for g in grants:
        grant_rows += f"""
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #eee;">
                <strong>{g.get('title', '')}</strong><br>
                <small>{g.get('agency', '')} | Deadline: {g.get('deadline', 'N/A')}</small><br>
                <small>{g.get('award_amount', '')}</small>
            </td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2563eb;">GrantAssist AI - New Grant Matches</h2>
        <p>We found new grants matching your keywords: <strong>{', '.join(keywords)}</strong></p>
        <table style="width: 100%; border-collapse: collapse;">
            {grant_rows}
        </table>
        <p style="margin-top: 20px; color: #666; font-size: 12px;">
            You received this email because you subscribed to grant alerts on GrantAssist AI.
        </p>
    </body>
    </html>
    """


def build_deadline_reminder_email(grant: dict, days_until: int) -> str:
    """Build HTML email for deadline reminders."""
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #dc2626;">Deadline Reminder</h2>
        <p>Your saved grant <strong>{grant.get('title', '')}</strong> has a deadline
        in <strong>{days_until} day(s)</strong>.</p>
        <p>
            <strong>Agency:</strong> {grant.get('agency', '')}<br>
            <strong>Deadline:</strong> {grant.get('deadline', '')}<br>
            <strong>Amount:</strong> {grant.get('award_amount', '')}
        </p>
        <p>Log in to GrantAssist AI to continue working on your application.</p>
    </body>
    </html>
    """
