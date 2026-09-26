#!/usr/bin/env python3

import os
import sys
import time
import shutil
import random
import getpass

import diary_core

ROOT = ".pydiary"


def cls():
    os.system("cls" if os.name == "nt" else "clear")

    try:
        term_width = os.get_terminal_size().columns
    except OSError:
        term_width = 80

    wid = " " * max(0, term_width - 13)
    print(f"\033[7;38m --PyDiary-- {wid}\n\033[0;0m\n")


def animate(tasks):
    frames = ["|", "/", "-", "\\"]
    for _ in range(random.randint(4, 5)):
        for frame in frames:
            sys.stdout.write(f"\r{tasks} {frame}")
            sys.stdout.flush()
            time.sleep(0.1)


def unlock():
    cls()
    if diary_core.diary_exists(ROOT):
        password = getpass.getpass("Password: ")
        key = diary_core.unlock_diary(ROOT, password)
        if key is None:
            # A wrong password used to unlock the diary anyway and only
            # blew up later trying to decrypt an entry. It is refused here,
            # at the door, instead.
            input("Wrong password.\n")
            sys.exit(1)
        return key

    print("***Choose a password for encryption***\n")
    password = getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        input("Passwords did not match.\n")
        sys.exit(1)
    return diary_core.setup_diary(ROOT, password)


def add_entry(key):
    cls()
    title = input("Enter title: ")
    entry = input("Entry: ")
    try:
        diary_core.write_entry(ROOT, key, title, entry)
    except ValueError:
        input("That title cannot be used as a file name.\n")
        return
    input("Entry written!")


def view_entries(key):
    cls()
    entries = diary_core.list_entries(ROOT)
    if entries:
        print("\n".join(entries))
    else:
        print("(no entries yet)")

    title = input("\n\n> ")
    text = diary_core.read_entry(ROOT, key, title)
    if text is None:
        input("Entry not found!")
        return
    cls()
    print(" --" + title + "--")
    input("\n   " + text + "\n\n\n")


def delete_entry():
    cls()
    entries = diary_core.list_entries(ROOT)
    if entries:
        print("\n".join(entries))
    else:
        print("(no entries yet)")

    title = input("\n\ndelete which entry? > ")
    if diary_core.delete_entry(ROOT, title):
        input("Entry deleted.\n")
    else:
        input("Entry not found!")


def wipe():
    cls()
    if os.path.exists(ROOT):
        shutil.rmtree(ROOT)
    print("\n\n")
    animate("Wiping...")
    input("\n\n\nEntries Wiped\n\n\n")
    sys.exit()


def main():
    key = unlock()

    while True:
        cls()
        choice = input(
            "\n\n    [1] Add entry\n    [2] View entries\n    [3] Delete entry\n"
            "    [4] Wipe\n    [q] exit\n\n\n\n> ")

        if choice == "1":
            add_entry(key)
        elif choice == "2":
            view_entries(key)
        elif choice == "3":
            delete_entry()
        elif choice == "4":
            wipe()
        elif choice == "q":
            cls()
            print("quitting...")
            sys.exit()


if __name__ == "__main__":
    main()
