import pyttsx3
import os
import time
import sounddevice as sd
import soundfile as sf
import speech_recognition as sr
from groq import Groq
import logging

# Configure logging for latency analysis
logging.basicConfig(level=logging.INFO)

class CallBotConsole:
    def __init__(self):
        self.stop_flag = False

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
            languages = [lang.decode() if isinstance(lang, bytes) else lang for lang in voice.languages]
            if any('fr' in lang.lower() for lang in languages):  # Check for French voice
                engine.setProperty('voice', voice.id)
                break
        engine.setProperty('rate', 150)  # Slow down speech rate
        engine.say(text)
        engine.runAndWait()
        end_time = time.time()
        self.log_time_taken("Texte-à-parole (pyttsx3)", start_time, end_time)

    def recognize_speech(self):
        recognizer = sr.Recognizer()
        fs = 44100
        seconds = 4
        print("Enregistrement audio...")
        audio = sd.rec(int(seconds * fs), samplerate=fs, channels=1)  # Use sounddevice for audio recording
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
        print("Bot : Comment puis-je vous aider aujourd'hui ?")
        self.speak("Comment puis-je vous aider aujourd'hui ?")

        while True:
            user_input = self.recognize_speech()
            print(f"Vous : {user_input}")

            if user_input.lower() == "au revoir":
                break

            start_time = time.time()
            response = self.groq_response(user_input)
            end_time = time.time()

            if response:
                print(f"Bot : {response}")
                self.speak(response)
            else:
                print("Bot : Je n'ai pas de réponse à vous fournir pour le moment.")
                self.speak("Je n'ai pas de réponse à vous fournir pour le moment.")

    def groq_response(self, user_input):
        try:
            start_time = time.time()
            client = Groq(api_key="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")  # Replace with your API key

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

if __name__ == "__main__":
    app = CallBotConsole()
    app.bot_conversation()
