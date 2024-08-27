import logging
import csv
import os
from transformers import pipeline

# File path for storing feedback
feedback_file = "/home/ncacord/N.E.X.U.S.-Server/shared/manual_tuned_gpt2/feedback/interaction_data.csv"
os.makedirs(os.path.dirname(feedback_file), exist_ok=True)

# Configure logging
logging_dir = os.environ.get(
    "LOGGING_DIR", "/home/ncacord/N.E.X.U.S.-Server/shared/manual_tuned_gpt2/logs"
)
log_file_name = "feedback_managers.log"  # Custom log file name for this script
log_file_path = os.path.join(logging_dir, log_file_name)

# Create the directory for the log file if it doesn't exist
if not os.path.exists(os.path.dirname(log_file_path)):
    os.makedirs(
        os.path.dirname(log_file_path), exist_ok=True
    )  # Ensure directory creation with exist_ok=True

logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)

logging.info("Starting models...")
# Categories for feedback
feedback_categories = ["Greeting", "Informational", "Actionable", "General"]

# Load sentiment analysis model
sentiment_analyzer = pipeline("sentiment-analysis")


def analyze_sentiment(text):
    try:
        # Get the sentiment analysis result
        result = sentiment_analyzer(text)

        # Check if result is None or not a list/dict we expect
        if not result or not isinstance(result, list) or len(result) == 0:
            logging.error("Invalid or empty result from sentiment analyzer")
            return None

        # Extract label and score safely
        label = result[0].get("label", None)
        score = result[0].get("score", None)

        if label is None or score is None:
            logging.error("Missing label or score in sentiment analysis result")
            return None

        # Convert sentiment score to a rating between 1 and 10
        if label == "POSITIVE":
            return int(score * 10)
        elif label == "NEGATIVE":
            return int((1 - score) * 10)
        else:  # NEUTRAL or any other label
            return 5
    except Exception as e:
        logging.error(f"Error analyzing sentiment: {e}")
        return None


def ask_for_category():
    print("Select a feedback category:")
    for idx, category in enumerate(feedback_categories, start=1):
        print(f"{idx}. {category}")

    while True:
        try:
            choice = int(input("Enter the category number: "))
            if 1 <= choice <= len(feedback_categories):
                return feedback_categories[choice - 1]
            else:
                print(
                    f"Please choose a valid category between 1 and {len(feedback_categories)}."
                )
        except ValueError:
            print("Please enter a valid number.")


def save_interaction(user_input, model_response, category, rating):
    with open(feedback_file, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([user_input, model_response, category, rating])
        print(f"Feedback saved: {user_input}, {model_response}, {category}, {rating}")


def collect_feedback(user_input, model_response):
    print(f"Model Response: {model_response}")
    category = ask_for_category()
    auto_rating = analyze_sentiment(model_response)
    print(f"Automated Rating based on sentiment: {auto_rating}")
    rating = ask_for_rating(
        auto_rating
    )  # User can override or confirm the automated rating
    save_interaction(user_input, model_response, category, rating)


def ask_for_rating(auto_rating):
    while True:
        try:
            user_input = input(
                "Rate the response (1-10) or press Enter to use automated rating: "
            )
            rating = int(user_input) if user_input else auto_rating
            if 1 <= rating <= 10:
                return rating
            else:
                print("Please enter a rating between 1 and 10.")
        except ValueError:
            print("Please enter a valid number.")


if __name__ == "__main__":
    # Example usage
    user_input = input("Enter your prompt: ")
    model_response = (
        "Example response from model"  # Replace with the actual model's response
    )
    collect_feedback(user_input, model_response)
