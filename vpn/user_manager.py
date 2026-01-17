import json
import os

class UserManager:
    def __init__(self, users_file='users.json'):
        self.users_file = users_file
        self.load_users()

    def load_users(self):
        if os.path.exists(self.users_file):
            with open(self.users_file, 'r') as f:
                self.users = json.load(f)
        else:
            self.users = {}

    def save_users(self):
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f, indent=4)

    def add_user(self, username, folder, cert_file, key_file):
        self.users[username] = {
            'folder': folder,
            'cert_file': cert_file,
            'key_file': key_file
        }
        self.save_users()

    def get_user(self, username):
        return self.users.get(username)

    def list_users(self):
        return list(self.users.keys())