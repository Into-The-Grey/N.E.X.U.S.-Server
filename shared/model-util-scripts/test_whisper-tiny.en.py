import torch
from transformers import WhisperProcessor, WhisperForConditionalGeneration
import os
import logging
import psutil
import time
import librosa

# Set the directory where the quantized model is stored
model_directory_path = "/home/ncacord/N.E.X.U.S.-Server/shared/models/whisper-tiny.en"

# Set up logging
log_file_path = "/home/ncacord/N.E.X.U.S.-Server/shared/logs/whisper_test.log"
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
logging.basicConfig(filename=log_file_path, level=logging.INFO)


# Monitoring system resources
def log_system_usage():
    cpu_usage = psutil.cpu_percent(interval=1)
    ram_usage = psutil.virtual_memory().percent
    logging.info(f"CPU Usage: {cpu_usage}% | RAM Usage: {ram_usage}%")


# Load the quantized model and processor
def load_model():
    try:
        logging.info("Starting model load...")
        model = WhisperForConditionalGeneration.from_pretrained(
            model_directory_path,
            device_map={"": "cpu"},  # Ensure it's loaded on CPU
            torch_dtype=torch.float32,  # Use float32 precision for CPU
        )
        processor = WhisperProcessor.from_pretrained(model_directory_path)
        logging.info("Model successfully loaded.")
        return model, processor
    except Exception as e:
        logging.exception(f"Failed to load model: {str(e)}")
        raise


def test_transcription(model, processor, audio_file):
    try:
        logging.info("Starting transcription...")
        start_time = time.time()

        # Load the audio file with librosa
        audio, _ = librosa.load(audio_file, sr=16000)

        # Process the audio to get input features and attention mask
        inputs = processor(audio, return_tensors="pt", sampling_rate=16000)
        input_features = inputs["input_features"]
        attention_mask = inputs["attention_mask"]

        # Ensure input features are of the correct type
        input_features = input_features.to(dtype=torch.float32)

        # Generate transcription with attention mask
        predicted_ids = model.generate(input_features, attention_mask=attention_mask)

        # Decode the predicted IDs to get the transcription
        transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)[
            0
        ]

        end_time = time.time()
        logging.info(f"Transcription completed in {end_time - start_time:.2f} seconds.")
        logging.info(f"Transcription: {transcription}")
        return transcription
    except Exception as e:
        logging.exception(f"Failed to transcribe audio: {str(e)}")
        raise


def main():
    model, processor = load_model()

    # Example test audio file (replace with the path to your actual test file)
    audio_file = "/home/ncacord/N.E.X.U.S.-Server/shared/audio/file_example_WAV_1MG.wav"

    if os.path.exists(audio_file):
        log_system_usage()
        transcription = test_transcription(model, processor, audio_file)
        logging.info("Test completed successfully.")
    else:
        logging.error(f"Test audio file does not exist: {audio_file}")

    log_system_usage()


if __name__ == "__main__":
    main()
