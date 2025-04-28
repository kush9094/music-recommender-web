# app.py

import streamlit as st
import random
import json
import os
from collections import Counter
import numpy as np
from sklearn.cluster import KMeans

# ====== Constants ======
USERS_FILE = "user_profiles.json"

songs_dataset = [
    {"song_name": "Stronger", "artist": "Kanye West", "genre": "Hip Hop", "mood": "motivational", "activity": "gym"},
    {"song_name": "Blinding Lights", "artist": "The Weeknd", "genre": "Pop", "mood": "energetic", "activity": "party"},
    {"song_name": "Someone Like You", "artist": "Adele", "genre": "Soul", "mood": "sad", "activity": "study"},
    {"song_name": "Happy", "artist": "Pharrell Williams", "genre": "Pop", "mood": "happy", "activity": "party"},
    {"song_name": "Lose Yourself", "artist": "Eminem", "genre": "Hip Hop", "mood": "motivational", "activity": "gym"},
    {"song_name": "Weightless", "artist": "Marconi Union", "genre": "Ambient", "mood": "calm", "activity": "study"},
    {"song_name": "Viva La Vida", "artist": "Coldplay", "genre": "Alternative", "mood": "energetic", "activity": "party"},
    {"song_name": "Lovely", "artist": "Billie Eilish", "genre": "Pop", "mood": "sad", "activity": "study"},
    {"song_name": "Don't Stop Me Now", "artist": "Queen", "genre": "Rock", "mood": "happy", "activity": "party"},
    {"song_name": "Circles", "artist": "Post Malone", "genre": "Pop", "mood": "calm", "activity": "study"}
]

# ====== Utility Functions ======

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def recommend_songs(mood, activity):
    matching_songs = [song for song in songs_dataset if song["mood"] == mood and song["activity"] == activity]
    return random.sample(matching_songs, min(5, len(matching_songs)))

def update_habits(user_profile, songs):
    for song in songs:
        user_profile['listening_history'].append({"mood": song['mood'], "artist": song['artist'], "activity": song['activity']})

def create_personalized_playlist(user_profile):
    history = user_profile['listening_history']
    if not history:
        return []
    mood_counter = Counter([item['mood'] for item in history])
    favorite_mood = mood_counter.most_common(1)[0][0]
    playlist = [song for song in songs_dataset if song['mood'] == favorite_mood]
    return playlist[:10]

def cluster_users(users):
    if len(users) < 2:
        return []
    features = []
    usernames = []
    for username, profile in users.items():
        mood_count = Counter([h['mood'] for h in profile['listening_history']])
        activity_count = Counter([h['activity'] for h in profile['listening_history']])
        feature = [
            mood_count.get('happy', 0),
            mood_count.get('sad', 0),
            mood_count.get('energetic', 0),
            mood_count.get('calm', 0),
            mood_count.get('motivational', 0),
            activity_count.get('gym', 0),
            activity_count.get('study', 0),
            activity_count.get('party', 0)
        ]
        features.append(feature)
        usernames.append(username)

    kmeans = KMeans(n_clusters=min(2, len(users)))
    labels = kmeans.fit_predict(np.array(features))
    return list(zip(usernames, labels))

# ====== Streamlit App ======

st.set_page_config(page_title="Music Recommendation System", page_icon=":musical_note:", layout="wide")

# Session state for login
if "username" not in st.session_state:
    st.session_state.username = None

users = load_users()

def login():
    st.title("Login or Register")

    login_choice = st.radio("Choose Action", ["Login", "Register"])

    if login_choice == "Login":
        username = st.text_input("Username")
        if st.button("Login"):
            if username in users:
                st.session_state.username = username
                st.success(f"Welcome back {username}!")
                st.experimental_rerun()
            else:
                st.error("Username not found.")
    else:
        new_username = st.text_input("Create Username")
        if st.button("Register"):
            if new_username in users:
                st.error("Username already exists.")
            else:
                users[new_username] = {
                    "favorite_mood": "",
                    "favorite_activity": "",
                    "listening_history": [],
                    "playlists": [],
                    "likes": 0
                }
                save_users(users)
                st.session_state.username = new_username
                st.success("Registration successful!")
                st.experimental_rerun()

def main_app():
    st.sidebar.title(f"Welcome, {st.session_state.username}!")
    menu = st.sidebar.radio("Menu", ["Home", "Get Recommendations", "My Playlist", "Public Playlists", "Cluster Users", "Feedback", "Logout"])

    if menu == "Home":
        st.title("Music Recommendation System")
        st.write("Get the best song suggestions based on your mood and activity!")

    elif menu == "Get Recommendations":
        st.header("Get Song Recommendations")
        mood = st.selectbox("Select Mood", ["happy", "sad", "energetic", "calm", "motivational"])
        activity = st.selectbox("Select Activity", ["gym", "study", "party"])

        if st.button("Recommend Songs"):
            recs = recommend_songs(mood, activity)
            if recs:
                st.success("Recommended Songs:")
                for song in recs:
                    st.write(f"- **{song['song_name']}** by *{song['artist']}*")
                update_habits(users[st.session_state.username], recs)
                save_users(users)
            else:
                st.warning("No matching songs found.")

    elif menu == "My Playlist":
        st.header("Your Personalized Playlist")
        playlist = create_personalized_playlist(users[st.session_state.username])
        if playlist:
            users[st.session_state.username]['playlists'] = playlist
            save_users(users)
            for song in playlist:
                st.write(f"- **{song['song_name']}** by *{song['artist']}*")
        else:
            st.warning("Not enough listening history yet.")

    elif menu == "Public Playlists":
        st.header("Public Playlists")
        for user, profile in users.items():
            if user != st.session_state.username and profile.get("playlists"):
                with st.expander(f"User: {user} (Likes: {profile.get('likes', 0)})"):
                    for song in profile["playlists"]:
                        st.write(f"- **{song['song_name']}** by *{song['artist']}*")
                    if st.button(f"Like {user}'s playlist", key=user):
                        users[user]['likes'] += 1
                        save_users(users)
                        st.success("Liked!")

    elif menu == "Cluster Users":
        st.header("User Clustering")
        cluster_result = cluster_users(users)
        if cluster_result:
            for username, cluster_id in cluster_result:
                st.write(f"**{username}** is in Cluster **{cluster_id}**")
        else:
            st.warning("Not enough users to cluster.")

    elif menu == "Feedback":
        st.header("Feedback")
        feedback = st.radio("Did you like the recommendations?", ["Yes", "No"])
        if st.button("Submit Feedback"):
            st.success("Thanks for your feedback!")

    elif menu == "Logout":
        st.session_state.username = None
        st.experimental_rerun()

# Routing
if st.session_state.username:
    main_app()
else:
    login()
