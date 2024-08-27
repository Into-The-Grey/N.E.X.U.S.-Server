import json
import os
from dotenv import load_dotenv

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


def get_personal_detail(key):
    personal_info = load_personal_info()
    return personal_info.get(key, "Detail not found")


# Example usage
if __name__ == "__main__":
    print(get_personal_detail("last_name"))  # Should output "Acord"
