import tkinter as tk
from tkinter import ttk
import pyttsx3
import os
import threading
import time
import sounddevice as sd  # Importer sounddevice pour l'enregistrement audio
import soundfile as sf  # Importer soundfile pour sauvegarder l'audio
import speech_recognition as sr  # Importer speech_recognition pour la reconnaissance vocale
from groq import Groq
import logging

# Configurer le journal pour l'analyse de la latence
logging.basicConfig(filename='latency_log.txt', level=logging.INFO)

class CallBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Bot d'appel")
        self.stop_flag = False

        self.create_widgets()

    def create_widgets(self):
        self.dialogue_frame = ttk.Frame(self.root, padding="20")
        self.dialogue_frame.grid(row=0, column=0, sticky="nsew")

        self.dialogue_label = ttk.Label(self.dialogue_frame, text="Dialogue :")
        self.dialogue_label.grid(row=0, column=0, sticky="w")

        self.dialogue_text = tk.Text(self.dialogue_frame, width=50, height=10)
        self.dialogue_text.grid(row=1, column=0, padx=5, pady=5)

        self.start_button = ttk.Button(self.root, text="Commencer la conversation", command=self.start_conversation)
        self.start_button.grid(row=1, column=0, sticky="e")

    def log_time_taken(self, task_name, start_time, end_time):
        elapsed_time = end_time - start_time
        logging.info(f"{task_name} a pris {elapsed_time:.2f} secondes")
        if "Reconnaissance vocale réussie" not in task_name:
            print(f"{task_name} a pris {elapsed_time:.2f} secondes")

    def speak(self, text):
        start_time = time.time()
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        for voice in voices:
            if not voice.languages:
                continue
            if 'fr' in voice.languages[0].lower():  # Vérifier la voix française
                engine.setProperty('voice', voice.id)
                break
        engine.setProperty('rate', 150)  # Diminuer la vitesse de parole
        engine.say(text)
        engine.runAndWait()
        end_time = time.time()
        self.log_time_taken("Texte-à-parole (pyttsx3)", start_time, end_time)

    def recognize_speech(self):
        recognizer = sr.Recognizer()
        fs = 44100
        seconds = 4
        print("Enregistrement audio...")
        audio = sd.rec(int(seconds * fs), samplerate=fs, channels=1)  # Utiliser sounddevice pour l'enregistrement audio
        sd.wait()
        audio_file = "temp.wav"
        sf.write(audio_file, audio, fs)

        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            try:
                start_time = time.time()
                result = recognizer.recognize_google(audio_data, language="fr-FR")
                end_time = time.time()
                print(f"Reconnaissance vocale réussie : {result}")
                self.log_time_taken("Transcription audio", start_time, end_time)
            except sr.UnknownValueError:
                result = "Je n'ai pas compris"
                print("Erreur : Reconnaissance vocale n'a pas compris l'audio.")
            except sr.RequestError as e:
                result = f"Erreur de reconnaissance vocale: {e}"
                print(f"Erreur de reconnaissance vocale : {e}")

        os.remove(audio_file)
        return result

    def bot_conversation(self):
        self.dialogue_text.insert(tk.END, "Bot : Comment puis-je vous aider aujourd'hui ?\n")
        self.speak("Comment puis-je vous aider aujourd'hui ?")

        while True:
            user_input = self.recognize_speech()
            self.dialogue_text.insert(tk.END, f"Vous : {user_input}\n")

            if user_input.lower() == "au revoir":
                break

            start_time = time.time()
            response = self.groq_response(user_input)
            end_time = time.time()

            if response:
                self.dialogue_text.insert(tk.END, f"Bot : {response}\n")
                self.speak(response)
            else:
                self.dialogue_text.insert(tk.END, "Bot : Je n'ai pas de réponse à vous fournir pour le moment.\n")
                self.speak("Je n'ai pas de réponse à vous fournir pour le moment.")

    def groq_response(self, user_input):
        try:
            start_time = time.time()
            client = Groq(api_key="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")  # Remplacez par votre clé API

            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": user_input,
                    }
                ],
                model="mixtral-8x7b-32768",
            )

            response = chat_completion.choices[0].message.content
            end_time = time.time()
            self.log_time_taken("Appel API Groq", start_time, end_time)

            return response
        except Exception as e:
            print(f"Erreur lors de l'appel à l'API Groq : {e}")
            return None

    def start_conversation(self):
        self.stop_flag = False
        thread = threading.Thread(target=self.bot_conversation)
        thread.daemon = True
        thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = CallBotGUI(root)
    root.mainloop()
