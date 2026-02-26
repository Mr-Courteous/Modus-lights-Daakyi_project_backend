"""
SendGrid Email Service for User Onboarding Notifications
Handles secure token-based password reset links and user notifications
"""

import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import secrets
import jwt
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Content, To
from database import DatabaseOperations
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class SendGridService:
    """Service for handling SendGrid email notifications"""
    
    def __init__(self):
        self.api_key = os.getenv('SENDGRID_API_KEY')
        self.from_email = os.getenv('SENDGRID_FROM_EMAIL')
        
        if not self.api_key:
            raise ValueError("SENDGRID_API_KEY environment variable is required")
        if not self.from_email:
            raise ValueError("SENDGRID_FROM_EMAIL environment variable is required")
            
        self.client = SendGridAPIClient(api_key=self.api_key)
        
        # JWT secret for password reset tokens (use a secure secret in production)
        self.jwt_secret = os.getenv('JWT_SECRET', 'daakyi-secure-jwt-secret-2025')
    
    async def send_user_onboarding_email(
        self, 
        user_email: str, 
        user_name: str, 
        organization_name: str,
        temporary_password: str
    ) -> Dict[str, Any]:
        """
        Send onboarding email with secure password reset link to newly created user
        
        Args:
            user_email: Email of the new user
            user_name: Full name of the new user
            organization_name: Name of the user's organization
            temporary_password: Temporary password for the user
            
        Returns:
            Dict with success status and details
        """
        try:
            # Generate secure password reset token (24-hour expiry)
            reset_token = self._generate_password_reset_token(user_email)
            
            # Store token in database for validation
            await self._store_reset_token(user_email, reset_token)
            
            # Create password reset URL - PRODUCTION ENVIRONMENT ONLY
            frontend_url = os.getenv('FRONTEND_URL')
            if not frontend_url:
                logger.error("FRONTEND_URL environment variable not set - required for production email links")
                raise ValueError("FRONTEND_URL environment variable is required for production password reset emails")
            
            reset_url = f"{frontend_url}/reset-password?token={reset_token}"
            
            logger.info(f"Generated password reset URL for {user_email}: {frontend_url}/reset-password (production environment)")
            
            # Email content
            subject = f"Welcome to DAAKYI CompaaS - Account Created"
            
            html_content = self._create_onboarding_email_template(
                user_email=user_email,
                user_name=user_name,
                organization_name=organization_name,
                temporary_password=temporary_password,
                reset_url=reset_url
            )
            
            text_content = self._create_onboarding_email_text(
                user_email=user_email,
                user_name=user_name,
                organization_name=organization_name,
                temporary_password=temporary_password,
                reset_url=reset_url
            )
            
            # Create email
            message = Mail(
                from_email=self.from_email,
                to_emails=To(email=user_email, name=user_name),
                subject=subject,
                html_content=Content("text/html", html_content),
                plain_text_content=Content("text/plain", text_content)
            )
            
            # Send email
            response = self.client.send(message)
            
            logger.info(f"Onboarding email sent successfully to {user_email}. Status: {response.status_code}")
            
            return {
                "success": True,
                "status_code": response.status_code,
                "message": "Onboarding email sent successfully",
                "reset_token_expires_in": "24 hours"
            }
            
        except Exception as e:
            logger.error(f"Failed to send onboarding email to {user_email}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to send onboarding email"
            }
    
    def _generate_password_reset_token(self, user_email: str) -> str:
        """Generate JWT token for password reset with 24-hour expiry"""
        payload = {
            "email": user_email,
            "purpose": "password_reset",
            "issued_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            "nonce": secrets.token_hex(16)  # Additional security
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")
        return token
    
    async def _store_reset_token(self, user_email: str, reset_token: str):
        """Store password reset token in database for validation"""
        token_data = {
            "email": user_email,
            "token": reset_token,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=24),
            "used": False,
            "purpose": "password_reset"
        }
        
        await DatabaseOperations.insert_one("password_reset_tokens", token_data)
    
    async def validate_reset_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate password reset token and return user email if valid"""
        try:
            # Check token in database
            token_data = await DatabaseOperations.find_one(
                "password_reset_tokens",
                {"token": token, "used": False}
            )
            
            if not token_data:
                return None
                
            # Check if token has expired
            if datetime.utcnow() > token_data["expires_at"]:
                return None
                
            # Verify JWT token
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            
            if payload["email"] != token_data["email"]:
                return None
                
            return {
                "email": payload["email"],
                "token_data": token_data
            }
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception as e:
            logger.error(f"Error validating reset token: {str(e)}")
            return None
    
    async def mark_token_as_used(self, token: str):
        """Mark password reset token as used to prevent reuse"""
        await DatabaseOperations.update_one(
            "password_reset_tokens",
            {"token": token},
            {"used": True, "used_at": datetime.utcnow()}
        )
    
    def _create_onboarding_email_template(
        self, 
        user_email: str,
        user_name: str, 
        organization_name: str, 
        temporary_password: str,
        reset_url: str
    ) -> str:
        """Create HTML email template for user onboarding with DAAKYI branding"""
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <meta http-equiv="X-UA-Compatible" content="IE=edge">
            <title>Welcome to DAAKYI CompaaS</title>
            <!--[if mso]>
            <noscript>
                <xml>
                    <o:OfficeDocumentSettings>
                        <o:PixelsPerInch>96</o:PixelsPerInch>
                    </o:OfficeDocumentSettings>
                </xml>
            </noscript>
            <![endif]-->
            <style type="text/css">
                /* Reset styles for email clients */
                body, table, td, p, a, li, blockquote {{
                    -webkit-text-size-adjust: 100%;
                    -ms-text-size-adjust: 100%;
                }}
                table, td {{ border-collapse: collapse; mso-table-lspace: 0pt; mso-table-rspace: 0pt; }}
                img {{
                    -ms-interpolation-mode: bicubic;
                    max-width: 100%;
                    height: auto;
                    display: block;
                }}
                
                /* DAAKYI Brand Colors */
                .brand-primary {{ background-color: #1e3a8a; }} /* DAAKYI Blue */
                .brand-secondary {{ background-color: #3b82f6; }} /* Light Blue */
                .brand-accent {{ background-color: #10b981; }} /* DAAKYI Green */
                .brand-dark {{ background-color: #1f2937; }} /* Dark Gray */
                
                /* Responsive styles */
                @media only screen and (max-width: 600px) {{
                    .container {{ width: 100% !important; }}
                    .mobile-center {{ text-align: center !important; }}
                    .mobile-padding {{ padding: 20px !important; }}
                }}
            </style>
        </head>
        <body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
            <!-- Wrapper table for Outlook -->
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                <tr>
                    <td style="padding: 20px 0;">
                        <!-- Main container -->
                        <table class="container" role="presentation" cellspacing="0" cellpadding="0" border="0" 
                               style="width: 600px; margin: 0 auto; background-color: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
                            
                            <!-- DAAKYI Header with Branding -->
                            <tr>
                                <td style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 50%, #10b981 100%); padding: 0; text-align: center;">
                                    <!-- Logo and Branding Section -->
                                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                        <tr>
                                            <td style="padding: 40px 20px 30px; text-align: center;">
                                                <!-- DAAKYI Logo Placeholder - Replace with actual logo when available -->
                                                <div style="width: 80px; height: 80px; background: rgba(255,255,255,0.2); border-radius: 50%; margin: 0 auto 20px; 
                                                           display: flex; align-items: center; justify-content: center; border: 2px solid rgba(255,255,255,0.3);">
                                                    <span style="color: white; font-size: 32px; font-weight: bold;">D</span>
                                                </div>
                                                <h1 style="margin: 0; font-size: 32px; font-weight: bold; color: white; letter-spacing: -0.5px;">
                                                    DAAKYI CompaaS
                                                </h1>
                                                <p style="margin: 8px 0 0 0; font-size: 16px; color: rgba(255,255,255,0.9); font-weight: 500;">
                                                    Cybersecurity Compliance Made Simple
                                                </p>
                                                <div style="width: 60px; height: 3px; background: rgba(255,255,255,0.4); margin: 20px auto 0; border-radius: 2px;"></div>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            
                            <!-- Main Content -->
                            <tr>
                                <td style="padding: 40px 40px 30px;" class="mobile-padding">
                                    <h2 style="color: #1f2937; margin: 0 0 24px; font-size: 28px; font-weight: 600; line-height: 1.3;">
                                        Welcome, {user_name}! 👋
                                    </h2>
                                    
                                    <p style="color: #4b5563; margin: 0 0 24px; font-size: 16px; line-height: 1.6;">
                                        Your administrator has created a new account for you on the DAAKYI CompaaS platform. 
                                        You're now part of <strong style="color: #1e3a8a;">{organization_name}</strong>'s 
                                        cybersecurity compliance team.
                                    </p>
                                    
                                    <!-- Account Details Card -->
                                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" 
                                           style="background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); border-radius: 12px; margin: 30px 0; border: 1px solid #e5e7eb;">
                                        <tr>
                                            <td style="padding: 24px;">
                                                <h3 style="margin: 0 0 20px; color: #1f2937; font-size: 18px; font-weight: 600; display: flex; align-items: center;">
                                                    🔑 Your Account Details
                                                </h3>
                                                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                                    <tr>
                                                        <td style="padding: 8px 0; color: #6b7280; font-size: 14px; font-weight: 500; width: 30%;">Email:</td>
                                                        <td style="padding: 8px 0; color: #1f2937; font-size: 14px; font-weight: 600;">{user_email}</td>
                                                    </tr>
                                                    <tr>
                                                        <td style="padding: 8px 0; color: #6b7280; font-size: 14px; font-weight: 500;">Temporary Password:</td>
                                                        <td style="padding: 8px 0;">
                                                            <code style="background: #f3f4f6; padding: 4px 8px; border-radius: 4px; font-family: 'Courier New', monospace; 
                                                                        font-size: 14px; color: #1f2937; border: 1px solid #d1d5db;">{temporary_password}</code>
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td style="padding: 8px 0; color: #6b7280; font-size: 14px; font-weight: 500;">Organization:</td>
                                                        <td style="padding: 8px 0; color: #1f2937; font-size: 14px; font-weight: 600;">{organization_name}</td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                    </table>
                                    
                                    <!-- Security Warning -->
                                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" 
                                           style="background: #fef3c7; border-radius: 8px; border-left: 4px solid #f59e0b; margin: 24px 0;">
                                        <tr>
                                            <td style="padding: 16px 20px;">
                                                <p style="margin: 0; color: #92400e; font-size: 14px; font-weight: 600; display: flex; align-items: center;">
                                                    🔐 Security Notice
                                                </p>
                                                <p style="margin: 8px 0 0; color: #92400e; font-size: 14px; line-height: 1.5;">
                                                    For security reasons, please set a new password immediately using the secure link below. 
                                                    This temporary password should only be used for your initial setup.
                                                </p>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            
                            <!-- Call to Action Section -->
                            <tr>
                                <td style="padding: 0 40px 40px;" class="mobile-padding">
                                    <div style="text-align: center; margin: 0 0 30px;">
                                        <!-- Primary CTA Button -->
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin: 0 auto;">
                                            <tr>
                                                <td style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); border-radius: 8px; box-shadow: 0 4px 12px rgba(30,58,138,0.4);">
                                                    <a href="{reset_url}" 
                                                       style="display: inline-block; padding: 16px 32px; color: white; text-decoration: none; 
                                                              font-size: 16px; font-weight: 600; letter-spacing: 0.5px;">
                                                        🚀 Set Your New Password
                                                    </a>
                                                </td>
                                            </tr>
                                        </table>
                                        <p style="margin: 12px 0 0; font-size: 12px; color: #9ca3af;">
                                            This secure link expires in 24 hours and can only be used once.
                                        </p>
                                    </div>
                                    
                                    <!-- Getting Started Guide -->
                                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" 
                                           style="background: white; border: 2px solid #e5e7eb; border-radius: 12px; margin: 30px 0;">
                                        <tr>
                                            <td style="padding: 24px;">
                                                <h3 style="margin: 0 0 20px; color: #1f2937; font-size: 18px; font-weight: 600;">
                                                    🎯 What's Next?
                                                </h3>
                                                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                                    <tr>
                                                        <td style="padding: 6px 0; color: #4b5563; font-size: 14px; line-height: 1.6;">
                                                            <strong>1.</strong> Click the "Set Your New Password" button above
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td style="padding: 6px 0; color: #4b5563; font-size: 14px; line-height: 1.6;">
                                                            <strong>2.</strong> Create a strong, secure password (8+ characters, mixed case, numbers, symbols)
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td style="padding: 6px 0; color: #4b5563; font-size: 14px; line-height: 1.6;">
                                                            <strong>3.</strong> Log in to your DAAKYI CompaaS dashboard
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td style="padding: 6px 0; color: #4b5563; font-size: 14px; line-height: 1.6;">
                                                            <strong>4.</strong> Complete your profile setup and explore your workspace
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td style="padding: 6px 0; color: #4b5563; font-size: 14px; line-height: 1.6;">
                                                            <strong>5.</strong> Start collaborating on cybersecurity compliance assessments
                                                        </td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            
                            <!-- DAAKYI Footer with Branding -->
                            <tr>
                                <td style="background: #1f2937; padding: 30px 40px; text-align: center;" class="mobile-padding">
                                    <!-- Brand Footer -->
                                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                        <tr>
                                            <td style="text-align: center; padding-bottom: 20px;">
                                                <div style="width: 40px; height: 40px; background: #3b82f6; border-radius: 50%; margin: 0 auto 12px; 
                                                           display: flex; align-items: center; justify-content: center;">
                                                    <span style="color: white; font-size: 16px; font-weight: bold;">D</span>
                                                </div>
                                                <h4 style="margin: 0; color: white; font-size: 16px; font-weight: 600;">DAAKYI CompaaS</h4>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="text-align: center; padding: 0 0 20px;">
                                                <p style="margin: 0; color: #9ca3af; font-size: 14px; line-height: 1.6;">
                                                    Making cybersecurity compliance simple, efficient, and collaborative.<br>
                                                    Empowering organizations to achieve and maintain regulatory compliance.
                                                </p>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="text-align: center; border-top: 1px solid #374151; padding-top: 20px;">
                                                <p style="margin: 0; color: #6b7280; font-size: 12px;">
                                                    Questions? Contact your administrator or our support team.<br>
                                                    <span style="color: #9ca3af;">© 2025 DAAKYI CompaaS. All rights reserved.</span>
                                                </p>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
    
    def _create_onboarding_email_text(
        self, 
        user_email: str,
        user_name: str, 
        organization_name: str, 
        temporary_password: str,
        reset_url: str
    ) -> str:
        """Create plain text email for user onboarding with DAAKYI branding"""
        return f"""
═══════════════════════════════════════════════════════════════════
                    DAAKYI CompaaS
         🚀 Cybersecurity Compliance Made Simple 🚀
═══════════════════════════════════════════════════════════════════

Welcome to DAAKYI CompaaS, {user_name}! 👋

Your administrator has created a new account for you on the DAAKYI 
CompaaS platform. You're now part of {organization_name}'s 
cybersecurity compliance team.

═══════════════════════════════════════════════════════════════════
🔑 YOUR ACCOUNT DETAILS
═══════════════════════════════════════════════════════════════════

Email Address: {user_email}
Temporary Password: {temporary_password}
Organization: {organization_name}

🔐 SECURITY NOTICE:
For security reasons, please set a new password immediately using 
the secure link below. This temporary password should only be used 
for your initial setup.

═══════════════════════════════════════════════════════════════════
🚀 SET YOUR NEW PASSWORD
═══════════════════════════════════════════════════════════════════

Click or copy this secure link to reset your password:
{reset_url}

⚠️  IMPORTANT: This link expires in 24 hours and can only be used once.

═══════════════════════════════════════════════════════════════════
🎯 WHAT'S NEXT?
═══════════════════════════════════════════════════════════════════

1. Click the password reset link above
2. Create a strong, secure password 
   (8+ characters, mixed case, numbers, symbols)
3. Log in to your DAAKYI CompaaS dashboard
4. Complete your profile setup and explore your workspace
5. Start collaborating on cybersecurity compliance assessments

═══════════════════════════════════════════════════════════════════
📞 NEED HELP?
═══════════════════════════════════════════════════════════════════

Questions? Contact your administrator or our support team.
We're here to make your compliance journey as smooth as possible!

═══════════════════════════════════════════════════════════════════
                    DAAKYI CompaaS Platform
           Making Cybersecurity Compliance Simple

    🔒 Secure • 🤝 Collaborative • ⚡ Efficient • 📊 Compliant

            © 2025 DAAKYI CompaaS. All rights reserved.
═══════════════════════════════════════════════════════════════════

        """

# Lazy initialization of service instance
def get_sendgrid_service():
    """Get SendGrid service instance with lazy initialization"""
    return SendGridService()