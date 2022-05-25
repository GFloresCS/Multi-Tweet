import tweepy
import pyqrcode
import png
# import pypng

# return both auth and authurl since we'll need to verify them with a pin
def get_auth_url(C_KEY, C_SECRET):
    auth = tweepy.OAuthHandler(C_KEY, C_SECRET)
    auth_url = auth.get_authorization_url()
    
    # Create and save the png file naming "myqr.png"
    url = pyqrcode.create(auth_url)
    png_url = '/tmp/myqr.png'
    url.png(png_url, scale=6)
    return auth, auth_url