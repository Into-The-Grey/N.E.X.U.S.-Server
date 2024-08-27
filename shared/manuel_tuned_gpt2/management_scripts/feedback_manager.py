import logging
import csv
import os
from transformers import pipeline

# File path for storing feedback
feedback_file = "/home/ncacord/N.E.X.U.S.-Server/shared/manuel_tuned_gpt2/feedback/interaction_data.csv"

# Configure logging
logging_dir = "LOGGING_DIR"
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

logging.info("Starting feedback manager...")

# Categories for feedback
feedback_categories = ["Greeting", "Informational", "Actionable", "General"]

# Load sentiment analysis model
try:
    sentiment_analyzer = pipeline("sentiment-analysis")
    logging.info("Sentiment analysis model loaded successfully.")
except Exception as e:
    logging.error(f"Failed to load sentiment analysis model: {e}")
    raise RuntimeError("Failed to load sentiment analysis model.") from e


def analyze_sentiment(text):
    try:
        # Get the sentiment analysis result
        result = sentiment_analyzer(text)

        # Validate the result
        if not result or not isinstance(result, list) or len(result) == 0:
            logging.error("Invalid or empty result from sentiment analyzer")
            return 5  # Default to neutral rating

        # Extract label and score safely
        label = result[0].get("label")
        score = result[0].get("score")

        if label is None or score is None:
            logging.error("Missing label or score in sentiment analysis result")
            return 5  # Default to neutral rating

        # Convert sentiment score to a rating between 1 and 10
        if label == "POSITIVE":
            return int(score * 10)
        elif label == "NEGATIVE":
            return int((1 - score) * 10)
        else:  # NEUTRAL or any other label
            return 5
    except Exception as e:
        logging.error(f"Error analyzing sentiment: {e}")
        return 5  # Default to neutral rating


def ask_for_category():
    try:
        print("Select a feedback category:")
        for idx, category in enumerate(feedback_categories, start=1):
            print(f"{idx}. {category}")

        while True:
            choice = input("Enter the category number: ").strip()
            if choice.isdigit():
                choice = int(choice)
                if 1 <= choice <= len(feedback_categories):
                    return feedback_categories[choice - 1]
                else:
                    print(
                        f"Please choose a valid category between 1 and {len(feedback_categories)}."
                    )
            else:
                print("Please enter a valid number.")
    except Exception as e:
        logging.error(f"Error selecting category: {e}")
        return "General"  # Default to "General" if an error occurs


def save_interaction(user_input, model_response, category, rating):
    try:
        with open(feedback_file, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([user_input, model_response, category, rating])
            print(
                f"Feedback saved: {user_input}, {model_response}, {category}, {rating}"
            )
            logging.info(
                f"Interaction saved: {user_input}, {model_response}, {category}, {rating}"
            )
    except Exception as e:
        logging.error(f"Error saving interaction: {e}")
        print("Failed to save feedback. Please try again.")


def collect_feedback(user_input, model_response):
    try:
        print(f"Model Response: {model_response}")
        category = ask_for_category()
        auto_rating = analyze_sentiment(model_response)
        print(f"Automated Rating based on sentiment: {auto_rating}")
        rating = ask_for_rating(
            auto_rating
        )  # User can override or confirm the automated rating
        save_interaction(user_input, model_response, category, rating)
    except Exception as e:
        logging.error(f"Error during feedback collection: {e}")
        print("An error occurred during feedback collection. Please try again.")


def ask_for_rating(auto_rating):
    try:
        while True:
            user_input = input(
                "Rate the response (1-10) or press Enter to use automated rating: "
            ).strip()
            if not user_input:  # User pressed Enter, use auto rating
                return auto_rating
            if user_input.isdigit():
                rating = int(user_input)
                if 1 <= rating <= 10:
                    return rating
                else:
                    print("Please enter a rating between 1 and 10.")
            else:
                print("Please enter a valid number.")
    except Exception as e:
        logging.error(f"Error during rating input: {e}")
        print("Failed to get a valid rating. Using automated rating.")
        return auto_rating  # Fallback to automated rating if an error occurs


if __name__ == "__main__":
    try:
        # Example usage
        user_input = input("Enter your prompt: ").strip()
        if not user_input:
            print("No input provided.")
            logging.error("No user input provided.")
            exit(1)

        model_response = (
            "Example response from model"  # Replace with the actual model's response
        )
        collect_feedback(user_input, model_response)
    except Exception as e:
        logging.critical(f"Critical error in main execution: {e}")
        print("A critical error occurred. Exiting.")
