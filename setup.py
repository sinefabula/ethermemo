from setuptools import setup
from make_icons import make_iconset

VERSION = "0.1.0"
APP = ["ethermem.py"]
OPTIONS = {
    "argv_emulation": True,
    "plist": {
        "LSUIElement": True,
    },
    "packages": ["rumps", "pydantic"],
    "iconfile": make_iconset("icon.png", "ethermem.iconset"),
}

setup(
    name="ethermem",
    description="macOS app to save track titles on the internet radio",
    version=VERSION,
    app=APP,
    data_files=[],
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
