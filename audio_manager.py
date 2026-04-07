"""Audio playback helpers for background music and call sound effects."""

from pathlib import Path

from PyQt6.QtCore import QUrl
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer


ASSETS_DIR = Path(__file__).resolve().parent / "assets" / "audio"


class AudioManager:
    """Owns the media players used by the UI."""

    def __init__(self):
        self.music_player = QMediaPlayer()
        self.music_output = QAudioOutput()
        self.music_player.setAudioOutput(self.music_output)

        self.sfx_player = QMediaPlayer()
        self.sfx_output = QAudioOutput()
        self.sfx_player.setAudioOutput(self.sfx_output)

        self.playlist = [
            ASSETS_DIR / "music_01.mp3",
            ASSETS_DIR / "music_02.mp3",
            ASSETS_DIR / "music_03.mp3",
            ASSETS_DIR / "music_04.mp3",
            ASSETS_DIR / "music_05.mp3",
        ]

        self.sfx = {
            "incoming": ASSETS_DIR / "call_incoming.mp3",
            "accept": ASSETS_DIR / "call_accept.mp3",
            "reject": ASSETS_DIR / "call_reject.mp3",
            "end": ASSETS_DIR / "call_end.mp3",
        }

    def play_track(self, index: int, volume: int = 60):
        """Start playing a track if the index is valid and the file exists."""
        if not (0 <= index < len(self.playlist)):
            return

        path = self.playlist[index]
        if not path.exists():
            return

        self.music_player.setSource(QUrl.fromLocalFile(str(path.resolve())))
        self.set_volume(volume)
        self.music_player.play()

    def pause_music(self):
        self.music_player.pause()

    def resume_music(self):
        self.music_player.play()

    def stop_music(self):
        self.music_player.stop()

    def set_volume(self, volume: int):
        """Set playback volume in the inclusive range [0, 100]."""
        bounded = max(0, min(100, volume))
        self.music_output.setVolume(bounded / 100.0)

    def play_sfx(self, name: str, volume: float = 1.0):
        """Play a sound effect by name."""
        path = self.sfx.get(name)
        if path is None or not path.exists():
            return

        self.sfx_player.setSource(QUrl.fromLocalFile(str(path.resolve())))
        self.sfx_output.setVolume(max(0.0, min(1.0, volume)))
        self.sfx_player.play()
