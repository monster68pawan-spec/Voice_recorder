import tkinter as tk
from tkinter import filedialog, messagebox
import sounddevice as sd
import wave
import queue
import time
from datetime import datetime
from pathlib import Path


class VoiceRecorder:
    def __init__(self, root):
        self.root = root
        self.root.title("Voice Recorder")
        self.root.geometry("500x350")
        self.root.resizable(False, False)

        # Microphone settings
        self.device = 0
        self.channels = 1
        self.dtype = "int16"

        # Get the microphone's default sample rate
        device_info = sd.query_devices(self.device, "input")
        self.sample_rate = int(device_info["default_samplerate"])

        # Recording variables
        self.recording = False
        self.stream = None
        self.audio_queue = queue.Queue()
        self.start_time = 0

        # ---------------- TITLE ----------------
        tk.Label(
            root,
            text="🎙 Voice Recorder",
            font=("Arial", 24, "bold")
        ).pack(pady=25)

        # ---------------- TIMER ----------------
        self.timer_label = tk.Label(
            root,
            text="00:00",
            font=("Arial", 32, "bold")
        )
        self.timer_label.pack(pady=5)

        # ---------------- STATUS ----------------
        self.status_label = tk.Label(
            root,
            text="Status: Ready to record",
            font=("Arial", 12)
        )
        self.status_label.pack(pady=15)

        # ---------------- BUTTONS ----------------
        button_frame = tk.Frame(root)
        button_frame.pack(pady=20)

        self.record_button = tk.Button(
            button_frame,
            text="Start Recording",
            font=("Arial", 11, "bold"),
            width=18,
            height=2,
            command=self.start_recording
        )
        self.record_button.grid(row=0, column=0, padx=8)

        self.stop_button = tk.Button(
            button_frame,
            text="Stop & Save",
            font=("Arial", 11, "bold"),
            width=18,
            height=2,
            command=self.stop_recording,
            state=tk.DISABLED
        )
        self.stop_button.grid(row=0, column=1, padx=8)

        # ---------------- EXIT ----------------
        tk.Button(
            root,
            text="Exit",
            width=12,
            command=self.close_application
        ).pack(pady=5)

    # ---------------- AUDIO CALLBACK ----------------
    def audio_callback(self, indata, frames, time_info, status):
        if status:
            print("Audio status:", status)

        self.audio_queue.put(indata.copy().tobytes())

    # ---------------- START RECORDING ----------------
    def start_recording(self):
        if self.recording:
            return

        try:
            # Clear old audio data
            while not self.audio_queue.empty():
                self.audio_queue.get()

            # Open laptop microphone
            self.stream = sd.InputStream(
                device=self.device,
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=self.dtype,
                callback=self.audio_callback
            )

            self.stream.start()

            self.recording = True
            self.start_time = time.time()

            self.record_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.status_label.config(text="Status: Recording...")

            self.update_timer()

        except Exception as error:
            self.stream = None

            messagebox.showerror(
                "Microphone Error",
                f"Could not start recording.\n\n{error}"
            )

    # ---------------- TIMER ----------------
    def update_timer(self):
        if not self.recording:
            return

        elapsed = int(time.time() - self.start_time)
        minutes = elapsed // 60
        seconds = elapsed % 60

        self.timer_label.config(
            text=f"{minutes:02d}:{seconds:02d}"
        )

        self.root.after(1000, self.update_timer)

    # ---------------- STOP RECORDING ----------------
    def stop_recording(self):
        if not self.recording:
            return

        try:
            self.recording = False

            # Stop microphone
            if self.stream:
                self.stream.stop()
                self.stream.close()
                self.stream = None

            # Collect audio
            audio_data = []

            while not self.audio_queue.empty():
                audio_data.append(
                    self.audio_queue.get()
                )

            audio_bytes = b"".join(audio_data)

            if not audio_bytes:
                messagebox.showwarning(
                    "No Audio",
                    "No audio was recorded."
                )
                self.reset_interface()
                return

            # Ask where to save
            default_name = (
                "recording_"
                + datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                + ".wav"
            )
            recordings_directory = Path(__file__).resolve().parent / "Saved_Recording"
            recordings_directory.mkdir(parents=True, exist_ok=True)

            file_path = filedialog.asksaveasfilename(
                title="Save Recording",
                defaultextension=".wav",
                initialfile=default_name,
                initialdir=str(recordings_directory),
                filetypes=[
                    ("WAV Audio File", "*.wav")
                ]
            )

            if not file_path:
                self.status_label.config(
                    text="Status: Recording discarded"
                )
                self.reset_interface()
                return

            # Save WAV file
            with wave.open(file_path, "wb") as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(2)
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_bytes)

            self.reset_interface()

            self.status_label.config(
                text="Status: Recording saved successfully"
            )

            messagebox.showinfo(
                "Success",
                f"Recording saved successfully!\n\n{file_path}"
            )

        except Exception as error:
            self.recording = False
            self.stream = None

            messagebox.showerror(
                "Error",
                f"Something went wrong.\n\n{error}"
            )

            self.reset_interface()

    # ---------------- RESET INTERFACE ----------------
    def reset_interface(self):
        self.recording = False
        self.timer_label.config(text="00:00")
        self.record_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    # ---------------- CLOSE APPLICATION ----------------
    def close_application(self):
        if self.recording and self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass

        self.root.destroy()


# ---------------- MAIN ----------------
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = VoiceRecorder(root)
        root.mainloop()

    except Exception as error:
        print("Application error:", error)