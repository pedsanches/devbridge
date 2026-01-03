"""
Email Service.

Wrapper for Resend email API to send magic links.
"""

import resend

from app.core.config import settings


def send_magic_link_email(
    to_email: str,
    token: str,
    expires_in_minutes: int = 15,
) -> bool:
    """
    Send a magic link authentication email.

    Args:
        to_email: Recipient email address.
        token: Magic link token.
        expires_in_minutes: Token expiration time.

    Returns:
        True if email was sent successfully, False otherwise.
    """
    if not settings.RESEND_API_KEY:
        # Development mode: log instead of sending
        print(
            f"[DEV MODE] Magic link for {to_email}: {settings.FRONTEND_URL}/auth/verify?token={token}"
        )
        return True

    resend.api_key = settings.RESEND_API_KEY

    verify_url = f"{settings.FRONTEND_URL}/auth/verify?token={token}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f5f5f7; padding: 40px 20px;">
        <div style="max-width: 480px; margin: 0 auto; background: white; border-radius: 12px; padding: 40px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
            <h1 style="color: #1d1d1f; font-size: 24px; font-weight: 600; margin: 0 0 24px;">
                Acesse o DevBridge
            </h1>
            <p style="color: #515154; font-size: 16px; line-height: 1.5; margin: 0 0 24px;">
                Clique no botão abaixo para acessar sua conta. Este link expira em {expires_in_minutes} minutos.
            </p>
            <a href="{verify_url}"
               style="display: inline-block; background: #0071E3; color: white; text-decoration: none; padding: 14px 28px; border-radius: 8px; font-weight: 500; font-size: 16px;">
                Acessar DevBridge
            </a>
            <p style="color: #86868b; font-size: 14px; margin: 32px 0 0; line-height: 1.5;">
                Se você não solicitou este email, pode ignorá-lo com segurança.
            </p>
        </div>
    </body>
    </html>
    """

    try:
        resend.Emails.send(
            {
                "from": settings.EMAIL_FROM,
                "to": [to_email],
                "subject": "Seu link de acesso ao DevBridge",
                "html": html_content,
            }
        )
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        return False
