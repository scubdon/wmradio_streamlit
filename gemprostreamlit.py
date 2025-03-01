import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from datetime import datetime
import io


# --- Data Loading and Preparation ---
def load_data(data):
    """Loads and preprocesses the music data."""
    df = pd.read_csv(data)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["date"] = df["timestamp"].dt.date  # Extract just the date
    df['artist'] = df['artist'].fillna('Unknown Artist').astype(str)
    df['song'] = df['song'].fillna('Unknown Song').astype(str)
    df = df[~df['artist'].str.contains('The WMW Radio Network')]
    df = df[~df['song'].str.contains('Promo')]
    return df


# --- Streamlit App ---
st.set_page_config(layout="wide", page_title="Radio Station Music Dashboard")
st.title("Radio Station Music Dashboard")


# Load data (replace with your actual file path or URL)
# Create sample data (as a string, like it would be in a CSV)
data = "https://storage.googleapis.com/wmradiopubbucket/data/wmradiodata.csv"
df = load_data(data)


# --- Sidebar Filters ---
st.sidebar.header("Filters")

# Date Range Filter
min_date = df["date"].min()
max_date = df["date"].max()
start_date, end_date = st.sidebar.date_input(
    "Date Range", (min_date, max_date), min_value=min_date, max_value=max_date
)

# Artist Filter
selected_artist = st.sidebar.selectbox(
    "Select Artist (Optional)", ["All"] + sorted(df["artist"].unique().tolist())
)

# Song Filter
if selected_artist != 'All':
    available_songs = sorted(df[df['artist']==selected_artist]['song'].unique().tolist())
else:
    available_songs = sorted(df['song'].unique().tolist())

selected_song = st.sidebar.selectbox(
    "Select Song (Optional)", ["All"] + available_songs
)


# --- Data Filtering ---
filtered_df = df[
    (df["date"] >= start_date) & (df["date"] <= end_date)
]  # date range

if selected_artist != "All":
    filtered_df = filtered_df[filtered_df["artist"] == selected_artist]

if selected_song != "All":
    filtered_df = filtered_df[filtered_df["song"] == selected_song]



# --- Main Page Content ---

# --- Top Played ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Top 5 Artists")
    top_artists = (
        filtered_df.groupby("artist")["pick_id"]
        .count()
        .nlargest(5)
        .reset_index(name="plays")
    )
    fig_top_artists = px.bar(
        top_artists, x="artist", y="plays", title="Top 5 Artists"
    )
    st.plotly_chart(fig_top_artists, use_container_width=True)

with col2:
    st.subheader("Top 5 Songs")
    top_songs = (
        filtered_df.groupby(["artist", "song", "artwork_large"])["pick_id"]
        .count()
        .nlargest(5)
        .reset_index(name="plays")
    )  # Include artwork
    fig_top_songs = px.bar(
        top_songs,
        x="song",
        y="plays",
        color="artist",  # Add color for artist
        title="Top 5 Songs",
        hover_data=["artist"],  # Show artist on hover
    )

    # Custom hover template to include image (requires a bit of a workaround in Streamlit)
    fig_top_songs.update_traces(
        hovertemplate="<b>%{x}</b><br>Artist: %{customdata[0]}<br>Plays: %{y}<br><extra></extra>"
    )  # Remove the "trace" part
    st.plotly_chart(fig_top_songs, use_container_width=True)

    # Display images (workaround, since Streamlit doesn't directly support HTML in tooltips)
    for _, row in top_songs.iterrows():
        st.image(row["artwork_large"], caption=f"{row['song']} by {row['artist']}", width=100)


# --- Plays Over Time ---

st.subheader("Plays Over Time")

plays_over_time = (
    filtered_df.groupby(["date", "artist", "song"])["pick_id"].count().reset_index(name="plays")
)

fig_plays_over_time = px.line(
    plays_over_time, x="date", y="plays", color="song", title="Plays Over Time" , hover_data=["artist"]) #added hover_data
st.plotly_chart(fig_plays_over_time, use_container_width=True)


# --- Song/Artist Timeline ---
# This is a bit more complex.  We'll do a scatter plot, with hover data.

st.subheader("Song/Artist Play Timeline")
if selected_artist != 'All' or selected_song != 'All':
    timeline_df = filtered_df.copy()
    timeline_df["time_of_day"] = timeline_df["timestamp"].dt.time  # For y-axis


    fig_timeline = px.scatter(
        timeline_df,
        x="date",
        y="time_of_day",
        color="song" if selected_artist != "All" else "artist",
        title=f"Play Timeline for {selected_artist if selected_artist != 'All' else selected_song}",
        hover_data=["artist", "song", "timestamp"],
    )
    fig_timeline.update_layout(yaxis_title="Time of Day")
    st.plotly_chart(fig_timeline, use_container_width=True)
else:
    st.write("Select an artist or song to see the play timeline.")



# --- Recently Played Table ---

st.subheader("Recently Played Songs")
recent_plays = filtered_df.sort_values("timestamp", ascending=False).head(10)
recent_plays = recent_plays[["timestamp", "artist", "song", "artwork_large"]]
recent_plays["timestamp"] = recent_plays["timestamp"].dt.strftime(
    "%Y-%m-%d %H:%M:%S"
)  # Format nicely

# Display as a table with images
st.write(recent_plays.to_html(escape=False, index=False, formatters={'artwork_large': lambda x: f'<img src="{x}" width="60">'}), unsafe_allow_html=True)


# --- Raw Data Table (Paginated) ---
with st.expander("Show Raw Data"):
        st.dataframe(filtered_df)