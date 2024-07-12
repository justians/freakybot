from requests import post
import json
import streamlit as st
from openai import OpenAI
from serpapi import GoogleSearch
import base64
import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

client_id = st.secrets["CLIENT_ID"]
client_secret = st.secrets["CLIENT_SECRET"]

def get_token():
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")
    
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64, 
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    result = post(url, headers=headers, data=data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token

token = get_token()

def get_auth_header(token):
    return {"Authorization": "Bearer " + token}

# Function to search Spotify
def search_spotify(query, token):
    url = "https://api.spotify.com/v1/search"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    params = {
        "q": query,
        "type": "track",
        "limit": 1
    }
    response = requests.get(url, headers=headers, params=params)
    return response.json()

# Function to get recommendations based on a seed track
def get_recommendations(seed_track_id, token):
    url = f"https://api.spotify.com/v1/recommendations"
    headers = get_auth_header(token)
    params = {
        "seed_tracks": seed_track_id,
        "limit": 5  # Adjust limit as needed
    }
    response = requests.get(url, headers=headers, params=params)
    return response.json()

# Set up Streamlit app
st.title("Song Search Chatbot")

# Initialize OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Function to perform web search
def web_search(query, num_results=3):
    search = GoogleSearch({
        "q": query,
        "api_key": st.secrets["SERPAPI_API_KEY"],
        "num": num_results
    })
    results = search.get_dict()
    organic_results = results.get("organic_results", [])

    search_results = []
    for result in organic_results[:num_results]:
        title = result.get('title', 'No title')
        # Extracting the artist name from the result
        artist = 'No artist'  # Default value if artist is not found
        if 'rich_snippet' in result:
            rich_snippet = result['rich_snippet']
            if 'top' in rich_snippet and 'extensions' in rich_snippet['top']:
                extensions = rich_snippet['top']['extensions']
                if len(extensions) > 1:
                    artist = extensions[1]

        search_results.append(f"Title: {title}\nArtist: {artist}")

    return search_results

# Streamlit UI for user input
song_query = st.text_input("Enter the name of the song:")

selected_song = None  # Initialize selected_song variable

if song_query:
    # Generate a search query
    search_query = f"{song_query} song"
    
    # Perform web search
    search_results = web_search(search_query, num_results=3)
    
    st.subheader("Search Results:")
    if search_results:
        selected_song = st.radio("Select a song:", search_results)
        
        if selected_song:
            st.write(f"You selected:\n{selected_song}")
            print(f"Selected song: {selected_song}")
    else:
        st.write("No results found.")

#############################################################

if selected_song:
    # Search Spotify
    spotify_results = search_spotify(selected_song, token)
    
    # Display Spotify search results
    if spotify_results and 'tracks' in spotify_results and spotify_results['tracks']['items']:
        track_info = spotify_results['tracks']['items'][0]
        track_name = track_info['name']
        artist_name = track_info['artists'][0]['name']
        seed_track_id = track_info['id']

        # Display Spotify result more prominently
        st.subheader("Spotify Result:")
        st.write(f"Track: {track_name}")
        st.write(f"Artist: {artist_name}")
        st.image(track_info['album']['images'][0]['url'], caption='Album Cover', use_column_width=True)

        # Example of using get_recommendations function
        st.subheader("Getting Recommendations...")
        recommendations = get_recommendations(seed_track_id, token)

        if recommendations and 'tracks' in recommendations:
            st.write("Recommendations:")
            for rec_track in recommendations['tracks']:
                rec_track_name = rec_track['name']
                rec_artist_name = rec_track['artists'][0]['name']
                st.write(f"Track: {rec_track_name}, Artist: {rec_artist_name}")
        else:
            st.write("No recommendations found.")
    else:
        st.write("No results found on Spotify.")
