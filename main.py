#!/usr/bin/python3

import os
import sys
import time
import base64
import shutil
import random
import getpass
import hashlib
from cryptography.fernet import Fernet


def cls():
    try:
        os.system('clear')
    except Exception:
        os.system('cls')
    
    try:
        term_width = os.get_terminal_size().columns
    except Exception:
        term_width = 80
        
    wid_num = max(0, term_width - 13)
    wid = ' ' * wid_num
    print(f'\033[7;38m --PyDiary-- {wid}\n\033[0;0m\n')


def list_files(directory):
    list_path = os.path.join('.pydiary', 'list')
    os.makedirs('.pydiary', exist_ok=True)
    
    try:
        with open(list_path, 'w') as f:
            entries = os.listdir(directory)
            for entry in entries:
                f.write(entry + '\n')
    except Exception:
        try:
            os.system(f'ls {directory} > {list_path}')
        except Exception:
            os.system(f'dir {directory} > {list_path}')


def animate(tasks):
    frames = ['|', '/', '-', '\\']
    for _ in range(random.randint(4, 5)):
        for frame in frames:
            sys.stdout.write(f'\r{tasks} {frame}')
            sys.stdout.flush()
            time.sleep(0.1)


def encrypt(data, key):
    return Fernet(key).encrypt(data.encode('utf-8'))


def decrypt(data, key):
    return Fernet(key).decrypt(data)


# Initialize data directory
os.makedirs('.pydiary/entries', exist_ok=True)

# Password setup and authentication
pass_path = os.path.join('.pydiary', 'pass.dat')
cls()

if os.path.exists(pass_path):
    password = getpass.getpass('Password: ')
else:
    print('***Enter your password for encryption***\n')
    password = getpass.getpass('Password: ')
    with open(pass_path, 'w') as f:
        f.write('true')

key = base64.b64encode(hashlib.md5(password.encode('utf-8')).hexdigest().encode('utf-8'))

# Ensure check file exists
check_path = os.path.join('.pydiary', 'check.dat')
if not os.path.exists(check_path):
    with open(check_path, 'w') as f:
        f.write('true')


# Main application loop
while True:
    cls()
    choice = input('\n\n    [1] Add entry\n    [2] View entries\n    [3] Wipe\n    [q] exit\n\n\n\n> ')
    
    if choice == '1':
        cls()
        title = input('Enter title: ')
        entry = input('Entry: ')
        if title:
            file_data = encrypt(entry, key)
            entry_path = os.path.join('.pydiary', 'entries', title)
            with open(entry_path, 'wb') as f:
                f.write(file_data)
            input('Entry written!')
        else:
            input('Title cannot be empty!')
    
    elif choice == '2':
        cls()
        entries_dir = os.path.join('.pydiary', 'entries')
        list_files(entries_dir)
        list_path = os.path.join('.pydiary', 'list')
        if os.path.exists(list_path):
            with open(list_path, 'r') as f:
                print(f.read())
        
        title = input('\n\n>')
        entry_path = os.path.join('.pydiary', 'entries', title)
        if os.path.exists(entry_path):
            with open(entry_path, 'rb') as f:
                file_data = f.read()
            entry = decrypt(file_data, key).decode('utf-8')
            cls()
            print(' --' + title + '--')
            input('\n   ' + entry + '\n\n\n')
        else:
            input('Entry not found!')
    
    elif choice == '3':
        cls()
        if os.path.exists('.pydiary'):
            shutil.rmtree('.pydiary')
        print('\n\n')
        animate('Wiping...')
        input('\n\n\nEntries Wiped\n\n\n')
        sys.exit()

    elif choice == 'q':
        cls()
        print('quitting...')
        sys.exit()