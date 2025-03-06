import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.title("Wal-Mart Radio Plays")

df = pd.read_csv('https://storage.googleapis.com/wmradiopubbucket/data/wmradiodata.csv')

df['timestamp'] = pd.to_datetime(df['timestamp'])

# Handle null values in artist column and convert to string
df['artist'] = df['artist'].fillna('Unknown Artist').astype(str)

# Create sidebar for filtering
st.sidebar.header("Filter Options")

filter_type = st.sidebar.radio("Filter by:", ["Artist", "Song"])

if filter_type == "Artist":
    selected_artists = st.sidebar.multiselect(
        "Select Artists:",
        options=sorted(df['artist'].unique()),
        default=[df['artist'].iloc[0]]
    )
    filtered_df = df[df['artist'].isin(selected_artists)]
else:
    selected_songs = st.sidebar.multiselect(
        "Select Songs:",
        options=sorted(df['song'].unique()),
        default=[df['song'].iloc[0]]
    )
    filtered_df = df[df['song'].isin(selected_songs)]

# Create timeline visualization
if not filtered_df.empty:
    # Extract date and hour components from timestamp
    filtered_df['date'] = filtered_df['timestamp'].dt.date
    filtered_df['hour'] = filtered_df['timestamp'].dt.hour

    fig = px.scatter(
        filtered_df,
        x='date',  # Use 'date' for the x-axis
        y='hour',  # Use 'hour' for the y-axis
        color='artist' if filter_type == "Artist" else 'song',
        hover_data=['song', 'artist', 'timestamp'],
        title=f"Play History Timeline for Selected {filter_type}s",
        height=400
    )

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Hour of Day",
        showlegend=True,
        hovermode='closest'
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Play History Details")
    st.dataframe(
        filtered_df[['timestamp', 'artist', 'song']]
        .sort_values('timestamp', ascending=False)
    )
else:
    st.warning("No data available for the selected filters.")