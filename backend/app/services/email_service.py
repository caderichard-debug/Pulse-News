"""
Email service for sending transactional emails (password reset, verification, etc.)
"""

import os
import logging
import resend
from jinja2 import Environment, FileSystemLoader
from ..config import settings

logger = logging.getLogger(__name__)

# Initialize Resend
if settings.resend_api_key:
    resend.api_key = settings.resend_api_key
else:
    logger.warning("RESEND_API_KEY not set - email sending will be disabled")

# Initialize Jinja2 template environment
template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
template_env = Environment(loader=FileSystemLoader(template_dir))


def send_password_reset_email(email: str, user_name: str, reset_token: str) -> bool:
    """
    Send password reset email to user.

    Args:
        email: User's email address
        user_name: User's name (or email if name not set)
        reset_token: Password reset token

    Returns:
        True if email sent successfully, False otherwise
    """
    if not settings.resend_api_key:
        logger.error("Resend API key not configured - cannot send email")
        return False

    try:
        # Get frontend URL from environment or default
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        reset_link = f"{frontend_url}/reset-password?token={reset_token}"

        # Load and render template
        template = template_env.get_template("password_reset.html")
        html_content = template.render(
            user_name=user_name,
            reset_link=reset_link
        )

        # Send email via Resend
        params = {
            "from": f"{settings.from_name} <{settings.from_email}>",
            "to": [email],
            "subject": "Reset Your Pulse Password",
            "html": html_content
        }

        response = resend.Emails.send(params)

        logger.info(f"Password reset email sent to {email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send password reset email to {email}: {str(e)}")
        return False


def send_verification_email(email: str, user_name: str, verification_token: str) -> bool:
    """
    Send email verification email to user.

    Args:
        email: User's email address
        user_name: User's name (or email if name not set)
        verification_token: Email verification token

    Returns:
        True if email sent successfully, False otherwise
    """
    if not settings.resend_api_key:
        logger.error("Resend API key not configured - cannot send email")
        return False

    try:
        # Get frontend URL from environment or default
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        verification_link = f"{frontend_url}/verify-email?token={verification_token}"

        # For now, send a simple HTML email (can create template later)
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Verify Your Email - Pulse</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
                <h1 style="margin: 0;">Welcome to Pulse!</h1>
            </div>
            <div style="background-color: #fff; padding: 30px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 8px 8px;">
                <p>Hello {user_name},</p>
                <p>Thank you for signing up for Pulse! Please verify your email address by clicking the button below:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_link}" style="display: inline-block; padding: 14px 32px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; border-radius: 6px; font-weight: 600;">Verify Email</a>
                </div>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; background-color: #f4f4f4; padding: 10px; border-radius: 4px;">{verification_link}</p>
                <p>This link will expire in 24 hours.</p>
                <p>If you didn't create an account, you can safely ignore this email.</p>
            </div>
        </body>
        </html>
        """

        # Send email via Resend
        params = {
            "from": f"{settings.from_name} <{settings.from_email}>",
            "to": [email],
            "subject": "Verify Your Pulse Email Address",
            "html": html_content
        }

        response = resend.Emails.send(params)

        logger.info(f"Verification email sent to {email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send verification email to {email}: {str(e)}")
        return False
