# -*- coding: utf-8 -*-

# This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK for Python.
# Please visit https://alexa.design/cookbook for additional examples on implementing slots, dialog management,
# session persistence, api calls, and more.
# This sample is built using the handler classes approach in skill builder.
import logging
import ask_sdk_core.utils as ask_utils
import os
from ask_sdk_s3.adapter import S3Adapter
s3_adapter = S3Adapter(bucket_name=os.environ["S3_PERSISTENCE_BUCKET"])

import tweet_out
import tweepy
import sign_in
import twitter_handler
import check_existing_users
import get_auth_url
import verify_pin

from secrets import *
from check_existing_users import account_threads

import time
import json
from urllib3.connectionpool import xrange

from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_intent_name

from ask_sdk_model import Response
from ask_sdk_model.ui import SimpleCard
from ask_sdk_model.ui import StandardCard
from ask_sdk_model.interfaces.display import (
    ImageInstance, Image, RenderTemplateDirective,
    BackButtonBehavior, BodyTemplate2)
from ask_sdk_model import ui

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

#sign in once using the api
# api = sign_in.sign_in()

# account_threads = []
number_accounts = 0
twitter_username = "No Username"
auth_info = None


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        global number_accounts
        # type: (HandlerInput) -> Response
        
        # load accounts saved on file
        check_users = check_existing_users.check_existing_users(handler_input)
        number_accounts = check_users.return_account_numbers()
        
        speak_output = "Hello! Welcome to Multiple Tweet. Would you like to tweet something?"
        reprompt_text = "You can say, accounts, in order to see how many accounts you have active."
        
        card_title = "Multiple Tweet!"
        card_text = "Hello! Welcome to Multiple Tweet. Would you like to tweet something?"
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt_text)
                .set_card(StandardCard("Multiple Tweet!", "<Insert QR Image Here>", Image("https://s3.amazonaws.com/icepick-alexa/cow.jpg", "https://s3.amazonaws.com/icepick-alexa/cow.jpg")))
                .response
        )

class CaptureTweetIntentHandler(AbstractRequestHandler):
    """Handler for Capture Tweet Intent."""
    # global api
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        #This change ensures that the canHandle() function will be invoked when a CaptureTweetIntent request comes through.
        return ask_utils.is_intent_name("CaptureTweetIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        # get the tweet from the slots and display it
        slots = handler_input.request_envelope.request.intent.slots
        TextToTweet = slots["TextToTweet"].value
        speak_output = 'I will tweet out, {TextToTweet} from all accounts!'.format(TextToTweet=TextToTweet)
        reprompt_text = "Would you like to tweet something?"
        
        # tweet out to all accounts
        # only saves last one (edit later)
        succesful = False
        for i in account_threads:
            succesful = i.tweet(TextToTweet)
        if succesful:
            card_title = "Multiple Tweet!"
            card_text = "You tweeted something!"
            return (
                handler_input.response_builder
                    .speak(speak_output)
                    # .ask(reprompt_text)
                    .set_card(SimpleCard(card_title, card_text))
                    .response
                )
        else :
            return (
                handler_input.response_builder
                    .speak("You already tweeted this!")
                    # .ask(reprompt_text)
                    .response
            )

class HasLastTweetIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        attr = handler_input.attributes_manager.persistent_attributes
        #attributes_are_present = ("latest tweet" in attr)
        attributes_are_present = ("Accounts" in attr)
        return ask_utils.is_intent_name("HasLastTweetIntent")(handler_input)
        
    def handle(self, handler_input):
        attr = handler_input.attributes_manager.persistent_attributes
        # latest_tweet = attr['latest tweet']
        latest_account = attr['Accounts'][0]['Username']
        #speak_output = "Your last tweet that I posted was... '{latest_tweet}'".format(latest_tweet=latest_tweet)
        speak_output = "Your account information is... '{latest_account}'".format(latest_account=latest_account)
        reprompt_text = "Would you like to tweet something?"
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt_text)
                .response
        )

class LastTweetIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("LastTweetIntent")(handler_input)
        
    def handle(self, handler_input):
        slots = handler_input.request_envelope.request.intent.slots
        twitter_name = slots["TwitterName"].value
        # check to see if theres any accounts, if there are just use the first one to retrieve the tweet
        if len(account_threads) == 0:
            speak_output = "You have 0 accounts. Add a new account by saying \"new\""
        else:
            succesful = account_threads[0].latest_tweets(twitter_name)
            if succesful:
                their_tweet = account_threads[0].return_tweet()
                speak_output = "@{} latest tweet was {}".format(twitter_name, their_tweet)
            else:
                speak_output = "Error fetching their tweet."
        reprompt_text = "Would you like to view someone's latest tweet?"
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt_text)
                .response
        )

class AccountsIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AccountsIntent")(handler_input)
        
    def handle(self, handler_input):
        global number_accounts
        
        if number_accounts == 0:
            speak_output = "You have 0 accounts. Add a new account by saying \"new\""
        else:
            # get all of the names that we have of the accounts we read (delete the extra whitespace and comma [mlg coding here btw])
            list_of_account_names = ""
            temp = 1
            for i in account_threads:
                list_of_account_names += "( "
                list_of_account_names += str(temp)
                list_of_account_names += " ). "
                list_of_account_names += i.return_username()
                list_of_account_names += ". "
                temp += 1
            list_of_account_names = list_of_account_names[:-2]
            # speak_output = "You have {} account(s). The username(s) are {}".format(number_accounts, list_of_account_names)
            speak_output = "You have {} account(s). The username(s) are {}".format(len(account_threads), list_of_account_names)
        reprompt_text = "You can add a new account by saying \"new\""
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt_text)
                .set_card(StandardCard("Multiple Tweet!", "Accounts!", Image("https://s3.amazonaws.com/icepick-alexa/cow.jpg", "https://s3.amazonaws.com/icepick-alexa/cow.jpg")))
                .response
        )

class TweetFromIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("TweetFromIntent")(handler_input)
        
    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        if number_accounts == 0:
            speak_output = "You must first add an account, say \"new\" to add one."
            return (
                handler_input.response_builder
                    .speak(speak_output)
                    # .ask(reprompt_text)
                    .response
                )
        else:
            slots = handler_input.request_envelope.request.intent.slots
            # get account numbers from input and retrieve numbers only
            TextToTweet = slots["TextToTweet"].value
            temp_account = slots["AccountNumbers"].value
            valid_accounts = get_valid_ids(temp_account)
            print(valid_accounts)
            
            if len(valid_accounts) == 0:
                speak_output = "You must choose a valid account ID. Say \"accounts\" to view them."
                return (
                    handler_input.response_builder
                    .speak(speak_output)
                    # .ask(reprompt_text)
                    .response
                )
            
            # get the name of the accounts we're tweeting from
            list_of_account_names = ""
            for i in valid_accounts:
                list_of_account_names += account_threads[i-1].return_username()
                list_of_account_names += ", "
            list_of_account_names = list_of_account_names[:-2]
            print(TextToTweet)
            
            # display only the names of the accounts we're tweeting from
            # speak_output = "I will tweet out, {TextToTweet} from {}".format(TextToTweet=TextToTweet, list_of_account_names)
            speak_output = "I will tweet out \"{}\" from {}".format(TextToTweet, list_of_account_names)
            
            # only saves last one (edit later)
            succesful = False
            for i in valid_accounts:
                succesful = account_threads[i-1].tweet(TextToTweet)
                
            if succesful:
                return (
                    handler_input.response_builder
                        .speak(speak_output)
                        # .ask(reprompt_text)
                        .response
                    )
            else :
                return (
                    handler_input.response_builder
                        .speak("I was not able to tweet from all accounts that you mentioned.")
                        # .ask(reprompt_text)
                        .response
                )

# check if the pin they entered works with the url 
class NewUserIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("NewUserIntent")(handler_input)
        
    def handle(self, handler_input):
        global auth_info
        
        # auth_info[0] contains the auth and auth_info[1] contains the url
        auth_info = get_auth_url.get_auth_url(C_KEY, C_SECRET)
        speak_output = "Your authorization url is, {} . Please say, pin, followed by your pin to connect your account.".format(auth_info[1])
        # speak_output = "Adding new account"
        reprompt_text = "You can add a new account by saying \"new\""
        card_title = "URL and QR code"
        # card_text = "The url is {}".format(auth_info[1])
        card_text = "The url is hi!"
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt_text)
                #.set_card(SimpleCard(card_title, card_text))
                .response
        )

# check if the pin they entered works with the url 
class NewPinIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("NewPinIntent")(handler_input)
        
    def handle(self, handler_input):
        global number_accounts
        global auth_info
        
        # get pin and verify it
        slots = handler_input.request_envelope.request.intent.slots
        PIN = slots["PIN"].value
        verification_of_pin = verify_pin.verify_pin(auth_info, PIN, handler_input)
        successful = verification_of_pin.return_success()
        # print("The pin is: ",PIN," and it was successful: ",successful)
        # then save them to the file so they wont have to sign in again
        #<code goes here>
        reprompt_text = "You can add a new account by saying \"new\" and getting a new url and pin."
        
        if successful:
            speak_output = "You successfully connected your account!"
        else:
            speak_output = "There was an error connecting your account."
        return (
            handler_input.response_builder
                .speak(speak_output)
                #.ask(reprompt_text)
                .response
        )

class RemoveAccountIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("RemoveAccountIntent")(handler_input)
        
    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        keys = handler_input.attributes_manager.persistent_attributes
        
        if number_accounts == 0:
            speak_output = "You must first add an account, say \"new\" to add one."
            return (
                handler_input.response_builder
                    .speak(speak_output)
                    # .ask(reprompt_text)
                    .response
                )
        else:
            slots = handler_input.request_envelope.request.intent.slots
            # get account numbers from input and retrieve numbers only
            temp_account = slots["AccountNumbers"].value
            valid_accounts = get_valid_ids(temp_account)
            print(valid_accounts)
            
            if len(valid_accounts) == 0:
                speak_output = "You must choose a valid account ID. Say \"accounts\" to view them."
                return (
                    handler_input.response_builder
                    .speak(speak_output)
                    # .ask(reprompt_text)
                    .response
                )
            
            # get the name of the accounts we're removing from
            list_of_account_names = ""
            for i in valid_accounts:
                list_of_account_names += account_threads[i-1].return_username()
                list_of_account_names += ", "
            list_of_account_names = list_of_account_names[:-2]
            # display only the names of the accounts we're removing
            speak_output = "Removing {} from saved accounts.".format(list_of_account_names)
            
            # remove accounts here and save updated list to s3
            print("OLD KEYS: ", keys)
            new_keys = remove_account(valid_accounts, keys)
            save_to_s3(handler_input, new_keys)
            #attributes_manager = handler_input.attributes_manager
            #attributes_manager.persistent_attributes = new_keys
            #attributes_manager.save_persistent_attributes()
            #print("NEW KEYS: ", new_keys)
            
            # dummy variable must find a way to check if it was succesful
            #------------------------------------------------------------
            succesful = True;
            reprompt_text = "Error, try getting a new url and entering the pin again."
            if succesful:
                return (
                    handler_input.response_builder
                        .speak(speak_output)
                        .ask(reprompt_text)
                        .response
                    )
            else :
                return (
                    handler_input.response_builder
                        .speak("I was not able to remove all accounts that you mentioned.")
                        .ask(reprompt_text)
                        .response
                )

# get only the numbers and once we have them make sure theyre within the number of id's we have
def get_valid_ids(temp_account):
    account_ids = [int(i) for i in temp_account.split() if i.isdigit()]
    for x in account_ids:
        if x<=0 or x>number_accounts:
            account_ids.remove(x)
    return account_ids

# removes account from list, s3 bucket, and kills the thread handling that account
def remove_account(valid_accounts, keys):
    global number_accounts
    
    if(len(valid_accounts)>0):
        for x in valid_accounts:
            try:
                # kill the thread
                account_threads[x-1].kill_thread()
            except IndexError:
                pass
            # remove from json list
            new_keys = remove_from_json(account_threads[x-1], keys)
            # remove from account list
            del account_threads[x-1]
            number_accounts -= 1
    return new_keys

# remove account from s3 bucket
def remove_from_json(account, keys):
    for i in xrange(len(keys['Accounts'])):
        # print(keys['Accounts'][i]['Username'], "\n", account.return_username())
        if keys['Accounts'][i]["Username"] == account.return_username():
            # print("It is in the list. Lets remove it.")
            del keys['Accounts'][i]
            break
    return keys

# save to s3 bucket
def save_to_s3(handler_input, new_keys):
    attributes_manager = handler_input.attributes_manager
    attributes_manager.persistent_attributes = new_keys
    attributes_manager.save_persistent_attributes()

class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "You can say tweet or tweet out, followed by whatever you'd like to tweet. For example... tweet out Hello World!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Exiting Multiple Tweet"
        for i in account_threads:
            i.kill_thread()
            time.sleep(.5)
        account_threads.clear()
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Exiting Multiple Tweet"
        for i in account_threads:
            i.kill_thread()
            time.sleep(.5)
        account_threads.clear()
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.


sb = CustomSkillBuilder(persistence_adapter=s3_adapter)

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(CaptureTweetIntentHandler())
sb.add_request_handler(HasLastTweetIntentHandler())
sb.add_request_handler(LastTweetIntentHandler())
sb.add_request_handler(AccountsIntentHandler())
sb.add_request_handler(TweetFromIntentHandler())
sb.add_request_handler(NewUserIntentHandler())
sb.add_request_handler(NewPinIntentHandler())
sb.add_request_handler(RemoveAccountIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()