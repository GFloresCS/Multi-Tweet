import os.path
import json
import twitter_handler
import tweepy
from secrets import *

from ask_sdk_s3.adapter import S3Adapter
s3_adapter = S3Adapter(bucket_name=os.environ["S3_PERSISTENCE_BUCKET"])

account_threads = []

# if the file exists then see how many accounts there are, else create a new json file
class check_existing_users:
    keys_unique = None
    number_accounts = 0

    def __init__(self, handler_input):
        attr = handler_input.attributes_manager.persistent_attributes
        # attributes_are_present = ("Accounts" in attr)
        print("We are checking for existing users. Please stand by.")
        if  attr is not None:
            print("File with accounts found.")
            # open the file check for duplicates, once duplicates are deleted then overwrite the file
            # and see how many accounts are in there, if it was empty then dont increment account count either
            self.keys_unique = {'Accounts': list(self.no_duplicates(attr))}
            # print("***Problem?", self.keys_unique)
            
            # print(self.keys_unique['Accounts'])
            # for every account, make a twitter handler and keep track of the number of accounts
            for x in self.keys_unique['Accounts']:
                # print(x," Access Token: ", x['Access Token'], "\nAccess Secret: ", x['Access Token Secret'])
                auth = tweepy.OAuthHandler(C_KEY, C_SECRET)
                account_threads.append(twitter_handler.twitter_handler(x['Access Token'], x['Access Token Secret'], auth))
                account_threads[-1].start()
            self.number_accounts = len(account_threads)
            print(self.number_accounts, " read from file.")
            
            # write to file in case deleted cuplicates
            attributes_manager = handler_input.attributes_manager
            attributes_manager.persistent_attributes = self.keys_unique
            attributes_manager.save_persistent_attributes()
            
                
        else:
            print("File Does Not Exist or it had zero accounts.\nCreating new keys.json file to store account information.")
            no_keys = {'Accounts': []}
            #write to file
            print(no_keys)
            attributes_manager = handler_input.attributes_manager
            attributes_manager.persistent_attributes = no_keys
            attributes_manager.save_persistent_attributes()

    def return_account_numbers(self):
        return self.number_accounts

    @staticmethod
    def no_duplicates(keys):
        seen = []
        for x in keys['Accounts']:
            if x not in seen:
                yield x
                seen.append(x)
        unique_keys = {'Accounts': seen}
        return unique_keys
        