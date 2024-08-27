import csv
import os

# File path for storing feedback
feedback_file = "/home/ncacord/N.E.X.U.S.-Server/shared/manual_tuned_gpt2/feedback/interaction_data.csv"
os.makedirs(os.path.dirname(feedback_file), exist_ok=True)


def ask_for_rating():
    while True:
        try:
            rating = int(input("Rate the response (1-10): "))
            if 1 <= rating <= 10:
                return rating
            else:
                print("Please enter a rating between 1 and 10.")
        except ValueError:
            print("Please enter a valid number.")


def save_interaction(user_input, model_response, rating):
    with open(feedback_file, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([user_input, model_response, rating])
        print(f"Feedback saved: {user_input}, {model_response}, {rating}")


def collect_feedback(user_input, model_response):
    print(f"Model Response: {model_response}")
    rating = ask_for_rating()
    save_interaction(user_input, model_response, rating)


if __name__ == "__main__":
    # Example usage
    user_input = input("Enter your prompt: ")
    model_response = (
        "Example response from model"  # Replace with the actual model's response
    )
    collect_feedback(user_input, model_response)
