import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element
import typing
import io
from functools import partial


class PlayerBank:
    def __init__(self, data: io.BytesIO):
        self.data = data
        self.tree = ET.parse(self.data)
        self.root = self.tree.getroot()
        self.player_section = self.root.find("Section[@name='Player']")
        self.last_game_section = self.root.find("Section[@name='LG']")
        self.modes = {}
        # Default to handle 10385601fc8a4c9b939d9db802563ce6
        self.last_game = {}

        modes = ['1v1', '1v1v1v1', '2v2v2v2', '3v3v3v3', '2v2']
        _mode_key = partial(self.get_mode_key, self.player_section)
        for mode in modes:
            payload = {
                'wins': _mode_key(mode, 'wins', 'int'),
                'games': _mode_key(mode, 'games', 'int'),
                'elo': _mode_key(mode, 'elo', 'fixed'),
                'history': _mode_key(mode, 'history', 'string'),
            }
            payload['losses'] = int(payload['games']) - int(payload['wins'])
            self.modes[mode] = payload

        if self.last_game_section is None:
            # Resolve sentry 10385601fc8a4c9b939d9db802563ce6
            return

        lg_mode = self.get_key(self.last_game_section, 'mode')
        winning_team = self.get_key(self.last_game_section, 'winningteam')
        _mode_key = partial(self.get_key, self.last_game_section)
        lg_time = self.get_key(self.last_game_section, 'time', 'int')
        players = {}
        for p in range(1, 12):
            id = _mode_key(f'p{p}handle', 'string')
            if id is None:
                continue

            games = _mode_key(f'p{p}games', 'int')
            wins = _mode_key(f'p{p}wins', 'int')
            elo = _mode_key(f'p{p}elo', 'fixed')
            history = _mode_key(f'p{p}history', 'string')
            team = _mode_key(f'p{p}team', 'int')
            position = _mode_key(f'p{p}position', 'int')
            players[id] = {
                'wins': wins,
                'games': games,
                'elo': elo,
                'history': history,
                'team': team,
                'position': position,
            }
            if games is not None and wins is not None:
                players[id]['losses'] = str(int(games) - int(wins))  # Back as str for consistency

        self.last_game = {'mode': lg_mode, 'winning_team': winning_team, 'players': players, 'time': lg_time}

    def get_key(self, section: Element, key: str, value_type: str = "string") -> typing.Optional[str]:
        value = section.find(f"Key[@name='{key}']/Value")
        if isinstance(value, Element):
            return value.attrib.get(value_type)

    def get_mode_key(self, section: Element, mode: str, key: str, value_type: str = "string") -> str:
        value = self.get_key(section, f"{key}{mode}", value_type)
        return value if value is not None else "0"

    @property
    def id(self):
        return self.get_key(self.player_section, 'handle')

    @property
    def stubborn_mode(self):
        return self.get_key(self.player_section, 'stubborn_mode', 'flag') == 1

    @property
    def games(self):
        return self.get_key(self.player_section, 'games', 'int')

    @property
    def wins(self):
        return self.get_key(self.player_section, 'wins', 'int')

    @property
    def losses(self):
        return int(self.games) - int(self.wins)