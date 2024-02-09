import rumps
from pydantic import BaseModel
from typing import List, Optional
import requests
import time
from datetime import datetime


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
    next_in: int


class Metadata:
    last_update: Optional[int]

    def __init__(self, config: AppConfig):
        self.config = config
        self.last_update = None
        self.valid = False

    def update(self) -> Result:
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
            next_in = self.config.update_interval
        else:
            next_in = int(self.last_update + self.config.update_interval - now)
        return Result(
            title=self.title,
            valid=self.valid,
            next_in=next_in,
            stamp=int(self.last_update),
        )

    @staticmethod
    def _parse_title(b: bytes) -> str:
        s = b.rstrip(b"\x00").decode()
        index = s.find("StreamTitle=")
        if index == -1:
            return "<NOT_FOUND>"
        quote_index = index + len("StreamTitle=")
        start = quote_index + 1
        quote = s[quote_index]
        end = s.find(quote + ";")
        if end == -1:
            # Can't find it but let's return SOMETHING at least.
            return s[start:]
        return s[start:end]

    def retrieve_title(self) -> str:
        resp = requests.get(self.config.url, headers={"Icy-MetaData": "1"}, stream=True)
        resp.raw.read(int(resp.headers["icy-metaint"]))
        meta = resp.raw.read(16 * ord(resp.raw.read(1)))
        return self._parse_title(meta)


class EthermemApp(rumps.App):
    last_result: Result

    def __init__(self):
        super(EthermemApp, self).__init__("Ethermem", icon="ethermem.icns")
        self.config = AppConfig()
        try:
            with self.open(APP_CONFIG) as f:
                self.config = AppConfig.model_validate_json(f.read())
        except FileNotFoundError:
            pass
        self.now_playing_item = rumps.MenuItem("Now playing")
        self.menu = [
            self.now_playing_item,
            f"Radio: {self.config.url}",
            "Like this!",
            "Comment...",
            "Show liked",
            "Change radio station...",
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
        self.track_list = rumps.Window(title="Liked tracks", ok=None, cancel=None)
        self.timer = rumps.Timer(self.tick, 1)
        self.timer.start()

    def tick(self, sender):
        self.last_result = self.metadata.update()
        if self.last_result.valid:
            prefix = ""
        else:
            prefix = "[!]"
        self.now_playing_item.title = f"{prefix}{self.last_result.title}"

    @rumps.clicked("Like this!")
    def like(self, sender):
        if self.last_result.valid:
            self._save_liked(comment="")

    @rumps.clicked("Comment...")
    def comment(self, sender):
        if self.last_result.valid:
            resp = self.comment_dialogue.run()
            if resp.clicked:
                self._save_liked(comment=resp.text)

    @rumps.clicked("Show liked")
    def show_saved(self, sender):
        tracks = "\n".join([str(track) for track in self._load_liked()])
        self.track_list.default_text = tracks
        self.track_list.run()

    @rumps.clicked("Change radio station...")
    def change_station(self, sender):
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
    EthermemApp().run()
