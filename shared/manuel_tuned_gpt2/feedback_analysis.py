import csv
from collections import defaultdict

# File path for loading feedback
feedback_file = "/home/ncacord/N.E.X.U.S.-Server/shared/manual_tuned_gpt2/feedback/interaction_data.csv"


def analyze_feedback():
    feedback_data = defaultdict(lambda: {"total_rating": 0, "count": 0})

    with open(feedback_file, "r") as file:
        reader = csv.reader(file)
        for row in reader:
            category = row[2]
            rating = int(row[3])
            feedback_data[category]["total_rating"] += rating
            feedback_data[category]["count"] += 1

    print("Feedback Analysis Report:")
    for category, data in feedback_data.items():
        avg_rating = data["total_rating"] / data["count"]
        print(f"Category: {category}")
        print(f"  Average Rating: {avg_rating:.2f}")
        print(f"  Number of Feedbacks: {data['count']}")
        print("-" * 30)


if __name__ == "__main__":
    analyze_feedback()
