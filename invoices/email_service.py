"""Brevo (https://www.brevo.com) transactional email over HTTPS.

Replaces the previous raw SMTP setup (smtp.gmail.com:587 + a Gmail app
password) -- Render's free tier blocks outbound SMTP entirely, so that
send silently died in production every time (and worse: since the old
code called `.send()` with no error handling, an SMTP failure raised an
uncaught exception in the middle of CreateInvoiceView.post(), meaning a
failed email could 500 the *entire invoice creation request* even though
the invoice had already been saved to the database).

Degrades gracefully with no credentials configured: logs instead of
sending, and NEVER raises -- a failed/unconfigured send must not break
invoice creation, which is the actual business-critical action here.
"""

import base64
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def send_invoice_email(invoice, pdf_bytes: bytes) -> bool:
    """Sends the invoice PDF to the client. Returns True if actually sent,
    False otherwise (never raises)."""
    if not pdf_bytes:
        logger.warning("[invoice email] no-op -- PDF generation failed for invoice %s", invoice.id)
        return False

    if not settings.BREVO_API_KEY or not settings.BREVO_SENDER_EMAIL:
        logger.info(
            "[invoice email] no-op -- BREVO_API_KEY/BREVO_SENDER_EMAIL not set. "
            "Would have emailed invoice %s to %s.", invoice.id, invoice.client_email,
        )
        return False

    payload = {
        "sender": {"email": settings.BREVO_SENDER_EMAIL, "name": settings.COMPANY_NAME},
        "to": [{"email": invoice.client_email, "name": invoice.client_name}],
        "subject": f"Invoice {invoice.id} from {settings.COMPANY_NAME}",
        "htmlContent": (
            f"<p>Dear {invoice.client_name},</p>"
            f"<p>Please find your invoice (#{invoice.id}) attached.</p>"
            f"<p>Total: ${invoice.total}</p>"
            f"<p>— {settings.COMPANY_NAME}</p>"
        ),
        "attachment": [{
            "content": base64.b64encode(pdf_bytes).decode("ascii"),
            "name": f"invoice_{invoice.id}.pdf",
        }],
    }

    try:
        resp = requests.post(
            BREVO_API_URL,
            headers={"api-key": settings.BREVO_API_KEY, "Content-Type": "application/json"},
            json=payload, timeout=10,
        )
        resp.raise_for_status()
        logger.info("[invoice email] sent invoice %s to %s", invoice.id, invoice.client_email)
        return True
    except requests.exceptions.RequestException as exc:
        # Best-effort: the invoice itself is already saved regardless of
        # whether the email goes out. A failed send should never surface
        # as a 500 to whoever's creating the invoice.
        logger.error("[invoice email] failed to send invoice %s: %s", invoice.id, exc)
        return False
