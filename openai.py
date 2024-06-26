import tkinter as tk
from tkinter import ttk
import threading
import time
import sounddevice as sd  # For recording audio
import soundfile as sf  # For saving audio
import requests
import os
import pygame  # For playing audio
import tempfile

# Replace with your actual API key
api_key = "-------------------------------------------"

# Function to convert speech to text using custom API
def convert_speech_to_text(audio_file_path, api_key):
    start_time = time.time()  # Start time for STT
    with open(audio_file_path, "rb") as audio_file:
        files = {"file": audio_file}
        headers = {"Authorization": f"Bearer {api_key}"}
        data = {"model": "whisper-1", "response_format": "json"}

        response = requests.post("https://api.openai.com/v1/audio/transcriptions", headers=headers, files=files, data=data)

    end_time = time.time()  # End time for STT
    stt_time = end_time - start_time
    print(f"STT took {stt_time:.2f} seconds")

    if response.status_code == 200:
        return response.json()["text"]
    else:
        return f"Error: {response.status_code} - {response.text}"

# Function to convert text to speech using custom API
def convert_text_to_speech(text, api_key):
    start_time = time.time()  # Start time for TTS
    url = "https://api.openai.com/v1/audio/speech"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {"model": "tts-1", "input": text, "voice": "fable", "response_format": "mp3"}

    response = requests.post(url, headers=headers, json=data)

    end_time = time.time()  # End time for TTS
    tts_time = end_time - start_time
    print(f"TTS took {tts_time:.2f} seconds")

    if response.status_code == 200:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_audio_file:
            temp_audio_file.write(response.content)
            audio_file_path = temp_audio_file.name

        return audio_file_path
    else:
        return None

# Function to send user message to LLM and get response
def send_message(message):
    start_time = time.time()  # Start time for LLM
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "model": "gpt-3.5-turbo-16k",
        "messages": [{"role": "user", "content": message}],
        "max_tokens": 150,
        "temperature": 0.7,
        "n": 1
    }

    response = requests.post(url, headers=headers, json=data)

    end_time = time.time()  # End time for LLM
    llm_time = end_time - start_time
    print(f"LLM took {llm_time:.2f} seconds")

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Error: {response.status_code} - {response.text}"

# Function to play the audio file
def play_audio(file_path):
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)
    pygame.mixer.music.stop()  # Stop the music
    pygame.mixer.quit()  # Quit the mixer

    try:
        os.remove(file_path)  # Clean up the temporary audio file after playing
    except Exception as e:
        print(f"Error deleting {file_path}: {e}")


# GUI class for the CallBot application
class CallBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Call Bot")
        self.create_widgets()

    def create_widgets(self):
        self.dialogue_frame = ttk.Frame(self.root, padding="20")
        self.dialogue_frame.grid(row=0, column=0, sticky="nsew")

        self.dialogue_label = ttk.Label(self.dialogue_frame, text="Dialogue:")
        self.dialogue_label.grid(row=0, column=0, sticky="w")

        self.dialogue_text = tk.Text(self.dialogue_frame, width=50, height=10)
        self.dialogue_text.grid(row=1, column=0, padx=5, pady=5)

        # Start the conversation directly upon initialization
        self.start_conversation()

    def recognize_speech(self):
        fs = 44100
        seconds = 4  # Adjust as needed for your speech input duration
        print("Recording audio...")
        audio = sd.rec(int(seconds * fs), samplerate=fs, channels=1)  # Record audio
        sd.wait()

        audio_file = "temp.wav"
        sf.write(audio_file, audio, fs)  # Save recorded audio to file

        # Convert speech to text using custom API
        text = convert_speech_to_text(audio_file, api_key)

        # Clean up temporary audio file
        os.remove(audio_file)

        return text

    def bot_conversation(self):
        self.dialogue_text.insert(tk.END, "Bot: Comment puis-je vous aider aujourd'hui ?\n")
        response_audio = convert_text_to_speech("Comment puis-je vous aider aujourd'hui ?", api_key)
        if response_audio:
            play_audio(response_audio)

        while True:
            user_input = self.recognize_speech()
            self.dialogue_text.insert(tk.END, f"Vous: {user_input}\n")

            if user_input.lower() == "au revoir":
                break

            response = send_message(user_input)
            self.dialogue_text.insert(tk.END, f"Bot: {response}\n")
            response_audio = convert_text_to_speech(response, api_key)
            if response_audio:
                play_audio(response_audio)

    def start_conversation(self):
        thread = threading.Thread(target=self.bot_conversation)
        thread.daemon = True
        thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = CallBotGUI(root)
    root.mainloop()
