A simple macOS app which lets you save song titles you liked on your favourite internet radio stations.

Shows current song playing on your chosen radio station. Clicking 'Like this!' saves the song title. Also, you can write optional comments for the songs. All data is stored locally, nothing is sent anywhere.

Currently, the app only works with ICY metadata.

# Requirements

- python3
- pydantic
- rumps
- py2app

# Installation

After cloning the repository, run

```shell
python setup.py py2app -A
```

This will create a macOS app bundle and put it into `dist/` folder in the repo directory. Then, just drop that app to your Applications folder.

# Ideas

- Look liked songs up on your favourite streaming service and add them to your playlist
- Support other metadata