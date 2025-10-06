"""
Test email endpoint - for testing Resend integration.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from .database import get_session
from .models import User
from .routes.auth import get_current_user
from .config import settings
from pydantic import BaseModel, EmailStr
from .services.newsletter_service import send_test_newsletter
import resend
import logging

router = APIRouter(prefix="/test", tags=["testing"])
logger = logging.getLogger(__name__)


class SendTestEmailRequest(BaseModel):
    to_email: EmailStr
    subject: str = "Test Email from Pulse News"
    message: str = "This is a test email from your Pulse News Aggregator!"


@router.post("/send-email")
def send_test_email(
    request: SendTestEmailRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Send a test email using Resend.

    Requires authentication. Useful for testing email configuration.
    """
    # Check if Resend API key is configured
    if not settings.resend_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Resend API key not configured. Set RESEND_API_KEY in .env file"
        )

    # Initialize Resend
    resend.api_key = settings.resend_api_key

    try:
        # Send test email
        response = resend.Emails.send({
            "from": f"{settings.from_name} <{settings.from_email}>",
            "to": request.to_email,
            "subject": request.subject,
            "html": f"""
                <html>
                    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h1 style="color: #2563eb;">Test Email Successful! 🎉</h1>
                        <p style="font-size: 16px; line-height: 1.6;">
                            {request.message}
                        </p>
                        <hr style="border: 1px solid #e5e7eb; margin: 20px 0;">
                        <p style="color: #6b7280; font-size: 14px;">
                            <strong>Configuration Details:</strong><br>
                            From: {settings.from_name} &lt;{settings.from_email}&gt;<br>
                            To: {request.to_email}<br>
                            Environment: {settings.environment}<br>
                            Sent by: {current_user.email}
                        </p>
                        <p style="color: #6b7280; font-size: 14px; margin-top: 20px;">
                            This email was sent via Resend API as a test. Your email configuration is working correctly!
                        </p>
                    </body>
                </html>
            """
        })

        logger.info(f"Test email sent to {request.to_email} by {current_user.email}")

        return {
            "success": True,
            "message": f"Test email sent successfully to {request.to_email}",
            "resend_response": response,
            "from": f"{settings.from_name} <{settings.from_email}>",
            "to": request.to_email
        }

    except Exception as e:
        logger.error(f"Failed to send test email: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}"
        )


class SendTestNewsletterRequest(BaseModel):
    to_email: EmailStr


@router.post("/send-newsletter")
def send_test_newsletter_route(
    request: SendTestNewsletterRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Send a test newsletter to the specified email address.
    Requires authentication.
    """
    if not settings.resend_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Resend API key not configured. Set RESEND_API_KEY in .env file"
        )

    success = send_test_newsletter(request.to_email)
    if success:
        return {"success": True, "message": f"Test newsletter sent to {request.to_email}"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to send test newsletter to {request.to_email}"
        )


@router.get("/email-config")
def get_email_config(current_user: User = Depends(get_current_user)):
    """
    Get current email configuration (without exposing API keys).
    """
    return {
        "resend_configured": bool(settings.resend_api_key),
        "from_email": settings.from_email,
        "from_name": settings.from_name,
        "environment": settings.environment,
        "api_key_set": "Yes" if settings.resend_api_key else "No (set RESEND_API_KEY in .env)",
        "api_key_preview": f"{settings.resend_api_key[:10]}..." if settings.resend_api_key else None
    }
