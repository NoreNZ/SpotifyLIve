import requests
import time
import urllib.request
import cv2
import numpy as np
from datetime import datetime, timedelta
import time
from googleapiclient.discovery import build
import pprint
import os

from pprint import pprint
from urllib.parse import quote
from PIL import Image, ImageOps, ImageDraw, ImageFont, ImageFilter, ImageChops

#requests
#urllib
#cv2

# Set working directory
os.chdir("images")

#Spotify secrets
SPOTIFY_GET_CURRENT_TRACK_URL = 'https://api.spotify.com/v1/me/player/currently-playing'
refresh_token = "REFRESHTOKEN"
base_64 = 'BASE64'

#Google secrets
google_api_key = "GOOGLEAPIKEY"
google_cse_id = "GOOGLECSEID"

#Function gets current track from Spotify API
def get_current_track(access_token):
    #GET request
    response = requests.get(
        SPOTIFY_GET_CURRENT_TRACK_URL,
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )
    #Initialise variables we want to retrieve
    image = ""
    track_id = ""
    track_name = ""
    artists = ""
    image = ""

    #Try to fetch information
    try:
        #Assign json response
        json_resp = response.json()
        #Set track id
        track_id = json_resp['item']['id']
        #Set track name
        track_name = json_resp['item']['name']
        #Set track artists
        artists = [artist for artist in json_resp['item']['artists']]
        #Set track image
        image = json_resp['item']['album']['images'][0]['url']
    except:
        pass

    #append artists into string
    artist_names = ', '.join([artist['name'] for artist in artists])

    #Create array with song information
    current_track_info = {
    	"id": track_id,
    	"track_name": track_name,
    	"artists": artist_names,
        "image_link": image
    }

    #Return array
    return current_track_info

#Function for retrieving images based on search term
def google_search(search_term):
    #Intialize empty variable for search engine to function
    image = None
    #Append album cover to search term to generate full search term for an album cover
    search_term = (search_term + "album cover")
    service = build("customsearch", "v1", developerKey=google_api_key)
    #Retrieve first image from google search
    res = service.cse().list(q=search_term, cx=google_cse_id, searchType=image, num=1).execute()
    #return the url of the retrieved image
    return(res['items'][0]['pagemap']['metatags'][0]['og:image'])

#Refresh Spotify Access token (60 minute duration)
def call_refresh():
    #Post request
    response = requests.post("https://accounts.spotify.com/api/token",
                                data={"grant_type": "refresh_token",
                                    "refresh_token": refresh_token},
                                headers={"Authorization": "Basic " + base_64})

    response_json = response.json()
    print(response_json)

    #return refreshed access token
    return response_json["access_token"]


def main():
    #Initialize variables
    current_track_name = None
    image_url = ""
    cover_x = 0

    #Set current time at runtime
    current_time = datetime.now()
    #Set time of refresh (55 mins from time of launch)
    refresh_time = current_time + timedelta(minutes=55)

    #Initialize dropshadow effect image
    dropshadow = Image.open('dropshadow.png')

    #Generate Spotify access token and runtime
    access_token = str(call_refresh())
    while True:
        #Get current track info
        current_track_info = get_current_track(access_token)
        #Update current time
        current_time = datetime.now()

        #If current track name has changed run the following
        if current_track_info['track_name'] != current_track_name:
            pprint(
                current_track_info,
                indent=4,
            )
            #Fetch image url of song
            image_url = current_track_info['image_link']
            #Open url and save image as temp.jpg
            if image_url != "":
                with urllib.request.urlopen(image_url) as url:
                    with open('temp.jpg', 'wb') as f:
                        f.write(url.read())
                #Open saved image as img
                img = Image.open('temp.jpg')
            #If no image url retrieved, in the case of offline songs in a Spotify playlist, do the following
            if image_url == "":
                #Fetch the song name
                song_name = (current_track_info['track_name'])
                #Truncate song name to 20 characters
                search_term = song_name[0:20]
                try:
                    #Try to open an existing saved image for this song
                    img = Image.open(search_term +'.jpg')
                    print('Local Image Opened')
                except:
                    try:
                        #If image doesn't exist, fetch from google (100 queries per day)
                        google_url = google_search(search_term)
                        print("New Image Fetched: " + google_url)
                        #Open fetched google image url and save locally as the truncated song name
                        with urllib.request.urlopen(google_url) as url:
                            with open(search_term + '.jpg', 'wb') as f:
                                f.write(url.read())
                        #Open the saved image
                        img = Image.open(search_term + '.jpg')
                    except:
                        #If all the above fails, open blank song image e.g. when all search queries are used
                        img = Image.open('blank.jpg')
                
                #Scale image to 630x630 in the case that fetched image is of different dimensions
                img = ImageOps.fit(img, size = (630,630))
            #Initialize cv2 window to display images
            cv2.namedWindow("cover", cv2.WINDOW_NORMAL)
            cv2.setWindowProperty("cover", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)

            #blurImage is the Gaussian blurred background version of the song image
            #blurImage is resized song cover to 1920x1920
            blurImage = img.resize(size = (1920,1920),resample=Image.BOX)
            #Gaussian effect applied to image
            blurImage = blurImage.filter(ImageFilter.GaussianBlur(20))
            #Create new blank image to work onto
            final_img = Image.new('RGBA', (1920,1080), (0, 0, 0, 255))
            #Resize song image
            img = img.resize(size = (900,900))
            #Paste gaussian blur onto final img
            final_img.paste(blurImage, (0,-300))
            #Paste dropshadow effect onto final img
            final_img.paste(dropshadow, (0-cover_x,0), dropshadow)
            #Paste song image onto final image
            final_img.paste(img, (960-450-cover_x,540-450))
            #Save final image as temp.png
            final_img.save("temp.png", format="png")

            #Open final image and display
            img = cv2.imread('temp.png')
            cv2.imshow('cover',img)

            cv2.waitKey(1)

        #Within loop, constantly update current track name, if this updates, the above loop will start again
        current_track_name = current_track_info['track_name']

        #Check if current time is greater than refresh time, if it is generate a new access token
        if current_time >= refresh_time:
            access_token = str(call_refresh())
            #Update new refresh time
            refresh_time = current_time + timedelta(minutes=55)

        k = cv2.waitKey(1) & 0xFF
        # press 'q' to exit
        if k == ord('q'):
            break

    time.sleep(1)


if __name__ == '__main__':
    main()