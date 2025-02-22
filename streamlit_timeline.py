import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

def load_and_prepare_data():
    # Read the CSV file
    df = pd.read_csv('wmradiodata.csv')

    # Handle null values in artist column and convert to string
    df['artist'] = df['artist'].fillna('Unknown Artist').astype(str)

    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    return df

def create_app():
    st.title("WM Radio Play History Visualization")
    
    # Load the data
    df = load_and_prepare_data()
    
    # Create sidebar for filtering
    st.sidebar.header("Filter Options")
    
    # Create filter options
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
        fig = px.scatter(
            filtered_df,
            x='timestamp',
            y='artist' if filter_type == "Artist" else 'song',
            color='artist' if filter_type == "Artist" else 'song',
            hover_data=['song', 'artist', 'timestamp'],
            title=f"Play History Timeline for Selected {filter_type}s",
            height=400
        )
        
        # Customize the layout
        fig.update_layout(
            xaxis_title="Date and Time",
            yaxis_title=filter_type,
            showlegend=True,
            hovermode='closest'
        )
        
        # Display the plot
        st.plotly_chart(fig, use_container_width=True)
        
        # Display the data table
        st.subheader("Play History Details")
        st.dataframe(
            filtered_df[['timestamp', 'artist', 'song']]
            .sort_values('timestamp', ascending=False)
        )
    else:
        st.warning("No data available for the selected filters.")

if __name__ == "__main__":
    create_app()
