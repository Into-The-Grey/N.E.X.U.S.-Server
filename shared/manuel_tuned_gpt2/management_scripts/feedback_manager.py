import logging
import csv
import os
import random
from transformers import pipeline
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(
    dotenv_path="/home/ncacord/N.E.X.U.S.-Server/shared/manuel_tuned_gpt2/chatbot.env",
    verbose=True,
    override=True,
)
albert_model_path = os.getenv("ALBERT_MODEL_PATH")

# File path for storing feedback
feedback_file = "/home/ncacord/N.E.X.U.S.-Server/shared/manuel_tuned_gpt2/feedback/interaction_data.csv"
os.makedirs(os.path.dirname(feedback_file), exist_ok=True)

# Configure logging
logging_dir = os.environ.get(
    "LOGGING_DIR", "/home/ncacord/N.E.X.U.S.-Server/shared/manuel_tuned_gpt2/logs"
)
log_file_name = "feedback_manager.log"  # Custom log file name for this script
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
feedback_categories = [
    "Greeting",
    "Informational",
    "Actionable",
    "Clarification",
    "Detailed Explanation",
    "Concise",
    "Helpful",
    "Empathetic",
    "Insightful",
    "Engaging",
]

# Load sentiment analysis model
sentiment_analyzer = pipeline("sentiment-analysis", model=albert_model_path, tokenizer=albert_model_path, device=0)


def analyze_sentiment(text):
    try:
        result = sentiment_analyzer(text)

        if not result or not isinstance(result, list) or len(result) == 0:
            logging.error("Invalid or empty result from sentiment analyzer")
            return None

        label = result[0].get("label", None)
        score = result[0].get("score", None)

        if label is None or score is None:
            logging.error("Missing label or score in sentiment analysis result")
            return None

        if label == "POSITIVE":
            return int(score * 10)
        elif label == "NEGATIVE":
            return int((1 - score) * 10)
        else:  # NEUTRAL or any other label
            return 5
    except Exception as e:
        logging.error(f"Error analyzing sentiment: {e}")
        return None


def ask_yes_no_question():
    while True:
        response = (
            input("Did the response answer your prompt? (Yes/No): ").strip().lower()
        )
        if response in ["yes", "no"]:
            return response == "yes"
        else:
            print("Please enter 'Yes' or 'No'.")


def ask_for_quality():
    while True:
        try:
            rating = int(input("Rate the response quality (1-10): "))
            if 1 <= rating <= 10:
                return rating
            else:
                print("Please enter a rating between 1 and 10.")
        except ValueError:
            print("Please enter a valid number.")


def ask_for_category():
    selected_categories = random.sample(feedback_categories, 5)
    print("Select the category that best describes the response:")
    for idx, category in enumerate(selected_categories, start=1):
        print(f"{idx}. {category}")

    while True:
        try:
            choice = int(input("Enter the category number: "))
            if 1 <= choice <= len(selected_categories):
                return selected_categories[choice - 1]
            else:
                print(
                    f"Please choose a valid category between 1 and {len(selected_categories)}."
                )
        except ValueError:
            print("Please enter a valid number.")


def save_interaction(user_input, model_response, category, quality_rating, answered):
    with open(feedback_file, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            [user_input, model_response, category, quality_rating, answered]
        )
        print(
            f"Feedback saved: {user_input}, {model_response}, {category}, {quality_rating}, {answered}"
        )


def collect_feedback(user_input, model_response):
    print(f"Model Response: {model_response}")
    should_collect_feedback = random.random() < 0.33  # 1 in 3 chance

    if should_collect_feedback:
        answered = ask_yes_no_question()
        quality_rating = ask_for_quality()

        if quality_rating > 3 and answered:  # Skip category if rating is 3 or lower
            category = ask_for_category()
            save_interaction(
                user_input, model_response, category, quality_rating, answered
            )
        else:
            save_interaction(user_input, model_response, None, quality_rating, answered)


if __name__ == "__main__":
    # Example usage
    user_input = input("Enter your prompt: ")
    model_response = (
        "Example response from model"  # Replace with the actual model's response
    )
    collect_feedback(user_input, model_response)
