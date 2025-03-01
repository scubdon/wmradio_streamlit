import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
from io import BytesIO
from PIL import Image
import numpy as np
from urllib.parse import urlparse
import time

# Set page config
st.set_page_config(
    page_title="WMRadio Metrics",
    page_icon="🎵",
    layout="wide"
)

# Page title and description
st.title("WMRadio Metrics")
st.markdown("Interactive analytics for your radio station's play history")


# Function to load data
@st.cache_data
def load_data(file):
    try:
        df = pd.read_csv(file)
        df['artist'] = df['artist'].fillna('Unknown Artist').astype(str)
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        # Extract date components for filtering
        df['date'] = df['timestamp'].dt.date
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.day_name()
        df['month'] = df['timestamp'].dt.month_name()
        df['year'] = df['timestamp'].dt.year
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None


# Function to validate image URL
def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


# Function to display images from URLs with caching and error handling
@st.cache_data
def get_image(url):
    if not is_valid_url(url):
        return None

    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            return img
        return None
    except Exception:
        return None


# File upload option
uploaded_file = st.file_uploader("Upload CSV file with radio play data", type="csv")

# Demo option
use_demo_data = st.checkbox("Use sample data", value=not bool(uploaded_file))

if use_demo_data:
    # Create sample data from the provided examples
    sample_data = """pick_id,timestamp,artist,song,artwork_large
20303122605,2025-02-06T00:38:05.950755,The WMW Radio Network,Daily Rewind (w/Chris),https://s.rockbot.com/upload/live/users/500/3/2540173.jpg
20302989874,2025-02-06T01:01:01.504661,Moby,Bodyrock,https://s.rockbot.com/upload/live/albums/500/0/570.jpg
20303081356,2025-02-06T01:04:01.074752,Rihanna,Where Have You Been,https://s.rockbot.com/upload/live/albums/500/6/16026.jpg
20303109646,2025-02-06T01:08:01.416814,The Doobie Brothers,China Grove,https://s.rockbot.com/upload/live/albums/500/3/3243.jpg
20303637313,2025-02-06T01:11:00.939052,The 1975,It's Not Living (If It's Not With You),https://s.rockbot.com/upload/live/albums/500/9/1942699.jpg
20303664137,2025-02-06T01:15:01.334524,Afrojack,Take Over Control (feat. Eva Simons),https://s.rockbot.com/upload/live/albums/500/6/25236.jpg"""
    # Expand the sample with more data to make the demo more interesting
    # Generate plays for the last 30 days
    import io
    from random import choice, randint

    # Create a DataFrame from the sample data
    df_sample = pd.read_csv(io.StringIO(sample_data))

    # Use the unique artists and songs from the sample
    unique_artists = df_sample['artist'].unique()
    songs_by_artist = {artist: df_sample[df_sample['artist'] == artist]['song'].unique() for artist in unique_artists}
    artwork_by_artist = {artist: df_sample[df_sample['artist'] == artist]['artwork_large'].iloc[0] for artist in
                         unique_artists}

    # Generate 500 random plays over the last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    synthetic_data = []
    for i in range(500):
        random_timestamp = start_date + timedelta(
            days=randint(0, 30),
            hours=randint(0, 23),
            minutes=randint(0, 59),
            seconds=randint(0, 59)
        )

        random_artist = choice(list(unique_artists))
        random_song = choice(list(songs_by_artist[random_artist]))
        artwork = artwork_by_artist[random_artist]

        synthetic_data.append({
            'pick_id': 20303000000 + i,
            'timestamp': random_timestamp.isoformat(),
            'artist': random_artist,
            'song': random_song,
            'artwork_large': artwork
        })

    # Create DataFrame from synthetic data
    demo_df = pd.DataFrame(synthetic_data)
    df = load_data(io.StringIO(demo_df.to_csv(index=False)))
    st.info("Using synthetic demo data. Upload your own CSV file for real analysis.")

elif uploaded_file is not None:
    df = load_data(uploaded_file)
else:
    st.warning("Please upload a CSV file or use the sample data.")
    st.stop()

if df is not None and not df.empty:
    # Success message
    st.success(f"Successfully loaded data with {len(df)} song plays")

    # Fill empty artist names with string "Unknown Artist"
    df['artist'] = df['artist'].fillna('Unknown Artist').astype(str)
    df['song'] = df['song'].fillna('Unknown Song').astype(str)

    df = df[~df['artist'].str.contains('The WMW Radio Network')]
    df = df[~df['song'].str.contains('Promo')]

    # Display date range in the data
    min_date = df['timestamp'].min().date()
    max_date = df['timestamp'].max().date()
    st.info(f"Data spans from {min_date} to {max_date}")

    # Sidebar for global filters
    st.sidebar.title("Filters")

    # Date range filter
    date_range = st.sidebar.date_input(
        "Date Range",
        value=[min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )

    # Apply date filter
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    else:
        filtered_df = df

    # Artist filter (optional)
    all_artists = ['All Artists'] + sorted(filtered_df['artist'].unique().tolist())
    selected_artist = st.sidebar.selectbox("Filter by Artist", all_artists)

    if selected_artist != 'All Artists':
        filtered_df = filtered_df[filtered_df['artist'] == selected_artist]

    # Song filter (optional)
    all_songs = ['All Songs'] + sorted(filtered_df['song'].unique().tolist())
    selected_song = st.sidebar.selectbox("Filter by Song", all_songs)

    if selected_song != 'All Songs':
        filtered_df = filtered_df[filtered_df['song'] == selected_song]

    # Display filtered data size
    st.sidebar.info(f"Showing {len(filtered_df)} plays")

    # Download filtered data as CSV
    if st.sidebar.button("Download Filtered Data"):
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.sidebar.download_button(
            label="Download CSV",
            data=csv,
            file_name="filtered_radio_data.csv",
            mime="text/csv"
        )

    # Main dashboard - using tabs for organization
    tab1, tab2, tab3, tab4 = st.tabs(["Top Charts", "Trends Over Time", "Timeline", "Recent Plays"])

    with tab1:
        st.header("Top Songs and Artists")

        col1, col2 = st.columns(2)

        with col1:
            # Top songs visualization
            top_songs = filtered_df.groupby(['song', 'artist']).size().reset_index(name='plays')
            top_songs = top_songs.sort_values('plays', ascending=False).head(10)

            # Create a combined column for artist - song
            top_songs['title'] = top_songs['artist'] + ' - ' + top_songs['song']

            # Create horizontal bar chart
            fig_songs = px.bar(
                top_songs,
                x='plays',
                y='title',
                orientation='h',
                title='Top 10 Most Played Songs',
                color='plays',
                color_continuous_scale=px.colors.sequential.Viridis,
                labels={'plays': 'Number of Plays', 'title': 'Song'}
            )
            fig_songs.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_songs, use_container_width=True)

        with col2:
            # Top artists visualization
            top_artists = filtered_df.groupby('artist').size().reset_index(name='plays')
            top_artists = top_artists.sort_values('plays', ascending=False).head(10)

            fig_artists = px.bar(
                top_artists,
                x='plays',
                y='artist',
                orientation='h',
                title='Top 10 Most Played Artists',
                color='plays',
                color_continuous_scale=px.colors.sequential.Viridis,
                labels={'plays': 'Number of Plays', 'artist': 'Artist'}
            )
            fig_artists.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_artists, use_container_width=True)

        # Display top songs with artwork
        st.subheader("Top Songs with Artwork")

        # Create a grid for top songs with artwork
        top_n = min(5, len(top_songs))  # Ensure we don't exceed the available songs
        if top_n > 0:
            cols = st.columns(top_n)

            for i, (_, row) in enumerate(top_songs.head(top_n).iterrows()):
                with cols[i]:
                    # Get artwork image
                    artwork_url = filtered_df[(filtered_df['song'] == row['song']) &
                                              (filtered_df['artist'] == row['artist'])]['artwork_large'].iloc[0]
                    img = get_image(artwork_url)

                    if img is not None:
                        st.image(img, caption=f"{row['artist']} - {row['song']}")
                    else:
                        st.image("https://placehold.co/150x150?text=No+Image",
                                 caption=f"{row['artist']} - {row['song']}")

                    st.write(f"Plays: {row['plays']}")
        else:
            st.info("No songs to display")

    with tab2:
        st.header("Trends Over Time")

        # Time granularity selector
        time_granularity = st.radio(
            "Time Granularity",
            ["Daily", "Weekly", "Monthly"],
            horizontal=True
        )

        # Prepare data based on selected time granularity
        if time_granularity == "Daily":
            time_df = filtered_df.groupby(pd.Grouper(key='timestamp', freq='D')).size().reset_index(name='plays')
            time_df.columns = ['date', 'plays']
            x_axis = 'date'
            title = 'Daily Play Count'
        elif time_granularity == "Weekly":
            time_df = filtered_df.groupby(pd.Grouper(key='timestamp', freq='W')).size().reset_index(name='plays')
            time_df.columns = ['date', 'plays']
            title = 'Weekly Play Count'
            x_axis = 'date'
        else:  # Monthly
            time_df = filtered_df.groupby(pd.Grouper(key='timestamp', freq='M')).size().reset_index(name='plays')
            time_df.columns = ['date', 'plays']
            title = 'Monthly Play Count'
            x_axis = 'date'

        # Create time series chart
        fig_time = px.line(
            time_df,
            x=x_axis,
            y='plays',
            title=title,
            labels={'plays': 'Number of Plays', 'date': 'Date'},
            markers=True
        )
        st.plotly_chart(fig_time, use_container_width=True)

        # Artist or song trends over time
        st.subheader("Trends for Top Artists")

        # Get top 5 artists for trend analysis
        top_trend_artists = filtered_df.groupby('artist').size().reset_index(name='plays')
        top_trend_artists = top_trend_artists.sort_values('plays', ascending=False).head(5)['artist'].tolist()

        # Allow user to select multiple artists to compare
        selected_trend_artists = st.multiselect(
            "Select Artists to Compare",
            options=top_trend_artists,
            default=top_trend_artists[:min(3, len(top_trend_artists))]
        )

        if selected_trend_artists:
            # Filter data for selected artists
            artist_df = filtered_df[filtered_df['artist'].isin(selected_trend_artists)]

            # Group by artist and time period
            if time_granularity == "Daily":
                artist_time_df = artist_df.groupby(['artist', pd.Grouper(key='timestamp', freq='D')]). \
                    size().reset_index(name='plays')
            elif time_granularity == "Weekly":
                artist_time_df = artist_df.groupby(['artist', pd.Grouper(key='timestamp', freq='W')]). \
                    size().reset_index(name='plays')
            else:  # Monthly
                artist_time_df = artist_df.groupby(['artist', pd.Grouper(key='timestamp', freq='M')]). \
                    size().reset_index(name='plays')

            # Create line chart for artist trends
            fig_artist_trends = px.line(
                artist_time_df,
                x='timestamp',
                y='plays',
                color='artist',
                title=f'Trend for Selected Artists ({time_granularity})',
                labels={'plays': 'Number of Plays', 'timestamp': 'Date', 'artist': 'Artist'},
                markers=True
            )
            st.plotly_chart(fig_artist_trends, use_container_width=True)

        # Hour of day distribution
        st.subheader("Play Distribution by Hour of Day")
        hour_dist = filtered_df.groupby('hour').size().reset_index(name='count')

        fig_hour = px.bar(
            hour_dist,
            x='hour',
            y='count',
            labels={'count': 'Number of Plays', 'hour': 'Hour of Day (24h)'},
            title='Distribution of Plays by Hour'
        )
        st.plotly_chart(fig_hour, use_container_width=True)

        # Day of week distribution
        st.subheader("Play Distribution by Day of Week")

        # Order days correctly
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_dist = filtered_df.groupby('day_of_week').size().reset_index(name='count')
        day_dist['day_of_week'] = pd.Categorical(day_dist['day_of_week'], categories=day_order, ordered=True)
        day_dist = day_dist.sort_values('day_of_week')

        fig_day = px.bar(
            day_dist,
            x='day_of_week',
            y='count',
            labels={'count': 'Number of Plays', 'day_of_week': 'Day of Week'},
            title='Distribution of Plays by Day of Week'
        )
        st.plotly_chart(fig_day, use_container_width=True)

    with tab3:
        st.header("Timeline Visualization")

        # Allow filtering by song or artist
        filter_type = st.radio("Filter by", ["Artist", "Song"], horizontal=True)

        if filter_type == "Artist":
            # Get all artists
            all_timeline_artists = sorted(filtered_df['artist'].unique().tolist())
            if all_timeline_artists:
                selected_timeline_item = st.selectbox("Select Artist", all_timeline_artists)
                timeline_df = filtered_df[filtered_df['artist'] == selected_timeline_item]
                title = f"Play Timeline for Artist: {selected_timeline_item}"
            else:
                st.info("No artists available with the current filters")
                timeline_df = pd.DataFrame()
                title = "No data available"
        else:  # Song
            # Get all songs
            all_songs = sorted(filtered_df['song'].unique().tolist())
            if all_songs:
                selected_timeline_item = st.selectbox("Select Song", all_songs)
                timeline_df = filtered_df[filtered_df['song'] == selected_timeline_item]
                title = f"Play Timeline for Song: {selected_timeline_item}"
            else:
                st.info("No songs available with the current filters")
                timeline_df = pd.DataFrame()
                title = "No data available"

        # Display metrics
        total_plays = len(timeline_df)
        first_play = timeline_df['timestamp'].min() if not timeline_df.empty else None
        last_play = timeline_df['timestamp'].max() if not timeline_df.empty else None

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Plays", total_plays)
        with col2:
            st.metric("First Played", first_play.strftime('%Y-%m-%d %H:%M') if first_play else "N/A")
        with col3:
            st.metric("Last Played", last_play.strftime('%Y-%m-%d %H:%M') if last_play else "N/A")

        # Create a timeline visualization
        if not timeline_df.empty:
            # Create a scatter plot where each point represents a play
            fig_timeline = px.scatter(
                timeline_df,
                x='timestamp',
                y=[1] * len(timeline_df),  # All points on the same line
                title=title,
                labels={'timestamp': 'Date and Time', 'y': ''},
                height=300
            )

            # Update layout to make it look more like a timeline
            fig_timeline.update_traces(marker=dict(size=10, symbol='circle', color='royalblue'))
            fig_timeline.update_yaxes(showticklabels=False, showgrid=False)
            fig_timeline.update_layout(showlegend=False)

            st.plotly_chart(fig_timeline, use_container_width=True)

            # Display histogram of plays by hour of day
            st.subheader("Plays by Hour of Day")
            hour_counts = timeline_df.groupby(timeline_df['timestamp'].dt.hour).size().reset_index(name='count')
            hour_counts.columns = ['hour', 'count']

            fig_hours = px.bar(
                hour_counts,
                x='hour',
                y='count',
                title=f"Distribution of Plays by Hour of Day for {selected_timeline_item}",
                labels={'count': 'Number of Plays', 'hour': 'Hour of Day (24h)'}
            )
            st.plotly_chart(fig_hours, use_container_width=True)

            # Display a sample of plays with artwork
            st.subheader("Sample Plays")

            # Create columns for display
            sample_size = min(5, len(timeline_df))
            sample_df = timeline_df.sample(sample_size) if sample_size > 0 else timeline_df

            for _, row in sample_df.iterrows():
                col1, col2 = st.columns([1, 4])

                with col1:
                    img = get_image(row['artwork_large'])
                    if img is not None:
                        st.image(img, width=100)
                    else:
                        st.image("https://placehold.co/100x100?text=No+Image")

                with col2:
                    st.write(f"**{row['artist']} - {row['song']}**")
                    st.write(f"Played: {row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                    st.write(f"ID: {row['pick_id']}")
        else:
            st.info(f"No plays found for the selected {filter_type.lower()}")

    with tab4:
        st.header("Recent Plays")

        # Sort by most recent first
        recent_plays = filtered_df.sort_values('timestamp', ascending=False)

        # Pagination
        plays_per_page = st.slider("Plays per page", 5, 50, 10)
        total_pages = max(1, (len(recent_plays) + plays_per_page - 1) // plays_per_page)

        # Only show page selector if there's more than one page
        if total_pages > 1:
            page = st.number_input("Page", min_value=1, max_value=total_pages, value=1) - 1  # 0-indexed internally
        else:
            page = 0

        # Get plays for current page
        start_idx = page * plays_per_page
        end_idx = min(start_idx + plays_per_page, len(recent_plays))

        if len(recent_plays) > 0:
            current_plays = recent_plays.iloc[start_idx:end_idx]

            # Display info about pagination
            st.info(f"Showing plays {start_idx + 1} to {end_idx} of {len(recent_plays)}")

            # Display plays
            for _, row in current_plays.iterrows():
                col1, col2, col3 = st.columns([1, 3, 1])

                with col1:
                    img = get_image(row['artwork_large'])
                    if img is not None:
                        st.image(img, width=120)
                    else:
                        st.image("https://placehold.co/120x120?text=No+Image")

                with col2:
                    st.subheader(f"{row['artist']} - {row['song']}")
                    st.write(f"Played at: {row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")

                with col3:
                    st.write(f"**ID**: {row['pick_id']}")

                # Add a divider between entries
                st.divider()
        else:
            st.info("No plays to display with the current filters")

    # Add footer with info
    st.markdown("---")
    st.caption("Dashboard last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
else:
    st.error("No data to display. Please upload a valid CSV file.")
