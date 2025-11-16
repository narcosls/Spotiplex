from configparser import ConfigParser

config = ConfigParser()
config.read('config.txt')

def get_users():
    users_tokens = config['users']['tokens'].split(',')
    users = [user.split(':')[0] for user in users_tokens]
    return users
