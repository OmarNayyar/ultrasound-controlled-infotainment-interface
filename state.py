"""Shared UI state for the infotainment demo."""


class PlayerState:
    def __init__(self):
        self.playlist = [
            "Embedded Beats",
            "Haram Beats",
            "Debugging at Midnight",
            "Passionfruit",
            "Ohm My God (Too Much Resistance)",
        ]
        self.current_track = 2
        self.is_playing = True
        self.volume_level = 60
        self.shuffle_on = False
        self.repeat_on = False


class CallState:
    def __init__(self):
        self.call_active = False
        self.caller_names = [
            "Jinane",
            "Lab Instructor",
            "Dr. Omar Abdul-Latif",
            "Boutheina",
        ]
        self.caller_numbers = [
            "+971 50 123 4567",
            "+971 52 234 5678",
            "+971 54 345 6789",
            "+971 55 456 7890",
        ]


player_state = PlayerState()
call_state = CallState()

playlist = player_state.playlist
current_track = player_state.current_track
is_playing = player_state.is_playing
volume_level = player_state.volume_level
shuffle_on = player_state.shuffle_on
repeat_on = player_state.repeat_on

call_active = call_state.call_active
caller_names = call_state.caller_names
caller_numbers = call_state.caller_numbers
