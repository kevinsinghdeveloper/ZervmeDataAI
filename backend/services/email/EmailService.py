import os
import boto3
from typing import Optional, List
from abstractions.IServiceManagerBase import IServiceManagerBase
from dotenv import load_dotenv

load_dotenv()


class EmailService(IServiceManagerBase):
    """AWS SES email sending service."""

    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self._ses_client = None
        self._from_email = None
        self._from_name = None
        self._initialized = False

    def initialize(self):
        """Initialize SES client and sender address from config or environment variables."""
        region = self._config.get("aws_region", os.getenv("AWS_REGION_NAME", "us-east-1"))
        self._ses_client = boto3.client("ses", region_name=region)
        self._from_email = self._config.get("from_email", os.getenv("SES_FROM_EMAIL", ""))
        self._from_name = self._config.get("from_name", os.getenv("FROM_NAME", "Zerve My Time"))
        self._initialized = True

    def send_email(self, to_email: str, subject: str, html_body: str,
                   text_body: Optional[str] = None, cc: Optional[List[str]] = None,
                   bcc: Optional[List[str]] = None) -> bool:
        if not self._initialized:
            self.initialize()

        if not self._from_email:
            print("Warning: SES_FROM_EMAIL not configured. Email not sent.")
            return False

        try:
            source = f"{self._from_name} <{self._from_email}>" if self._from_name else self._from_email

            destination = {"ToAddresses": [to_email]}
            if cc:
                destination["CcAddresses"] = cc
            if bcc:
                destination["BccAddresses"] = bcc

            body = {"Html": {"Charset": "UTF-8", "Data": html_body}}
            if text_body:
                body["Text"] = {"Charset": "UTF-8", "Data": text_body}

            self._ses_client.send_email(
                Source=source,
                Destination=destination,
                Message={
                    "Subject": {"Charset": "UTF-8", "Data": subject},
                    "Body": body,
                },
            )
            return True
        except Exception as e:
            print(f"Failed to send email via SES: {e}")
            return False

    def send_invite_email(self, to_email: str, temp_password: str,
                          first_name: str = "", base_url: Optional[str] = None) -> bool:
        """Send an onboarding invitation email with temp password."""
        base_url = base_url or os.getenv("APP_BASE_URL", "http://localhost:3000")
        login_url = f"{base_url}/login"
        greeting = f"Hi {first_name}," if first_name else "Hi,"

        subject = "Welcome to Zerve Direct - Your Account is Ready"
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #333;">
            <div style="background: linear-gradient(135deg, #7b6df6, #10b981); padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
                <h1 style="color: white; margin: 0;">Zerve Direct</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 8px 0 0;">Connecting Businesses with Lenders</p>
            </div>
            <div style="padding: 30px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 8px 8px;">
                <p>{greeting}</p>
                <p>You have been invited to <strong>Zerve Direct</strong>, a platform that streamlines the lending application process for your business.</p>
                <p>To get started, log in with your temporary credentials:</p>
                <div style="background: #f5f5f5; padding: 16px; border-radius: 6px; margin: 20px 0;">
                    <p style="margin: 4px 0;"><strong>Email:</strong> {to_email}</p>
                    <p style="margin: 4px 0;"><strong>Temporary Password:</strong> {temp_password}</p>
                </div>
                <p>You will be asked to set a new password on your first login.</p>
                <p style="text-align: center; margin: 24px 0;">
                    <a href="{login_url}" style="background-color: #7b6df6; color: white; padding: 14px 32px;
                       text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold;">
                       Log In to Zerve Direct
                    </a>
                </p>
                <p><strong>What to expect:</strong></p>
                <ol>
                    <li>Log in and set your new password</li>
                    <li>Review the list of required documents</li>
                    <li>Upload your business documents securely</li>
                    <li>Our team will review and get back to you</li>
                </ol>
                <p>If you have questions, reply to this email and our team will assist you.</p>
                <p>Best regards,<br>The Zerve Direct Team</p>
            </div>
        </body>
        </html>
        """
        text_body = (
            f"{greeting}\n\n"
            f"You have been invited to Zerve Direct.\n"
            f"Log in at: {login_url}\n"
            f"Email: {to_email}\n"
            f"Temporary Password: {temp_password}\n\n"
            f"You will be asked to set a new password on first login."
        )

        return self.send_email(to_email, subject, html_body, text_body)

    def send_org_invitation(self, to_email: str, org_id: str, token: str,
                            base_url: Optional[str] = None) -> bool:
        """Send an organization invitation email with an accept link."""
        base_url = base_url or os.getenv("APP_BASE_URL", "https://d1nxnon4hga612.cloudfront.net")
        accept_url = f"{base_url}/register?invite={token}"

        subject = "You're Invited to Join a Team on Zerve My Time"
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #333;">
            <div style="background: linear-gradient(135deg, #7b6df6, #10b981); padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
                <h1 style="color: white; margin: 0;">Zerve My Time</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 8px 0 0;">Time Tracking Made Simple</p>
            </div>
            <div style="padding: 30px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 8px 8px;">
                <p>Hi,</p>
                <p>You've been invited to join a team on <strong>Zerve My Time</strong>, a time tracking platform for teams and organizations.</p>
                <p>Click the button below to create your account and get started:</p>
                <p style="text-align: center; margin: 24px 0;">
                    <a href="{accept_url}" style="background-color: #7b6df6; color: white; padding: 14px 32px;
                       text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold;">
                       Accept Invitation
                    </a>
                </p>
                <p style="color: #666; font-size: 13px;">This invitation expires in 7 days. If you did not expect this email, you can safely ignore it.</p>
                <p>Best regards,<br>The Zerve My Time Team</p>
            </div>
        </body>
        </html>
        """
        text_body = (
            f"You've been invited to join a team on Zerve My Time.\n\n"
            f"Accept your invitation at: {accept_url}\n\n"
            f"This invitation expires in 7 days."
        )

        return self.send_email(to_email, subject, html_body, text_body)

    def send_reminder_email(self, to_email: str, first_name: str = "",
                            base_url: Optional[str] = None) -> bool:
        """Send a reminder email for incomplete document uploads."""
        base_url = base_url or os.getenv("APP_BASE_URL", "http://localhost:3000")
        login_url = f"{base_url}/login"
        greeting = f"Hi {first_name}," if first_name else "Hi,"

        subject = "Reminder: Complete Your Document Upload - Zerve Direct"
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #333;">
            <div style="background: linear-gradient(135deg, #7b6df6, #10b981); padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
                <h1 style="color: white; margin: 0;">Zerve Direct</h1>
            </div>
            <div style="padding: 30px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 8px 8px;">
                <p>{greeting}</p>
                <p>We noticed you have not yet completed uploading your required documents on Zerve Direct.</p>
                <p>Please log in and upload any remaining documents so we can process your application.</p>
                <p style="text-align: center; margin: 24px 0;">
                    <a href="{login_url}" style="background-color: #7b6df6; color: white; padding: 14px 32px;
                       text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold;">
                       Complete Your Upload
                    </a>
                </p>
                <p>Best regards,<br>The Zerve Direct Team</p>
            </div>
        </body>
        </html>
        """
        text_body = f"{greeting}\n\nPlease complete your document upload at: {login_url}"

        return self.send_email(to_email, subject, html_body, text_body)

    def send_verification_email(self, to_email: str, verification_token: str,
                                base_url: Optional[str] = None) -> bool:
        base_url = base_url or os.getenv("APP_BASE_URL", "http://localhost:3000")
        verify_url = f"{base_url}/verify-email?token={verification_token}"

        subject = "Verify your email address"
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Email Verification</h2>
            <p>Please click the link below to verify your email address:</p>
            <p><a href="{verify_url}" style="background-color: #7b6df6; color: white; padding: 12px 24px;
               text-decoration: none; border-radius: 4px; display: inline-block;">Verify Email</a></p>
            <p>Or copy and paste this URL into your browser:</p>
            <p>{verify_url}</p>
            <p>This link will expire in 24 hours.</p>
        </body>
        </html>
        """
        text_body = f"Please verify your email by visiting: {verify_url}"
        return self.send_email(to_email, subject, html_body, text_body)

    def send_password_reset_email(self, to_email: str, reset_token: str,
                                  base_url: Optional[str] = None) -> bool:
        base_url = base_url or os.getenv("APP_BASE_URL", "http://localhost:3000")
        reset_url = f"{base_url}/reset-password?token={reset_token}"

        subject = "Password Reset Request"
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Password Reset</h2>
            <p>You requested a password reset. Click the link below to set a new password:</p>
            <p><a href="{reset_url}" style="background-color: #7b6df6; color: white; padding: 12px 24px;
               text-decoration: none; border-radius: 4px; display: inline-block;">Reset Password</a></p>
            <p>Or copy and paste this URL into your browser:</p>
            <p>{reset_url}</p>
            <p>This link will expire in 1 hour. If you did not request a password reset, please ignore this email.</p>
        </body>
        </html>
        """
        text_body = f"Reset your password by visiting: {reset_url}"
        return self.send_email(to_email, subject, html_body, text_body)
