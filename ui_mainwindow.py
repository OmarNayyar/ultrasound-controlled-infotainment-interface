"""Main PyQt window for the ultrasound-controlled infotainment demo."""

from pathlib import Path
import os
import time

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QPalette, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from audio_manager import AudioManager
from serial_reader import SerialGestureReader
from state import (
    call_active,
    caller_names,
    caller_numbers,
    current_track,
    is_playing,
    playlist,
    repeat_on,
    shuffle_on,
    volume_level,
)


IMAGES_DIR = Path(__file__).resolve().parent / "assets" / "images"
DEFAULT_SERIAL_PORT = os.getenv("ULTRASONIC_SERIAL_PORT", "COM4")
DEFAULT_BAUDRATE = int(os.getenv("ULTRASONIC_BAUDRATE", "9600"))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Ultrasound-Controlled Infotainment Interface")
        self.resize(1000, 480)

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(3, 3, 5))
        self.setPalette(palette)

        self.base_map_pix = None
        self.map_label = None

        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.nav_frame = self.create_nav_frame()
        layout.addWidget(self.nav_frame, stretch=3)

        self.media_frame = self.create_media_frame()
        layout.addWidget(self.media_frame, stretch=2)

        self.call_popup = self.create_call_popup()
        self.call_popup.hide()

        self.incall_screen = self.create_incall_screen()
        self.incall_screen.hide()
        self.incall_active = False
        self.call_start_ts = 0
        self.was_playing_before_call = False
        self.call_index = 0

        self.call_timer = QTimer(self)
        self.call_timer.setInterval(25_000)
        self.call_timer.timeout.connect(self.trigger_fake_call)
        self.call_timer.start()

        self.incall_timer = QTimer(self)
        self.incall_timer.setInterval(1000)
        self.incall_timer.timeout.connect(self.update_incall_timer)
        self.incall_timer.start()

        self.clock_timer = QTimer(self)
        self.clock_timer.setInterval(1000)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start()

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.audio = AudioManager()

        self.update_media_labels()
        self.update_buttons()
        self.update_clock()

        if is_playing:
            self.audio.play_track(current_track, volume_level)

        self.serial_reader = SerialGestureReader(
            port=DEFAULT_SERIAL_PORT,
            baudrate=DEFAULT_BAUDRATE,
            callback=self.handle_gesture,
        )

        self.serial_timer = QTimer(self)
        self.serial_timer.setInterval(20)
        self.serial_timer.timeout.connect(self.serial_reader.poll)
        self.serial_timer.start()

    def create_nav_frame(self) -> QFrame:
        frame = QFrame()
        frame.setAutoFillBackground(True)

        palette = frame.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(15, 15, 20))
        frame.setPalette(palette)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        title = QLabel("Navigation")
        title.setStyleSheet("color: white;")
        title.setFont(QFont("Arial", 14))
        layout.addWidget(title)

        map_card = QFrame()
        map_card.setStyleSheet(
            "background-color: #282c30; border-radius: 12px; padding: 8px;"
        )
        layout.addWidget(map_card, stretch=1)

        map_layout = QVBoxLayout(map_card)
        map_layout.setContentsMargins(4, 4, 4, 4)

        self.map_label = QLabel()
        self.map_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.map_label.setStyleSheet("border-radius: 10px;")
        map_layout.addWidget(self.map_label)

        map_path = IMAGES_DIR / "map.png"
        pix = QPixmap(str(map_path))
        if not pix.isNull():
            self.base_map_pix = pix
            self._update_map_pix()
        else:
            self.map_label.setText("Map image not found")
            self.map_label.setStyleSheet(
                "color: #aaaaaa; border-radius: 10px; border: 1px solid #444;"
            )

        return frame

    def _update_map_pix(self):
        if self.base_map_pix is None or self.map_label is None:
            return
        if self.map_label.width() <= 0 or self.map_label.height() <= 0:
            return

        scaled = self.base_map_pix.scaled(
            self.map_label.width(),
            self.map_label.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.map_label.setPixmap(scaled)

    def create_media_frame(self) -> QFrame:
        frame = QFrame()
        frame.setAutoFillBackground(True)

        palette = frame.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(3, 3, 5))
        frame.setPalette(palette)

        outer = QVBoxLayout(frame)
        outer.setContentsMargins(16, 8, 16, 8)
        outer.setSpacing(8)

        top_label = QLabel("Ultrasonic HMI Demo")
        top_label.setStyleSheet("color: white; font-size: 11px;")
        outer.addWidget(top_label)

        card = QFrame()
        card.setStyleSheet(
            "background-color: #14161a; border-radius: 12px; border: 1px solid #4a4f59;"
        )
        outer.addWidget(card)
        outer.setStretchFactor(card, 2)

        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(16)

        left = QVBoxLayout()
        left.setSpacing(10)
        card_layout.addLayout(left, stretch=3)

        self.track_label = QLabel()
        self.track_label.setStyleSheet(
            "color: white; font-size: 18px; font-weight: bold;"
        )
        left.addWidget(self.track_label)

        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: #00c000; font-size: 12px;")
        left.addWidget(self.status_label)

        controls_row = QHBoxLayout()
        controls_row.setSpacing(24)
        left.addLayout(controls_row)

        transport_style = """
            QPushButton {
                background-color: #20242a;
                border-radius: 20px;
                color: white;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #2a3033;
            }
        """

        self.prev_btn = QPushButton("<")
        self.play_btn = QPushButton("||")
        self.next_btn = QPushButton(">")

        for btn in (self.prev_btn, self.play_btn, self.next_btn):
            btn.setFixedSize(40, 40)
            btn.setStyleSheet(transport_style)

        controls_row.addWidget(self.prev_btn)
        controls_row.addWidget(self.play_btn)
        controls_row.addWidget(self.next_btn)

        self.prev_btn.clicked.connect(self.go_prev)
        self.play_btn.clicked.connect(self.toggle_play)
        self.next_btn.clicked.connect(self.go_next)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(12)
        left.addLayout(bottom_row)

        self.shuffle_btn = QPushButton("Shuffle")
        self.repeat_btn = QPushButton("Repeat")

        toggle_style = """
            QPushButton {
                background-color: #20242a;
                border-radius: 14px;
                padding: 4px 12px;
                color: #cccccc;
            }
            QPushButton:checked {
                background-color: #ff8c00;
                color: black;
            }
        """

        for btn in (self.shuffle_btn, self.repeat_btn):
            btn.setCheckable(True)
            btn.setStyleSheet(toggle_style)

        self.shuffle_btn.clicked.connect(self.toggle_shuffle)
        self.repeat_btn.clicked.connect(self.toggle_repeat)

        bottom_row.addWidget(self.shuffle_btn)
        bottom_row.addWidget(self.repeat_btn)

        vol_label = QLabel("Volume")
        vol_label.setStyleSheet("color: #bbbbbb;")
        bottom_row.addWidget(vol_label)

        self.vol_slider = QSlider(Qt.Orientation.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(volume_level)
        self.vol_slider.valueChanged.connect(self.volume_changed)
        bottom_row.addWidget(self.vol_slider, stretch=1)

        right = QVBoxLayout()
        right.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        card_layout.addLayout(right, stretch=1)

        self.logo_label = QLabel()
        self.logo_label.setFixedSize(80, 80)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo_path = IMAGES_DIR / "spotify_logo.webp"
        logo_pix = QPixmap(str(logo_path))
        if not logo_pix.isNull():
            logo_pix = logo_pix.scaled(
                self.logo_label.width(),
                self.logo_label.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.logo_label.setPixmap(logo_pix)
        else:
            self.logo_label.setStyleSheet(
                "background-color: #1db954; border-radius: 40px; color: black;"
            )
            self.logo_label.setText("Music")

        right.addWidget(self.logo_label)

        comm_card = QFrame()
        comm_card.setStyleSheet(
            "background-color: #14161a; border-radius: 12px; border: 1px solid #4a4f59;"
        )
        outer.addWidget(comm_card)
        outer.setStretchFactor(comm_card, 1)

        comm_layout = QVBoxLayout(comm_card)
        comm_title = QLabel("Communication")
        comm_title.setStyleSheet("color: white; font-size: 14px;")
        comm_sub = QLabel("Incoming-call simulation enabled")
        comm_sub.setStyleSheet("color: #a0a0a0;")
        comm_layout.addWidget(comm_title)
        comm_layout.addWidget(comm_sub)

        self.time_label = QLabel()
        self.time_label.setStyleSheet("color: white; font-size: 28px;")
        self.date_label = QLabel()
        self.date_label.setStyleSheet("color: #aaaaaa; font-size: 12px;")
        outer.addWidget(self.time_label, alignment=Qt.AlignmentFlag.AlignLeft)
        outer.addWidget(self.date_label, alignment=Qt.AlignmentFlag.AlignLeft)

        hint = QLabel(
            "Keyboard fallback: LEFT/RIGHT previous/next, SPACE play/pause, "
            "S shuffle, R repeat, UP accept call, DOWN reject or end."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #888888; font-size: 11px;")
        outer.addWidget(hint)

        return frame

    def create_call_popup(self) -> QFrame:
        popup = QFrame(self)
        popup.setStyleSheet(
            "background-color: #14161a; border-radius: 16px; border: 1px solid #4a4f59;"
        )
        popup.setFixedSize(420, 180)

        layout = QVBoxLayout(popup)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        title = QLabel("Incoming call")
        title.setStyleSheet("color: white; font-size: 16px;")
        layout.addWidget(title)

        self.call_name_label = QLabel("")
        self.call_name_label.setStyleSheet("color: white; font-size: 18px;")
        self.call_number_label = QLabel("")
        self.call_number_label.setStyleSheet("color: #aaaaaa; font-size: 12px;")

        layout.addWidget(self.call_name_label)
        layout.addWidget(self.call_number_label)

        hint = QLabel("Pull to accept | Push to reject")
        hint.setStyleSheet("color: #888888; font-size: 12px;")
        layout.addWidget(hint)

        popup.move(
            (self.width() - popup.width()) // 2,
            (self.height() - popup.height()) // 2,
        )
        return popup

    def create_incall_screen(self) -> QFrame:
        popup = QFrame(self)
        popup.setStyleSheet(
            "background-color: #111318; border-radius: 16px; border: 1px solid #4a4f59;"
        )
        popup.setFixedSize(440, 260)

        layout = QVBoxLayout(popup)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        self.avatar_label = QLabel("User")
        self.avatar_label.setFixedSize(100, 100)
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_label.setStyleSheet(
            "background-color: #d0b57a; border-radius: 50px; font-size: 20px; color: white;"
        )
        layout.addWidget(self.avatar_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.incall_name_label = QLabel("In call")
        self.incall_name_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.incall_name_label.setStyleSheet(
            "color: white; font-size: 20px; background: transparent;"
        )

        self.incall_number_label = QLabel("+971 .. .. .. ..")
        self.incall_number_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.incall_number_label.setStyleSheet(
            "color: #aaaaaa; font-size: 13px; background: transparent;"
        )

        self.incall_duration_label = QLabel("00:00")
        self.incall_duration_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.incall_duration_label.setStyleSheet(
            "color: #00c000; font-size: 15px; background: transparent;"
        )

        layout.addWidget(self.incall_name_label)
        layout.addWidget(self.incall_number_label)
        layout.addWidget(self.incall_duration_label)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(20)
        layout.addLayout(btn_row)

        def round_btn(text, bg, fg="white"):
            button = QPushButton(text)
            button.setFixedSize(70, 70)
            button.setStyleSheet(
                f"QPushButton {{ background-color: {bg}; color: {fg}; "
                "border-radius: 35px; font-size: 14px; }}"
            )
            return button

        self.hangup_btn = round_btn("End", "#c00000")
        self.hangup_btn.clicked.connect(self.end_call)

        self.mute_btn = round_btn("Mute", "#20242a")
        self.mute_btn.setCheckable(True)
        self.mute_btn.setStyleSheet(
            "QPushButton { background-color: #20242a; color: #dddddd; border-radius: 35px; font-size: 14px; } "
            "QPushButton:checked { background-color: #ff8c00; color: black; }"
        )

        self.keypad_btn = round_btn("Keypad", "#20242a")
        self.addcall_btn = round_btn("Add\nCall", "#20242a")

        btn_row.addWidget(self.hangup_btn)
        btn_row.addWidget(self.mute_btn)
        btn_row.addWidget(self.keypad_btn)
        btn_row.addWidget(self.addcall_btn)

        popup.move(
            (self.width() - popup.width()) // 2,
            (self.height() - popup.height()) // 2,
        )
        return popup

    def update_media_labels(self):
        global current_track, playlist, is_playing
        self.track_label.setText(playlist[current_track])
        if is_playing:
            self.status_label.setText("Playing")
            self.status_label.setStyleSheet("color: #00c000; font-size: 12px;")
            self.play_btn.setText("||")
        else:
            self.status_label.setText("Paused")
            self.status_label.setStyleSheet("color: #ff8c00; font-size: 12px;")
            self.play_btn.setText(">")

    def update_buttons(self):
        global shuffle_on, repeat_on
        self.shuffle_btn.setChecked(shuffle_on)
        self.repeat_btn.setChecked(repeat_on)

    def update_clock(self):
        self.time_label.setText(time.strftime("%H:%M"))
        self.date_label.setText(time.strftime("%d %b"))

    def go_prev(self):
        global current_track, is_playing
        current_track = (current_track - 1) % len(playlist)
        self.update_media_labels()
        if is_playing:
            self.audio.play_track(current_track, volume_level)

    def go_next(self):
        global current_track, is_playing
        current_track = (current_track + 1) % len(playlist)
        self.update_media_labels()
        if is_playing:
            self.audio.play_track(current_track, volume_level)

    def toggle_play(self):
        global is_playing
        is_playing = not is_playing
        if is_playing:
            self.audio.resume_music()
        else:
            self.audio.pause_music()
        self.update_media_labels()

    def toggle_shuffle(self):
        global shuffle_on
        shuffle_on = not shuffle_on
        self.update_buttons()

    def toggle_repeat(self):
        global repeat_on
        repeat_on = not repeat_on
        self.update_buttons()

    def volume_changed(self, value: int):
        global volume_level
        volume_level = value
        self.audio.set_volume(volume_level)

    def trigger_fake_call(self):
        global call_active, is_playing
        if call_active or self.incall_active:
            return

        self.was_playing_before_call = is_playing
        if is_playing:
            is_playing = False
            self.audio.pause_music()
            self.update_media_labels()

        call_active = True
        self.audio.play_sfx("incoming")

        name = caller_names[self.call_index]
        number = caller_numbers[self.call_index]
        self.call_index = (self.call_index + 1) % len(caller_names)

        self.call_name_label.setText(name)
        self.call_number_label.setText(f"{number} calling")
        self.call_popup.show()
        self.call_popup.raise_()

    def update_incall_timer(self):
        if not self.incall_active or self.call_start_ts == 0:
            return
        elapsed = int(time.time() - self.call_start_ts)
        mins, secs = divmod(elapsed, 60)
        self.incall_duration_label.setText(f"{mins:02d}:{secs:02d}")

    def end_call(self):
        global is_playing

        self.incall_active = False
        self.call_start_ts = 0
        self.incall_screen.hide()
        print("Call ended")
        self.audio.play_sfx("end")

        if self.was_playing_before_call:
            is_playing = True
            self.update_media_labels()
            self.audio.resume_music()
            self.was_playing_before_call = False

    def accept_call(self):
        global call_active
        if not call_active:
            return

        call_active = False
        self.call_popup.hide()

        self.incall_name_label.setText(self.call_name_label.text())
        number_text = self.call_number_label.text().replace(" calling", "")
        self.incall_number_label.setText(number_text)
        self.incall_duration_label.setText("00:00")

        self.call_start_ts = time.time()
        self.incall_active = True
        self.incall_screen.show()
        self.incall_screen.raise_()
        print("Call accepted")
        self.audio.play_sfx("accept")

    def reject_call(self):
        global call_active, is_playing
        if not call_active:
            return

        call_active = False
        self.call_popup.hide()
        self.incall_screen.hide()
        self.incall_active = False
        self.call_start_ts = 0
        print("Call rejected")
        self.audio.play_sfx("reject")

        if self.was_playing_before_call:
            is_playing = True
            self.update_media_labels()
            self.audio.resume_music()
            self.was_playing_before_call = False

    def keyPressEvent(self, event):
        global call_active

        if event.key() == Qt.Key.Key_Left:
            if not call_active and not self.incall_active:
                self.go_prev()
        elif event.key() == Qt.Key.Key_Right:
            if not call_active and not self.incall_active:
                self.go_next()
        elif event.key() == Qt.Key.Key_Space:
            if not call_active and not self.incall_active:
                self.toggle_play()
        elif event.key() == Qt.Key.Key_S:
            self.toggle_shuffle()
        elif event.key() == Qt.Key.Key_R:
            self.toggle_repeat()
        elif event.key() == Qt.Key.Key_Up:
            if call_active:
                self.accept_call()
        elif event.key() == Qt.Key.Key_Down:
            if call_active:
                self.reject_call()
            elif self.incall_active:
                self.end_call()
            else:
                self.toggle_play()
        else:
            super().keyPressEvent(event)

    def resizeEvent(self, event):
        self._update_map_pix()
        super().resizeEvent(event)

    def handle_gesture(self, gesture: str):
        """Map serial gestures onto the same actions available from the keyboard."""
        global call_active

        command = gesture.strip().upper()
        print(f"[Gesture] {command}")

        if call_active and not self.incall_active:
            if command == "PULL":
                self.accept_call()
            elif command == "PUSH":
                self.reject_call()
            return

        if self.incall_active:
            if command == "PUSH":
                self.end_call()
            return

        if command == "SWIPE_LEFT":
            self.go_prev()
        elif command == "SWIPE_RIGHT":
            self.go_next()
        elif command == "PUSH":
            self.toggle_play()
