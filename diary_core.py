#!/usr/bin/env python3

# Diary storage and encryption, kept separate from the CLI so it can be
# tested without a terminal in the loop.

import base64
import os
import re
import secrets

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

SALT_FILE = "salt.dat"
CHECK_FILE = "check.dat"
ENTRIES_DIR = "entries"
KDF_ITERATIONS = 390000

# Marker encrypted with the real key at setup time and decrypted on every
# unlock. pass.dat in the original code only ever stored the word "true",
# so any password decrypted it and a wrong guess was not caught until the
# first real entry blew up with an uncaught InvalidToken. This is the fix:
# nothing here works unless the password produces the exact original key.
CHECK_MARKER = b"pydiary-check"


def derive_key(password, salt):
    # PBKDF2 rather than a bare MD5 hash, and a random salt per diary
    # instead of none, so two diaries with the same password do not
    # share a key and a captured key cannot be brute forced with a
    # generic MD5 rainbow table.
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32,
                      salt=salt, iterations=KDF_ITERATIONS)
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


def setup_diary(root, password):
    # First run: pick a salt, derive the key, and write the encrypted
    # marker that every later unlock will be checked against.
    os.makedirs(os.path.join(root, ENTRIES_DIR), exist_ok=True)
    salt = secrets.token_bytes(16)
    with open(os.path.join(root, SALT_FILE), "wb") as f:
        f.write(salt)
    key = derive_key(password, salt)
    with open(os.path.join(root, CHECK_FILE), "wb") as f:
        f.write(Fernet(key).encrypt(CHECK_MARKER))
    return key


def unlock_diary(root, password):
    # Returns the key on a correct password, or None on a wrong one.
    # Nothing about a bad password reaches the caller as an exception:
    # a wrong guess is an expected outcome here, not a bug.
    with open(os.path.join(root, SALT_FILE), "rb") as f:
        salt = f.read()
    key = derive_key(password, salt)
    with open(os.path.join(root, CHECK_FILE), "rb") as f:
        token = f.read()
    try:
        if Fernet(key).decrypt(token) != CHECK_MARKER:
            return None
    except InvalidToken:
        return None
    return key


def diary_exists(root):
    return os.path.exists(os.path.join(root, SALT_FILE))


# A title becomes a filename, so anything that could escape the entries
# directory (a slash, a leading dot, an empty result) is rejected outright
# rather than silently mangled: a title like "../../etc/passwd" must be
# refused, not quietly rewritten into something that happens to be safe.
_SAFE_TITLE = re.compile(r"^[^/\\\\]+$")


def safe_title(title):
    title = title.strip()
    if not title or title in (".", "..") or not _SAFE_TITLE.match(title):
        return None
    return title


def list_entries(root):
    entries_dir = os.path.join(root, ENTRIES_DIR)
    if not os.path.isdir(entries_dir):
        return []
    return sorted(os.listdir(entries_dir))


def write_entry(root, key, title, text):
    safe = safe_title(title)
    if safe is None:
        raise ValueError(f"not a usable title: {title!r}")
    path = os.path.join(root, ENTRIES_DIR, safe)
    data = Fernet(key).encrypt(text.encode("utf-8"))
    with open(path, "wb") as f:
        f.write(data)
    return path


def read_entry(root, key, title):
    safe = safe_title(title)
    if safe is None:
        return None
    path = os.path.join(root, ENTRIES_DIR, safe)
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        data = f.read()
    return Fernet(key).decrypt(data).decode("utf-8")


def delete_entry(root, title):
    # Removing one entry without touching the rest, since Wipe erasing
    # the whole diary over one unwanted line is a bad trade.
    safe = safe_title(title)
    if safe is None:
        return False
    path = os.path.join(root, ENTRIES_DIR, safe)
    if not os.path.exists(path):
        return False
    os.remove(path)
    return True
