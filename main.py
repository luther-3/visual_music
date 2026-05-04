"""Application entry point for the music visualizer."""

import tkinter as tk
from tkinter import filedialog

from audio_processor import AudioProcessor
from visualizer import Visualizer


def select_audio_file() -> str | None:
    """Open native file dialog and return selected audio path."""
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="选择音频文件",
        filetypes=[("音频文件", "*.mp3 *.wav *.flac *.ogg"), ("所有文件", "*.*")],
    )
    root.destroy()
    return file_path if file_path else None


def main():
    """Main application loop."""
    while True:
        file_path = select_audio_file()
        if not file_path:
            print("未选择文件，程序退出。")
            break

        audio_data = AudioProcessor.load(file_path)
        if audio_data is None:
            continue

        visualizer = Visualizer()
        try:
            visualizer.run(audio_data, file_path)
        finally:
            visualizer.cleanup()


if __name__ == "__main__":
    main()
