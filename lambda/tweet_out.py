import tweepy
from secrets import *

def tweet(api, text):
    try:
        api.update_status(text)
        return True
    except:
        return False