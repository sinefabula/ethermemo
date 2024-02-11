import rumps
from rumps import MenuItem
from pydantic import BaseModel
from typing import List, Optional
import requests
import time
from datetime import datetime
import subprocess
import os


APP_CONFIG = "config.json"
APP_LIKED = "liked_tracks.json"


class AppConfig(BaseModel):
    url: str = "https://q2stream.wqxr.org/q2"
    update_interval: int = 5


class Track(BaseModel):
    title: str
    comment: str = ""
    stamp: int

    def __str__(self):
        ts = datetime.fromtimestamp(self.stamp).strftime("%c")
        if self.comment:
            comment = f' "{self.comment}'
        else:
            comment = ""
        return f"{ts} {self.title}{comment}"


class SavedTracks(BaseModel):
    tracks: List[Track] = []


class Result(BaseModel):
    title: str
    valid: bool
    stamp: int


class Metadata:
    last_update: Optional[int]

    def __init__(self, config: AppConfig):
        self.config = config
        self.last_update = None
        self.valid = False

    def update(self) -> Result:
        """Updates the song metadata if there is none or enough time
        (`config.update_interval`) has passed since `last_udpate`."""
        now = int(time.time())
        if (
            self.last_update is None
            or now - self.last_update > self.config.update_interval
        ):
            try:
                self.title = self.retrieve_title()
                self.valid = True
            except Exception as e:
                self.title = str(e)
                self.valid = False
            self.last_update = now
        return Result(
            title=self.title,
            valid=self.valid,
            stamp=int(self.last_update),
        )

    @staticmethod
    def _parse_title(b: bytes) -> str:
        """Tries to parse the ICY metadata to extract the song title."""
        # The string is null-terminated so remove the trailing zeros first.
        s = b.rstrip(b"\x00").decode()
        # Then, the tags should be (in theory) encoded as semicolon-separated
        # key-value pairs, with value enclosed in quotes, e.g.
        # StreamTitle="A cool song";
        # In practice though, song titles can contain any characters and no
        # one cares about escaping quotes, `=`, and `;` and also those quotes
        # can be either single or double so we'll try to locate the beginning
        # of the tag, then check which opening quote we have and hope for the
        # best.
        index = s.find("StreamTitle=")
        if index == -1:
            return "<NOT_FOUND>"
        quote_index = index + len("StreamTitle=")
        start = quote_index + 1
        quote = s[quote_index]
        end = s.find(quote + ";")
        if end == -1:
            # Can't find the closing quote but let's return SOMETHING at least.
            return s[start:]
        return s[start:end]

    def retrieve_title(self) -> str:
        """Retrieves ICY metadata from the radio stream, then parses it trying
        to extract the song title."""
        resp = requests.get(self.config.url, headers={"Icy-MetaData": "1"}, stream=True)
        resp.raw.read(int(resp.headers["icy-metaint"]))
        meta = resp.raw.read(16 * ord(resp.raw.read(1)))
        return self._parse_title(meta)


class EthermemoApp(rumps.App):
    last_result: Result

    def __init__(self):
        super(EthermemoApp, self).__init__("Ethermemo", icon="ethermemo.icns")
        self.config = AppConfig()
        try:
            with self.open(APP_CONFIG) as f:
                self.config = AppConfig.model_validate_json(f.read())
        except FileNotFoundError:
            pass
        self.menu_now_playing = MenuItem("Now playing")
        self.menu = [
            self.menu_now_playing,
            f"Radio: {self.config.url}",
            MenuItem("Like this!", callback=self.like),
            MenuItem("Comment...", callback=self.comment),
            {
                "Liked tracks": [
                    MenuItem("Show", callback=self.liked_show),
                    MenuItem("Reveal in Finder", callback=self.liked_reveal),
                ]
            },
            MenuItem("Change radio station...", callback=self.change_station),
        ]
        self.metadata = Metadata(self.config)
        self.comment_dialogue = rumps.Window(
            title="Say something",
            message="What do you think of this track?",
            cancel="Cancel",
        )
        self.change_station_dialogue = rumps.Window(
            title="Change radio station",
            default_text=self.config.url,
            cancel="Cancel",
        )
        self.track_list_dialogue = rumps.Window(
            title="Liked tracks", ok=None, cancel=None
        )
        # Timer which updates the song metadata runs every second.
        self.timer = rumps.Timer(self.tick, 1)
        self.timer.start()

    def tick(self, sender):
        """Timer tick. Loads current song metadata and updates the song title
        in the menu."""
        self.last_result = self.metadata.update()
        if self.last_result.valid:
            prefix = ""
        else:
            prefix = "[!]"
        self.menu_now_playing.title = f"{prefix}{self.last_result.title}"

    def like(self, sender):
        """Saves the song title do the file."""
        if self.last_result.valid:
            self._save_liked(comment="")

    def comment(self, sender):
        """Invokes a dialogue window asking the user for commentary for the
        song to be saved."""
        if self.last_result.valid:
            resp = self.comment_dialogue.run()
            if resp.clicked:
                self._save_liked(comment=resp.text)

    def liked_show(self, sender):
        """Shows previously saved songs."""
        tracks = "\n".join([str(track) for track in self._load_liked().tracks])
        self.track_list_dialogue.default_text = tracks
        self.track_list_dialogue.run()

    def liked_reveal(self, sender):
        """Reveals the JSON file with saved songs in Finder."""
        path = os.path.join(self._application_support, APP_LIKED)
        subprocess.call(["open", "-R", path])

    def change_station(self, sender):
        """Invokes the dialogue window asking the user to enter ther URL to
        a new radio station."""
        resp = self.change_station_dialogue.run()
        if resp.clicked:
            self.config.url = resp.text
            self._save_config()

    def _save_config(self):
        with self.open(APP_CONFIG, "w") as w:
            w.write(self.config.model_dump_json())

    def _load_liked(self) -> SavedTracks:
        saved = SavedTracks()
        try:
            with self.open(APP_LIKED) as f:
                saved = SavedTracks.model_validate_json(f.read())
        except FileNotFoundError:
            pass
        return saved

    def _save_liked(self, comment: str):
        saved = self._load_liked()
        track = Track(
            title=self.last_result.title,
            stamp=self.last_result.stamp,
            comment=comment,
        )
        saved.tracks.append(track)
        with self.open(APP_LIKED, "w") as w:
            w.write(saved.model_dump_json())


if __name__ == "__main__":
    EthermemoApp().run()
