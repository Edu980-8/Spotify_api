import json
import os
import base64
from requests import post, get
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

class SpotifyAPI:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = self.get_token()

    def get_token(self):
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode("utf-8")
        auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")
        url = "https://accounts.spotify.com/api/token"
        headers = {
            "Authorization": f"Basic {auth_base64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"grant_type": "client_credentials"}
        response = post(url, headers=headers, data=data)
        json_result = json.loads(response.content)
        token = json_result["access_token"]
        return token

    def get_auth_header(self):
        return {"Authorization": f"Bearer {self.token}"}

    def available_markets(self):
        url = "https://api.spotify.com/v1/markets"
        headers = self.get_auth_header()
        response = get(url, headers=headers)
        json_result = json.loads(response.content)["markets"]
        return json_result

    def get_genres(self):
        url = "https://api.spotify.com/v1/recommendations/available-genre-seeds"
        headers = self.get_auth_header()
        response = get(url, headers=headers)
        json_result = json.loads(response.content)["genres"]
        return json_result

    def get_playlist_id(self, region, genre): # Esta es la playlist que contiene las top 50 canciones de un pais
        top_tracks_url = f"https://api.spotify.com/v1/search"
        headers = self.get_auth_header()
        query = f"?q=Top+50+{region}&type=playlist&limit=1"
        query_url = top_tracks_url + query 

        response = get(query_url, headers=headers)

        json_result = json.loads(response.content)
        if response.status_code == 200 and json_result:
            json_result = response.json()
            playlist_id = json_result['playlists']['items'][0]['id']
            return playlist_id, genre
        else:
            print(f"Error: Unable to retrieve top tracks for {genre} in {region}. Status code: {response.status_code}")
            return None

    def get_playlist_tracks(self, playlist_id):
        url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        headers = self.get_auth_header()
        response = get(url, headers=headers)
        json_result = json.loads(response.content)
        return json_result

    def get_genre_by_artist(self, artist_id):
        url = f"https://api.spotify.com/v1/artists/{artist_id}"
        headers = self.get_auth_header()
        response = get(url, headers=headers)
        json_result = json.loads(response.content)["genres"]
        return json_result

if __name__ == "__main__":
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_ SECRET")

    spotify_api = SpotifyAPI(client_id, client_secret)

    print("Your client ID is:", client_id, "and your client secret is:", client_secret)

    regions = spotify_api.available_markets()#All the posible regions
    print("These are the available regions:", regions)

    genres = spotify_api.get_genres()
    print("These are the available genres:", genres) # All the available genres

    region_selected = input("Please select one of the above regions(just try with CO, i have to fix the other available regions dinamically), only type one of the codes shown before: ").upper()

playlist_id = spotify_api.get_playlist_id(region_selected, "all")[0]  

if playlist_id is not None:
    tracks = spotify_api.get_playlist_tracks(playlist_id)['items']
    tracks_data=[]

    for index, track in enumerate(tracks):
        track_genres = spotify_api.get_genre_by_artist(tracks[index]['track']['artists'][0]['id'])
        track_artist = ', '.join([artist['name'] for artist in track['track']['artists']])
        track_name = track['track']['name']

        # if track_genres:
        #     print(f"{index + 1}. {track['track']['name']} - {', '.join([artist['name'] for artist in track['track']['artists']])} ({', '.join(track_genres)})")
        # else:
        #     print(f"{index + 1}. {track['track']['name']} - {', '.join([artist['name'] for artist in track['track']['artists']])} (Unknown)")

        tracks_data.append({
                'Track Name': track['track']['name'],
                'Track Artist': track_artist,
                'Track Genre': track_genres
            })
        
    df = pd.DataFrame(tracks_data)
    print(df)
    
    
    split = pd.DataFrame(df['Track Genre'].to_list(), columns = ['Genre_1', 'Genre_2','Genre_3', 'Genre_4','Genre_5', 'Genre_6'])
    df = pd.concat([df, split], axis=1) 
    print(df)
    
    genre_columns = ['Genre_1', 'Genre_2', 'Genre_3', 'Genre_4', 'Genre_5', 'Genre_6']

    for column in genre_columns:
        unique_values = df[column].unique()
        
        for value in unique_values:
            songs_df = df[df[column] == value]
            filename = f"{value}.csv"
            songs_df.to_csv(filename, index=False)
    
else:
    print(f"The execution failed because the specified region {region_selected} does not exist. Please rerun the script and try with the available options.")

