import json
import os
from dotenv import load_dotenv
from datetime import datetime
import pytz

# Load environment variables from .env file
load_dotenv(
    dotenv_path="/home/ncacord/N.E.X.U.S.-Server/shared/manuel_tuned_gpt2/chatbot.env",
    verbose=True,
    override=True,
)

# Load the personal information file path from the environment variable
personal_info_path = os.getenv("NCA_PERSONAL_INFO_CONFIG")


def load_personal_info():
    if personal_info_path and os.path.exists(personal_info_path):
        try:
            with open(personal_info_path, "r") as file:
                return json.load(file)
        except Exception as e:
            print(f"Error loading personal information: {e}")
            return {}
    else:
        print(f"Personal info file not found at {personal_info_path}")
        return {}


def get_personal_detail(category, key):
    """Retrieve a specific piece of information from a given category."""
    personal_info = load_personal_info()
    return personal_info.get(category, {}).get(key, "Detail not found")


def get_full_name():
    """Retrieve the full name."""
    personal_info = load_personal_info()
    first_name = personal_info.get("personal", {}).get("first_name", "")
    middle_name = personal_info.get("personal", {}).get("middle_name", "")
    last_name = personal_info.get("personal", {}).get("last_name", "")
    return f"{first_name} {middle_name} {last_name}".strip()


def get_emergency_contact():
    """Retrieve emergency contact details."""
    return get_personal_detail("contact", "emergency_contact")


def get_local_time():
    """Retrieve the local time based on the user's time zone."""
    personal_info = load_personal_info()
    time_zone_str = personal_info.get("geographic", {}).get("time_zone", "UTC")
    tz = pytz.timezone(time_zone_str)
    return datetime.now(tz)


def get_social_media_account(platform):
    """Retrieve a specific social media account."""
    personal_info = load_personal_info()
    return (
        personal_info.get("social", {})
        .get("social_media", {})
        .get(platform, "Account not found")
    )


def get_health_info():
    """Retrieve health-related details."""
    return load_personal_info().get("health", {})


def get_financial_info():
    """Retrieve financial-related details."""
    return load_personal_info().get("financial", {})


# Example usage
if __name__ == "__main__":
    print("Full Name:", get_full_name())  # Outputs the full name
    print("Preferred Greeting:", get_personal_detail("personal", "preferred_greeting"))
    print("Local Time:", get_local_time().strftime("%Y-%m-%d %H:%M:%S %Z"))
    print("Emergency Contact:", get_emergency_contact())
    print("GitHub Account:", get_social_media_account("github"))
    print("Health Info:", get_health_info())
    print("Financial Info:", get_financial_info())
