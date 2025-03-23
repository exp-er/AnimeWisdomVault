import streamlit as st
import pandas as pd
import requests
from datetime import date
import firebase_admin
from firebase_admin import credentials, firestore

st.set_page_config(page_title="AnimeWisdomVault", layout="centered")

# ==== CONFIG ====
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1s-FATTwfzFUS2gdAjbjNrCKUg1GeCWnhzdzDYLea8Zc/export?format=csv"
import os

FIREBASE_CRED_PATH = (
    "/etc/secrets/firebase-service-account.json"
    if os.environ.get("RENDER")
    else "secrets/firebase-service-account.json"
)
FIREBASE_COLLECTION = "anime_quotes"

# ==== INIT FIREBASE ====
@st.cache_resource
def init_firebase():
    cred = credentials.Certificate(FIREBASE_CRED_PATH)
    firebase_admin.initialize_app(cred)
    return firestore.client()

db = init_firebase()

# ==== LOAD GOOGLE SHEET ====
@st.cache_data
def load_quotes_from_google_sheet():
    df = pd.read_csv(SHEET_CSV_URL)
    df.dropna(subset=["Quote"], inplace=True)
    return df

# ==== LOAD FROM FIRESTORE ====
@st.cache_data
def load_quotes_from_firestore():
    docs = db.collection(FIREBASE_COLLECTION).stream()
    return [doc.to_dict() for doc in docs]

# ==== STREAMLIT APP ====
st.title("Anime Wisdom Vault")

# ==== SYNC BUTTON ====
# if st.button("📤 Sync Google Sheet → Firebase"):
#     sheet_df = load_quotes_from_google_sheet()
#     new_quotes = sheet_df.to_dict(orient="records")

#     existing_quotes = load_quotes_from_firestore()
#     existing_texts = {q["Quote"] for q in existing_quotes}

#     added = 0
#     for quote in new_quotes:
#         if quote["Quote"] not in existing_texts:
#             db.collection(FIREBASE_COLLECTION).add(quote)
#             added += 1

#     st.success(f"✅ Synced! {added} new quote(s) added.")
#     st.cache_data.clear()  # clear cached data so display updates immediately

# ==== LOAD & DISPLAY FIREBASE QUOTES ====
quotes = load_quotes_from_firestore()
df = pd.DataFrame(quotes)

# === Quote of the Day ===
st.subheader("🗓️ Quote of the Day")
if not df.empty:
    qod = df.loc[hash(str(date.today())) % len(df)]
    st.info(f"**{qod['Quote']}**\n\n— *{qod['Character']}*, {qod['Anime']}")

# === Filters ===
st.sidebar.title("🔍 Filter Quotes")
anime_list = sorted(df["Anime"].dropna().unique())
character_list = sorted(df["Character"].dropna().unique())

selected_anime = st.sidebar.multiselect("Filter by Anime", anime_list)
selected_character = st.sidebar.multiselect("Filter by Character", character_list)
search_term = st.sidebar.text_input("Search in Quotes")

filtered_df = df.copy()
if selected_anime:
    filtered_df = filtered_df[filtered_df["Anime"].isin(selected_anime)]
if selected_character:
    filtered_df = filtered_df[filtered_df["Character"].isin(selected_character)]
if search_term:
    filtered_df = filtered_df[filtered_df["Quote"].str.contains(search_term, case=False, na=False)]

# === Display ===
st.subheader("📜 Quotes")
st.write(f"Showing {len(filtered_df)} quote(s):")
for _, row in filtered_df.iterrows():
    st.markdown(f"> *{row['Quote']}*\n> — **{row['Character']}**, _{row['Anime']}_")
    st.markdown("---")
