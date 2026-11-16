import requests
import json

import os
from dotenv import load_dotenv
load_dotenv(dotenv_path=r"D:\Downloads\python project\.env")
API_KEY = os.getenv("API_KEY")
CHANNEL_HANDLE = "MrBeast"

#print("ENV file loaded:", os.path.exists("./.env"))
#print("API key found:", bool(API_KEY))
#print("API key length:", len(API_KEY) if API_KEY else 0)

def get_playlist_id():
    try:
        url = f"https://youtube.googleapis.com/youtube/v3/channels?part=contentDetails&forHandle={CHANNEL_HANDLE}&key={API_KEY}" 

        response = requests.get(url)

        response.raise_for_status()  # Raise an exception for HTTP errors

        data = response.json()
        #print(json.dumps(data, indent=4))

        channel_items = data['items'][0]
        channel_playlist_id = channel_items['contentDetails']['relatedPlaylists']['uploads']
        print(f"Channel Playlist ID: {channel_playlist_id}")
        return channel_playlist_id

    except requests.exceptions.RequestException as e:
        raise e
    
if __name__ == "__main__":
    get_playlist_id()
