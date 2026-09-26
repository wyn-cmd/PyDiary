# PyDiary
A CLI application written in python. PyDiary creates encrypted entries that can be written, viewed and deleted inside the terminal.

Requires the `cryptography` package: `pip install cryptography`.

Each diary keeps its own random salt, so two diaries protected by the same password do not share a key. The password itself is never stored: an encrypted marker is written once at setup and checked again on every unlock, so a wrong password is refused immediately rather than accepted and only discovered later when an entry fails to decrypt.
