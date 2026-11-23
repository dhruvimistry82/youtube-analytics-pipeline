import requests
import json

import os
from dotenv import load_dotenv
load_dotenv(dotenv_path=r"D:\Downloads\python project\.env")
API_KEY = os.getenv("API_KEY")
CHANNEL_HANDLE = "MrBeast"
maxResults = 50
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



def  get_video_ids(playlistId):

    video_ids = []

    PageToken = None
    base_url = f"https://youtube.googleapis.com/youtube/v3/playlistItems?part=contentDetails&maxResults={maxResults}&playlistId={playlistId}&key={API_KEY}"

    try:

        while True:
            url = base_url

            if PageToken:
                url += f"&pageToken={PageToken}"

            response = requests.get(url)

            response.raise_for_status()  # Raise an exception for HTTP errors

            data = response.json()
            #print(json.dumps(data, indent=4))

            for item in data['items']:
                video_id = item['contentDetails']['videoId']
                video_ids.append(video_id)

            pageToken = data.get('nextPageToken')
            if not pageToken:
                break

            return video_ids
            

    except requests.exceptions.RequestException as e:
        raise e


def extract_video_data(video_ids):
    extracted_data = []

    def batch_list(video_id_list, batch_size=50):
        for i in range(0, len(video_id_list), batch_size):
            yield video_id_list[i:i + batch_size]

    try:
        for batch in batch_list(video_ids):
            video_ids_str = ','.join(batch)
            url = f"https://youtube.googleapis.com/youtube/v3/videos?part=contentDetails&part=snippet&part=statistics&id={video_ids_str}&key={API_KEY}"

            response = requests.get(url)

            response.raise_for_status()  # Raise an exception for HTTP errors

            data = response.json()
            #print(json.dumps(data, indent=4))

            for item in data.get('items', []):
                video_id = item['id']
                snippet = item['snippet']
                content_details = item['contentDetails']
                statistics = item['statistics']

                video_data = {
                        'video_id': video_id,
                        'title': snippet['title'],
                        
                        'published_at': snippet['publishedAt'],
                        'view_count':statistics.get('viewCount', None),
                        'like_count': statistics.get('likeCount', 0),
                        'comment_count': statistics.get('commentCount', 0)
                    }
                extracted_data.append(video_data)

        return extracted_data


    except requests.exceptions.RequestException as e:
        raise e


if __name__ == "__main__":
    playlist_id = get_playlist_id()
    video_ids = get_video_ids(playlist_id)
    extract_video_data(video_ids)
    
