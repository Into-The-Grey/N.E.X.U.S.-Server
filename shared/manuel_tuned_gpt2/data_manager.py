import pandas as pd

# File path for the feedback data
feedback_file = "/home/ncacord/N.E.X.U.S.-Server/shared/manual_tuned_gpt2/feedback/interaction_data.csv"
filtered_file = "/home/ncacord/N.E.X.U.S.-Server/shared/manual_tuned_gpt2/feedback/high_quality_data.csv"


def filter_high_quality_responses(min_rating=8):
    try:
        df = pd.read_csv(feedback_file)
        high_quality_df = df[df["Rating"] >= min_rating]
        high_quality_df.to_csv(filtered_file, index=False)
        print(f"Filtered {len(high_quality_df)} high-quality interactions.")
    except FileNotFoundError:
        print(f"Feedback file {feedback_file} not found.")
    except Exception as e:
        print(f"An error occurred while filtering data: {e}")


def show_statistics():
    try:
        df = pd.read_csv(feedback_file)
        print("Statistics:")
        print(df.describe())
    except FileNotFoundError:
        print(f"Feedback file {feedback_file} not found.")
    except Exception as e:
        print(f"An error occurred while generating statistics: {e}")


if __name__ == "__main__":
    filter_high_quality_responses()
    show_statistics()
