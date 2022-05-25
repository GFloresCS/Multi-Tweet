import os.path
import tweepy
import twitter_handler
import json
from check_existing_users import account_threads
from ask_sdk_s3.adapter import S3Adapter
s3_adapter = S3Adapter(bucket_name=os.environ["S3_PERSISTENCE_BUCKET"])

class verify_pin:
    ACCESS_KEY, ACCESS_SECRET, username = None, None, None
    successful = False
    
    def __init__(self, auth_info, PIN, handler_input):
        auth = auth_info[0]
        # get the data saved in s3 to check if we're already signed in
        attr = handler_input.attributes_manager.persistent_attributes
        try:
            auth.get_access_token(PIN)
            self.ACCESS_KEY = auth.access_token
            self.ACCESS_SECRET = auth.access_token_secret
            # create a new thread and keep track of it, retrieve the username of the account
            account_threads.append(twitter_handler.twitter_handler(self.ACCESS_KEY, self.ACCESS_SECRET, auth))
            self.username = account_threads[-1].return_username()
            account_threads[-1].start()
            print('Successfully connected to account: ' + self.username)
            self.successful = True
        except tweepy.TweepError:
            print("Make sure the pin is typed correctly!\n")
        # if you can connect then check if we already have that account if we dont then add it to the s3 bucket
        if self.successful:
            if any(attr['Access Token'] == self.ACCESS_KEY for attr in attr['Accounts']):
                # duplicate = True
                self.successful = False
                account_threads[-1].kill_thread()
                print("You're already logged into this account.")
            
            # if its not a duplicate then add it to the json and save it to the s3 bucket
            if self.successful:
                temp_accounts = attr['Accounts']
                # print("***Before ", attr)
                temp_key = {
                    "Username": self.username,
                    "Access Token": self.ACCESS_KEY,
                    "Access Token Secret": self.ACCESS_SECRET
                }
                attr['Accounts'].append(temp_key)
                # print("***after ", attr)
                attributes_manager = handler_input.attributes_manager
                attributes_manager.persistent_attributes = attr
                attributes_manager.save_persistent_attributes()
                
    def return_username(self):
        return self.username

    def return_success(self):
        return self.successful
    