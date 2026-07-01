"""Email service for transactional emails.

Production: uses SMTP (any provider — SendGrid, SES, Mailgun, etc.).
Development: prints emails to console and saves to a log file.

Configuration via environment variables:
  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_USE_TLS
  FROM_EMAIL — the "from" address for outgoing emails
  APP_BASE_URL — the frontend base URL for building reset links
  APP_ENV — "production" uses SMTP, anything else uses console mode
"""

import os
import smtplib
import logging
from email.message import EmailMessage
from typing import Optional

logger = logging.getLogger(__name__)

# ── Configuration ───────────────────────────────────────────────────────────
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@mizan.app")
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:3000")
APP_ENV = os.getenv("APP_ENV", "development").lower()

_IS_SMTP_CONFIGURED = bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)


def _send_smtp(to_email: str, subject: str, html_body: str) -> bool:
    """Send email via SMTP. Returns True on success."""
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = FROM_EMAIL
        msg["To"] = to_email
        msg.set_content("Please enable HTML to view this email.")
        msg.add_alternative(html_body, subtype="html")

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            if SMTP_USE_TLS:
                server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

        logger.info(f"Email sent to {to_email}: {subject}")
        return True
    except Exception as e:
        logger.error(f"SMTP send failed to {to_email}: {e}")
        return False


def _send_console(to_email: str, subject: str, html_body: str) -> bool:
    """Dev mode: print email to console and log."""
    # Strip HTML tags for console display
    import re
    text = re.sub(r"<[^>]+>", "", html_body).strip()
    border = "=" * 60
    logger.info(f"\n{border}\n📧 TO: {to_email}\n📋 SUBJECT: {subject}\n\n{text}\n{border}")
    print(f"\n{border}")
    print(f"📧 TO: {to_email}")
    print(f"📋 SUBJECT: {subject}")
    print(f"\n{text}")
    print(f"{border}\n")
    return True


def send_email(to_email: str, subject: str, html_body: str) -> bool:
    """Send an email.

    Uses SMTP if configured and in production, otherwise falls back to console.
    This is fail-soft: returns True in dev console mode, and logs errors
    but returns False if SMTP fails in production (caller decides what to do).
    """
    if _IS_SMTP_CONFIGURED and APP_ENV == "production":
        return _send_smtp(to_email, subject, html_body)
    else:
        return _send_console(to_email, subject, html_body)


def send_password_reset_email(
    to_email: str, reset_token: str, user_name: Optional[str] = None
) -> bool:
    """Send a password reset email with a link containing the reset token."""
    reset_url = f"{APP_BASE_URL}/reset-password?token={reset_token}"
    name = user_name or "there"

    html = f"""\
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
  <div style="text-align: center; margin-bottom: 24px;">
    <h1 style="color: #0d7c45; margin: 0;">ميزان Mizan</h1>
  </div>
  <h2 style="color: #1a1a1a;">Password Reset Request</h2>
  <p style="color: #4a4a4a; font-size: 16px; line-height: 1.6;">
    Hello {name},
  </p>
  <p style="color: #4a4a4a; font-size: 16px; line-height: 1.6;">
    We received a request to reset your Mizan account password. Click the button below
    to choose a new password:
  </p>
  <div style="text-align: center; margin: 32px 0;">
    <a href="{reset_url}"
       style="background-color: #0d7c45; color: white; padding: 14px 36px;
              border-radius: 8px; text-decoration: none; font-size: 16px;
              font-weight: bold; display: inline-block;">
      Reset Password
    </a>
  </div>
  <p style="color: #4a4a4a; font-size: 16px; line-height: 1.6;">
    Or copy this link into your browser:
  </p>
  <p style="color: #0d7c45; word-break: break-all; font-size: 14px;">
    {reset_url}
  </p>
  <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 24px 0;">
  <p style="color: #888; font-size: 13px; line-height: 1.5;">
    This link expires in 1 hour. If you didn't request a password reset,
    you can safely ignore this email — your password will not be changed.
  </p>
  <p style="color: #888; font-size: 13px;">
    — Mizan Team
  </p>
</div>
"""
    return send_email(
        to_email,
        "Reset Your Mizan Password / إعادة تعيين كلمة المرور",
        html,
    )


def send_alert_notification_email(
    to_email: str,
    user_name: Optional[str],
    triggered_alerts: list[dict],
) -> bool:
    """Send an email notification when price alerts are triggered.

    Args:
        to_email: Recipient email address.
        user_name: Recipient name (or None).
        triggered_alerts: List of alert dicts with keys:
            ticker, name_en, condition, target_price, current_price.
    """
    name = user_name or "there"

    # Build alert rows
    rows_html = ""
    for a in triggered_alerts:
        stock_name = a.get("name_en") or a.get("ticker", "")
        condition_text = "above" if a.get("condition") == "above" else "below"
        condition_ar = "أعلى من" if a.get("condition") == "above" else "أقل من"
        target = a.get("target_price", 0)
        current = a.get("current_price", 0)
        rows_html += f"""
        <tr>
          <td style="padding: 10px 12px; border-bottom: 1px solid #eee;">
            <strong>{stock_name}</strong><br>
            <span style="color: #888; font-size: 13px;">{a.get('ticker', '')}</span>
          </td>
          <td style="padding: 10px 12px; border-bottom: 1px solid #eee; text-align: center;">
            {condition_text} / {condition_ar}
          </td>
          <td style="padding: 10px 12px; border-bottom: 1px solid #eee; text-align: right;">
            {target:,.2f}
          </td>
          <td style="padding: 10px 12px; border-bottom: 1px solid #eee; text-align: right; font-weight: bold; color: #0d7c45;">
            {current:,.2f}
          </td>
        </tr>
        """

    alert_count = len(triggered_alerts)
    plural = "s" if alert_count != 1 else ""

    html = f"""\
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
  <div style="text-align: center; margin-bottom: 24px;">
    <h1 style="color: #0d7c45; margin: 0;">ميزان Mizan</h1>
  </div>
  <h2 style="color: #1a1a1a;">🔔 {alert_count} Price Alert{plural} Triggered</h2>
  <p style="color: #4a4a4a; font-size: 16px; line-height: 1.6;">
    Hello {name},
  </p>
  <p style="color: #4a4a4a; font-size: 16px; line-height: 1.6;">
    The following price alert{plural} ha{"ve" if alert_count != 1 else "s"} been triggered:
  </p>

  <table style="width: 100%; border-collapse: collapse; margin: 24px 0; font-size: 14px;">
    <thead>
      <tr style="background-color: #f5f5f5;">
        <th style="padding: 10px 12px; text-align: left;">Stock</th>
        <th style="padding: 10px 12px; text-align: center;">Condition</th>
        <th style="padding: 10px 12px; text-align: right;">Target</th>
        <th style="padding: 10px 12px; text-align: right;">Current</th>
      </tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
  </table>

  <div style="text-align: center; margin: 32px 0;">
    <a href="{APP_BASE_URL}"
       style="background-color: #0d7c45; color: white; padding: 14px 36px;
              border-radius: 8px; text-decoration: none; font-size: 16px;
              font-weight: bold; display: inline-block;">
      View Alerts
    </a>
  </div>

  <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 24px 0;">
  <p style="color: #888; font-size: 13px;">
    — Mizan Team / فريق ميزان
  </p>
</div>
"""
    return send_email(
        to_email,
        f"Mizan: {alert_count} Alert{plural} Triggered / تنبيه{plural} مفعّل",
        html,
    )
