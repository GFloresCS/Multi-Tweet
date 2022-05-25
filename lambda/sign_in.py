import tweepy
from secrets import *

def sign_in():
    auth = tweepy.OAuthHandler(C_KEY, C_SECRET)
    auth.set_access_token(A_TOKEN, A_SECRET)
    api = tweepy.API(auth)
    return api