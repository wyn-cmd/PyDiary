#!/usr/bin/python3


# Import modules
import os
import sys
import time
import base64
import shutil
import random
import getpass
import hashlib
from cryptography.fernet import Fernet

# Functions

# Clear
def cls():
    i = 0
    wid = ''
    wid_num = 0
    try:
        os.system('clear')
    except Exception:
        os.system('cls')
    term = os.get_terminal_size()
    wid_num = int(term[0]) - 13
    for i in range(wid_num):
        wid += ' '
    print(f'\033[7;38m --PyDiary-- {wid}\n\033[0;0m\n')
    return


# List files in the directory
def list_files(directory):
    os.system(f'echo " " >> .pydiary/list')
    os.remove('.pydiary/list')
    try:
        os.system(f'ls {directory} >> .pydiary/list')
    except Exception:
        os.system(f'dir {directory} >> .pydiary/list')
    return


def animate(tasks):
    num12=0
    while num12<random.randint(4,5):
        sys.stdout.write('\r'+tasks+' |')
        sys.stdout.flush()
        time.sleep(0.1)
        sys.stdout.write('\r'+tasks+' /')
        sys.stdout.flush()
        time.sleep(0.1)
        sys.stdout.write('\r'+tasks+' -')
        sys.stdout.flush()
        time.sleep(0.1)
        sys.stdout.write('\r'+tasks+' \\')
        sys.stdout.flush()
        time.sleep(0.1)
        num12+=1


# Define the encrypt function
def encrypt(data, key):
    output = Fernet(key).encrypt(data.encode('utf-8'))
    return(output)


# Define the decrypt function
def decrypt(data, key):
    output = Fernet(key).decrypt(data)
    return(output)






# Password check
cls()
try:
    open('.pydiary/pass.dat', 'r').read()
    password = getpass.getpass('Password:')
except Exception:
    print('***Enter your password for encryption***\n')
    password = getpass.getpass('Password:')
    os.system('mkdir .pydiary/')
    os.system('echo "true" >> .pydiary/pass.dat')
key = base64.b64encode((hashlib.md5(password.encode('utf-8')).hexdigest()).encode('utf-8'))

# Start the loop
try:
    open('.pydiary/check.dat', 'r').read()
except Exception:
    os.system('mkdir .pydiary/')
    os.system('mkdir .pydiary/entries/')
    os.system('echo "true" .pydiary/check.dat')

while True:
    # Print interface
    cls()
    choice = input('\n\n    [1] Add entry\n    [2] View entries\n    [3] Wipe\n    [q] exit\n\n\n\n> ')
    # Add a new entry
    if choice == '1':
        cls()
        title = input('Enter title: ')
        entry = input('Entry: ')
        file_data = encrypt(entry, key)
        os.system(f'echo "text" >> .pydiary/entries/{title}')
        open('.pydiary/entries/' + title, 'wb').write(file_data)
        input('Entry written!')
    # Read an entry
    elif choice == '2':
        cls()
        list_files('.pydiary/entries/')
        print(open('.pydiary/list', 'r').read())
        title = input('\n\n>')
        file_data = open(f'.pydiary/entries/{title}', 'rb').read()
        entry = (decrypt(file_data, key)).decode('utf-8')
        cls()
        print(' --' + title + '--')
        input('\n   ' + entry + '\n\n\n')
    elif choice == '3':
        cls()
        shutil.rmtree('.pydiary/')
        print('\n\n')
        animate('Wiping...')
        input('\n\n\nEntries Wiped\n\n\n')

    elif choice == 'q':
        cls()
        print('quitting...')
        sys.exit()
