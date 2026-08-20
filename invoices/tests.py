from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings

from . import email_service
from .models import Invoice


class EmailServiceTests(TestCase):
    """The previous SMTP version called EmailMessage.send() with no error
    handling -- an SMTP failure (guaranteed on Render's free tier, which
    blocks outbound SMTP) raised uncaught, meaning a failed email could
    500 the entire "create invoice" request even though the invoice had
    already been saved. send_invoice_email() must NEVER raise."""

    def setUp(self):
        self.invoice = Invoice.objects.create(
            client_name="Test Client", client_email="client@example.com", total=100,
        )

    @override_settings(BREVO_API_KEY="", BREVO_SENDER_EMAIL="")
    def test_noop_when_not_configured_does_not_raise(self):
        result = email_service.send_invoice_email(self.invoice, b"%PDF-fake-content")
        self.assertFalse(result)

    def test_noop_when_pdf_generation_failed(self):
        result = email_service.send_invoice_email(self.invoice, None)
        self.assertFalse(result)

    @override_settings(BREVO_API_KEY="fake-key", BREVO_SENDER_EMAIL="sender@example.com")
    def test_network_failure_does_not_raise(self):
        import requests
        with patch("invoices.email_service.requests.post",
                    side_effect=requests.exceptions.ConnectionError("network down")):
            result = email_service.send_invoice_email(self.invoice, b"%PDF-fake-content")
        self.assertFalse(result)

    @override_settings(BREVO_API_KEY="fake-key", BREVO_SENDER_EMAIL="sender@example.com",
                        COMPANY_NAME="Acme Landscaping")
    def test_successful_send_calls_brevo_with_attachment(self):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        with patch("invoices.email_service.requests.post", return_value=mock_response) as mock_post:
            result = email_service.send_invoice_email(self.invoice, b"%PDF-fake-content")
        self.assertTrue(result)
        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs["json"]
        self.assertEqual(payload["sender"]["email"], "sender@example.com")
        self.assertEqual(payload["sender"]["name"], "Acme Landscaping")
        self.assertEqual(payload["to"][0]["email"], "client@example.com")
        self.assertIn("attachment", payload)


class BrandingContextProcessorTests(TestCase):
    """COMPANY_NAME must be configurable per client instead of hardcoded
    -- this is the one customization point the app currently has."""

    def setUp(self):
        self.user = User.objects.create_user("staffuser", password="pw12345!")

    @override_settings(COMPANY_NAME="Acme Landscaping")
    def test_login_page_shows_configured_company_name(self):
        resp = self.client.get("/login/")
        self.assertContains(resp, "Acme Landscaping")

    @override_settings(COMPANY_NAME="Acme Landscaping")
    def test_invoice_list_shows_configured_company_name(self):
        self.client.force_login(self.user)
        resp = self.client.get("/invoices/")
        self.assertContains(resp, "Acme Landscaping Invoices")


class GenerateInvoicePdfTests(TestCase):
    """generate_invoice_pdf() renders via get_template().render() with no
    request object, so template context processors (including branding)
    never run automatically -- company_name has to be passed explicitly,
    or the PDF silently reverts to blank/hardcoded branding."""

    @override_settings(COMPANY_NAME="Acme Landscaping")
    def test_pdf_includes_configured_company_name(self):
        from .views import generate_invoice_pdf
        invoice = Invoice.objects.create(client_name="Test Client", client_email="c@example.com", total=50)
        pdf_bytes = generate_invoice_pdf(invoice)
        self.assertIsNotNone(pdf_bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
