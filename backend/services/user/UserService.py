"""User service for Cognito admin operations (bulk user creation)."""
import os
import string
import secrets
from typing import Optional, Tuple
import boto3
from botocore.exceptions import ClientError
from abstractions.IServiceManagerBase import IServiceManagerBase

COGNITO_REGION = os.getenv("AWS_REGION_NAME", "us-east-1")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID", "")


class UserService(IServiceManagerBase):
    """Handles Cognito admin user operations for bulk imports."""

    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self._cognito = None

    def initialize(self):
        self._cognito = boto3.client("cognito-idp", region_name=COGNITO_REGION)

    def generate_temp_password(self, length: int = 12) -> str:
        """Generate a secure temporary password meeting Cognito requirements."""
        # Ensure at least one of each required character type
        upper = secrets.choice(string.ascii_uppercase)
        lower = secrets.choice(string.ascii_lowercase)
        digit = secrets.choice(string.digits)
        special = secrets.choice("!@#$%^&*")
        remaining = ''.join(secrets.choice(string.ascii_letters + string.digits + "!@#$%^&*") for _ in range(length - 4))
        password = list(upper + lower + digit + special + remaining)
        secrets.SystemRandom().shuffle(password)
        return ''.join(password)

    def create_cognito_user(self, email: str, temp_password: str,
                            first_name: str = "", last_name: str = "") -> Tuple[bool, str, str]:
        """Create a user in Cognito with a temporary password.

        Args:
            email: User email (also used as username).
            temp_password: Temporary password for first login.
            first_name: Optional first name.
            last_name: Optional last name.

        Returns:
            Tuple of (success, cognito_sub, error_message)
        """
        if not self._cognito:
            self.initialize()

        user_attributes = [
            {"Name": "email", "Value": email},
            {"Name": "email_verified", "Value": "true"},
        ]
        if first_name:
            user_attributes.append({"Name": "given_name", "Value": first_name})
        if last_name:
            user_attributes.append({"Name": "family_name", "Value": last_name})

        try:
            response = self._cognito.admin_create_user(
                UserPoolId=COGNITO_USER_POOL_ID,
                Username=email,
                UserAttributes=user_attributes,
                TemporaryPassword=temp_password,
                MessageAction="SUPPRESS",  # We send our own email
            )
            cognito_sub = ""
            for attr in response.get("User", {}).get("Attributes", []):
                if attr["Name"] == "sub":
                    cognito_sub = attr["Value"]
                    break
            return True, cognito_sub, ""
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "UsernameExistsException":
                return False, "", "User already exists"
            return False, "", str(e.response["Error"]["Message"])
        except Exception as e:
            return False, "", str(e)
