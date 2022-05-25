import threading
import tweepy

class twitter_handler(threading.Thread):
    user_response = ""
    api, username, access_k, access_s, tweet_to_return = None, None, None, None, None
    running = True

    # when called, set the access key and access secret as well as authorize the tweepy API
    # waiting on the limit makes it print a message and wait if the rate limit is exceeded
    def __init__(self, ACCESS_KEY, ACCESS_SECRET, auth):
        threading.Thread.__init__(self)
        self.access_k = ACCESS_KEY
        self.access_s = ACCESS_SECRET
        auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
        self.api = tweepy.API(auth, wait_on_rate_limit=True,
                              wait_on_rate_limit_notify=True)
        self.username = self.api.me().name

    def run(self):
        print("Successfully connected to account: ", self.username)
        while self.running:
            # pass does nothing, just there to keep it running
            pass
            # print(self.name, username, "\n")
            # print("Thread name: ", self.name)
        print("Exiting twitter handler for: ", self.username)
        
    def tweet(self, text):
        try:
            self.api.update_status(text)
        except tweepy.error.TweepError as e:
            print('Invalid tweet.')
            print(e.response.text)
            return False
        else:
            print(self.username, 'Tweeted :', text)
            return True

    def latest_tweets(self, name_of_user):
        try:
            user = self.api.get_user(name_of_user)
            for tweet in self.api.user_timeline(screen_name=user.screen_name, count=1, tweet_mode="extended"):
                print("\nDate:", tweet.created_at, "\nTweet:", tweet.full_text)
                self.tweet_to_return = tweet.full_text
            return True
        except tweepy.error.TweepError as e:
            print('Could not find user with Twitter Handle: @' + name_of_user)
            # print(e.reason)
            return False

    def return_tweet(self):
        return self.tweet_to_return

    def kill_thread(self):
        self.running = False
    
    def return_username(self):
        return self.username
