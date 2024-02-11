from setuptools import setup
from make_icons import make_iconset

VERSION = "0.2.0"
APP = ["ethermemo.py"]
OPTIONS = {
    "argv_emulation": True,
    "plist": {
        "LSUIElement": True,
    },
    "packages": ["rumps", "pydantic"],
    "iconfile": make_iconset("icon.png", "ethermemo.iconset"),
}

setup(
    name="ethermemo",
    description="macOS app to save track titles on the internet radio",
    version=VERSION,
    app=APP,
    data_files=[],
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
