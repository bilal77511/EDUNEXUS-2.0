import streamlit as st
from utils import load_css, run_watson_granite, show_error, show_success, show_info
from youtube_transcript_api import YouTubeTranscriptApi
import json
import requests
from urllib.parse import urlparse, parse_qs
import random

# Move these functions right after imports (around line 7)
def get_video_id(url):
    """Extract video ID from YouTube URL"""
    parsed_url = urlparse(url)
    if parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
        return parse_qs(parsed_url.query).get('v', [None])[0]
    elif parsed_url.hostname in ['youtu.be']:
        return parsed_url.path[1:]
    return None

def get_transcript(video_id):
    """Get transcript using proxy rotation"""
    try:
        # List of free proxy services
        proxies = [
            None,  # Try without proxy first
            {'http': 'http://proxy.scrapingbee.com:8080'},
            {'http': 'http://proxy.scrapeops.io:8080'},
            {'https': 'https://proxy.webshare.io:80'}
        ]
        
        for proxy in proxies:
            try:
                return YouTubeTranscriptApi.get_transcript(
                    video_id,
                    proxies=proxy,
                    cookies={'CONSENT': 'YES+1'}
                )
            except:
                continue
                
        # If all proxies fail, try with different language codes
        languages = ['en', 'en-US', 'en-GB', 'auto']
        for lang in languages:
            try:
                return YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
            except:
                continue
                
        return None
    except Exception as e:
        return None

# Page config
st.set_page_config(page_title="Lecture Summaries", page_icon="📹", layout="wide")

# Load CSS
st.markdown(load_css(), unsafe_allow_html=True)

# Title
st.markdown("<h1 class='main-title'>Lecture Summaries 📹</h1>", unsafe_allow_html=True)

# Initialize session state
if 'summaries' not in st.session_state:
    st.session_state.summaries = []

# Description
st.markdown(
    """<div class='card'>
        <h3>Summarize Video Lectures</h3>
        <p class='info-text'>Transform lengthy video lectures into concise, structured summaries.</p>
    </div>""",
    unsafe_allow_html=True
)

# Sidebar options
st.sidebar.markdown("<h2 class='sub-title'>Summary Options</h2>", unsafe_allow_html=True)

summary_type = st.sidebar.selectbox(
    "Summary Type",
    ["Concise", "Detailed", "Bullet Points", "Academic", "Simple Language"]
)

summary_length = st.sidebar.slider(
    "Summary Length (% of original)",
    min_value=10,
    max_value=50,
    value=30,
    step=5
)

# Main interface
youtube_url = st.text_input("📺 YouTube Video URL", placeholder="Paste the video URL here...")

# Process URL
if youtube_url:
    try:
        video_id = get_video_id(youtube_url)
        if not video_id:
            show_error("Invalid YouTube URL format")
            st.stop()
            
        transcript = get_transcript(video_id)
        if transcript:
            transcript_text = " ".join([item['text'] for item in transcript])
            show_success("Transcript fetched successfully!")
        else:
            show_error("Could not retrieve transcript. Please ensure the video has subtitles enabled.")
            transcript_text = None
            
    except Exception as e:
        show_error(f"Error fetching transcript: {str(e)}")
        transcript_text = None

# Buttons
col1, col2 = st.columns([1, 5])
with col1:
    if st.button("🧹 Clear History"):
        st.session_state.summaries = []
        show_success("History cleared!")
        st.rerun()

with col2:
    if st.button("📝 Generate Summary"):
        if youtube_url and transcript_text:
            try:
                system_prompt = f"""You are an expert in summarizing educational content.
                Create a {summary_type.lower()} summary that is approximately {summary_length}% of the original length.
                Focus on key educational points and maintain clarity.
                
                Format the summary with:
                1. Main Concepts
                2. Key Points
                3. Important Examples
                4. Key Terms & Definitions
                
                Make the summary clear and well-structured."""

                response = run_watson_granite(transcript_text, system_prompt)

                if not response.startswith("Error"):
                    st.session_state.summaries.append({
                        "url": youtube_url,
                        "summary": response,
                        "type": summary_type,
                        "length": summary_length
                    })
                    show_success("Summary generated successfully!")
                else:
                    show_error(f"Summarization failed: {response}")
            except Exception as e:
                show_error(f"An error occurred: {str(e)}")
        else:
            show_error("Please provide a valid YouTube URL with available transcript.")

# Display summaries
if st.session_state.summaries:
    st.markdown("<h2 class='sub-title'>Generated Summaries</h2>", unsafe_allow_html=True)
    
    for idx, summary in enumerate(reversed(st.session_state.summaries)):
        with st.expander(f"Summary {len(st.session_state.summaries) - idx} - {summary['type']}"):
            st.markdown(
                f"""<div class='card'>
                    <p><strong>Video URL:</strong> <a href="{summary['url']}" target="_blank">{summary['url']}</a></p>
                    <div class='response-area'>
                        <p><strong>Summary ({summary['length']}% length):</strong></p>
                        {summary['summary']}
                    </div>
                </div>""",
                unsafe_allow_html=True
            )

# Tips section
with st.expander("📚 Tips for Better Summaries"):
    st.markdown("""
    ### Tips for Better Results:
    1. **Choose Clear Videos**: Select videos with good audio quality for better transcription
    2. **Select Appropriate Summary Type**:
        - *Concise*: Quick overview of main points
        - *Detailed*: Comprehensive coverage of content
        - *Bullet Points*: Easy-to-scan format
        - *Academic*: Formal, structured summary
        - *Simple Language*: Easy-to-understand format
    3. **Adjust Length**: Use the slider to find the optimal summary length
    4. **Check Transcript**: Ensure the video has available subtitles/transcript
    """)

# Footer
st.markdown(
    """<div style='text-align: center; margin-top: 3rem; padding: 1rem; background-color: #262730; border-radius: 0.5rem;'>
        <p>Transform your learning experience with AI-powered lecture summaries!</p>
        <p class='info-text'>Happy learning! 📚</p>
    </div>""",
    unsafe_allow_html=True
)
