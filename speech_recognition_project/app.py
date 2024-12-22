import sys
import os
import speech_recognition as sr
from gtts import gTTS
from moviepy import VideoFileClip
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QFileDialog,
    QTextEdit, QVBoxLayout, QWidget, QComboBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from googletrans import Translator
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl


class SpeechRecognitionThread(QThread):
    update_text = pyqtSignal(str)

    def __init__(self, language="en"):
        super().__init__()
        self.running = True
        self.language = language

    def run(self):
        recognizer = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source)
                while self.running:
                    try:
                        audio = recognizer.listen(source, timeout=10)
                        text = recognizer.recognize_google(audio, language=self.language)
                        self.update_text.emit(text)
                    except sr.WaitTimeoutError:
                        self.update_text.emit("Listening timed out while waiting for phrase.")
                    except sr.UnknownValueError:
                        self.update_text.emit("Could not understand the audio.")
                    except sr.RequestError as e:
                        self.update_text.emit(f"Google Speech Recognition error: {e}")
        except Exception as e:
            self.update_text.emit(f"Microphone error: {e}")

    def stop(self):
        self.running = False
        self.quit()


class SpeechRecognitionApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.thread = None
        self.language_code = "en"  # Default language English
        self.translator = Translator()  # For translation
        self.audio_player = QMediaPlayer()

    def initUI(self):
        self.setWindowTitle("Speech Recognition and Conversion")
        self.setGeometry(100, 100, 900, 700)
        self.setStyleSheet("""
            QMainWindow {
                background-color: qlineargradient(
                    spread: pad,
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #1d2671, stop: 1 #c33764
                );
            }
            QPushButton {
                background-color: #ffffff;
                color: #333;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #f4f4f9;
            }
            QLabel {
                color: #ffffff;
                font-size: 16px;
            }
        """)

        # Main Layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_layout = QVBoxLayout(self.central_widget)

        # Title
        self.title_label = QLabel("Speech Recognition and Video Processing")
        self.title_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.title_label)

        # Language Selector
        self.language_selector = QComboBox()
        self.language_selector.addItems(["English", "Italian"])
        self.language_selector.currentIndexChanged.connect(self.change_language)
        main_layout.addWidget(self.language_selector)

        # Buttons Layout
        self.choose_audio_btn = QPushButton("Choose Audio File")
        self.choose_audio_btn.clicked.connect(self.process_audio_file)
        main_layout.addWidget(self.choose_audio_btn)

        self.record_audio_btn = QPushButton("Start Real-Time Recognition")
        self.record_audio_btn.clicked.connect(self.start_recognition)
        main_layout.addWidget(self.record_audio_btn)

        self.stop_recognition_btn = QPushButton("Stop Real-Time Recognition")
        self.stop_recognition_btn.clicked.connect(self.stop_recognition)
        self.stop_recognition_btn.setEnabled(False)
        main_layout.addWidget(self.stop_recognition_btn)

        self.video_to_text_btn = QPushButton("Extract Text from Video")
        self.video_to_text_btn.clicked.connect(self.process_video_file)
        main_layout.addWidget(self.video_to_text_btn)

        self.text_to_speech_btn = QPushButton("Convert Text to Speech")
        self.text_to_speech_btn.clicked.connect(self.text_to_speech)
        main_layout.addWidget(self.text_to_speech_btn)

        self.translate_btn = QPushButton("Translate Text")
        self.translate_btn.clicked.connect(self.translate_text)
        main_layout.addWidget(self.translate_btn)

        self.play_audio_btn = QPushButton("Play Output Audio")
        self.play_audio_btn.clicked.connect(self.play_output_audio)
        main_layout.addWidget(self.play_audio_btn)

        self.reset_btn = QPushButton("Reset Application")
        self.reset_btn.clicked.connect(self.reset_application)
        main_layout.addWidget(self.reset_btn)

        # Text Area
        self.text_area = QTextEdit()
        self.text_area.setPlaceholderText("Recognized text will appear here or type text for conversion...")
        main_layout.addWidget(self.text_area)

        # Variables
        self.audio_file_path = None
        self.output_audio_path = "output_audio.mp3"

    def change_language(self):
        selected_language = self.language_selector.currentText()
        if selected_language == "English":
            self.language_code = "en"
            self.update_ui_language("English")
        elif selected_language == "Italian":
            self.language_code = "it"
            self.update_ui_language("Italian")

    def update_ui_language(self, language):
        if language == "English":
            self.title_label.setText("Speech Recognition and Video Processing")
            self.choose_audio_btn.setText("Choose Audio File")
            self.record_audio_btn.setText("Start Real-Time Recognition")
            self.stop_recognition_btn.setText("Stop Real-Time Recognition")
            self.video_to_text_btn.setText("Extract Text from Video")
            self.text_to_speech_btn.setText("Convert Text to Speech")
            self.translate_btn.setText("Translate Text")
            self.play_audio_btn.setText("Play Output Audio")
            self.reset_btn.setText("Reset Application")
            self.text_area.setPlaceholderText("Recognized text will appear here or type text for conversion...")
        elif language == "Italian":
            self.title_label.setText("Riconoscimento vocale e elaborazione video")
            self.choose_audio_btn.setText("Scegli file audio")
            self.record_audio_btn.setText("Avvia il riconoscimento in tempo reale")
            self.stop_recognition_btn.setText("Ferma il riconoscimento in tempo reale")
            self.video_to_text_btn.setText("Estrai testo dal video")
            self.text_to_speech_btn.setText("Converti testo in voce")
            self.translate_btn.setText("Traduci testo")
            self.play_audio_btn.setText("Riproduci audio")
            self.reset_btn.setText("Ripristina l'applicazione")
            self.text_area.setPlaceholderText("Il testo riconosciuto apparirà qui o digita il testo per la conversione...")

    def start_recognition(self):
        self.text_area.clear()
        self.thread = SpeechRecognitionThread(language=self.language_code)
        self.thread.update_text.connect(self.update_text_area)
        self.thread.start()
        self.record_audio_btn.setEnabled(False)
        self.stop_recognition_btn.setEnabled(True)

    def stop_recognition(self):
        if self.thread:
            self.thread.stop()
        self.record_audio_btn.setEnabled(True)
        self.stop_recognition_btn.setEnabled(False)

    def update_text_area(self, text):
        self.text_area.append(text)

    def process_audio_file(self):
        self.stop_recognition()
        self.audio_file_path, _ = QFileDialog.getOpenFileName(self, "Choose Audio File", "", "Audio Files (*.wav *.mp3 *.flac)")
        if not self.audio_file_path:
            self.title_label.setText("No file selected.")
            return

        self.title_label.setText(f"Processing file: {os.path.basename(self.audio_file_path)}")
        self.recognize_speech(self.audio_file_path)

    def process_video_file(self):
        video_file_path, _ = QFileDialog.getOpenFileName(self, "Choose Video File", "", "Video Files (*.mp4 *.avi *.mkv)")
        if not video_file_path:
            self.title_label.setText("No video file selected.")
            return

        self.title_label.setText(f"Processing video: {os.path.basename(video_file_path)}")
        try:
            clip = VideoFileClip(video_file_path)
            audio_path = "extracted_audio.wav"
            clip.audio.write_audiofile(audio_path)

            self.recognize_speech(audio_path)
            os.remove(audio_path)

        except Exception as e:
            self.title_label.setText(f"Error processing video: {str(e)}")

    def recognize_speech(self, file_path):
        recognizer = sr.Recognizer()
        try:
            with sr.AudioFile(file_path) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data, language=self.language_code)
                self.text_area.append(text)
        except Exception as e:
            self.title_label.setText(f"Error processing audio: {str(e)}")

    def translate_text(self):
        original_text = self.text_area.toPlainText()
        if not original_text:
            self.title_label.setText("No text available for translation.")
            return

        try:
            translated = self.translator.translate(original_text, dest="it" if self.language_code == "en" else "en")
            self.text_area.setText(translated.text)
            self.title_label.setText("Text translated successfully.")
        except Exception as e:
            self.title_label.setText(f"Error during translation: {str(e)}")

    def text_to_speech(self, text=None):
        try:
            text = text or self.text_area.toPlainText()
            if not text:
                self.title_label.setText("No text provided for conversion.")
                return

            tts = gTTS(text=text, lang=self.language_code)
            tts.save(self.output_audio_path)
            self.title_label.setText("Text converted to speech successfully.")
        except Exception as e:
            self.title_label.setText(f"Error during text-to-speech conversion: {str(e)}")

    def play_output_audio(self):
        if os.path.exists(self.output_audio_path):
            url = QUrl.fromLocalFile(os.path.abspath(self.output_audio_path))
            self.audio_player.setMedia(QMediaContent(url))
            self.audio_player.play()
            self.title_label.setText("Playing converted audio...")
        else:
            self.title_label.setText("No audio file to play.")

    def reset_application(self):
        self.text_area.clear()
        self.audio_player.stop()
        if self.thread:
            self.thread.stop()
        self.thread = None
        self.record_audio_btn.setEnabled(True)
        self.stop_recognition_btn.setEnabled(False)
        self.title_label.setText("Application reset successfully.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SpeechRecognitionApp()
    window.show()
    sys.exit(app.exec_())
