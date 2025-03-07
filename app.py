from flask import Flask, request, render_template, jsonify
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
import os
import re

app = Flask(__name__)

# Configure Gemini API securely
genai.configure(api_key="mention your api key")  # Set this in your environment

# Function to extract transcript from YouTube video
def get_youtube_transcript(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # Try fetching English transcript first
        if "en" in [t.language_code for t in transcript_list]:
            transcript = transcript_list.find_transcript(['en']).fetch()
        elif "hi" in [t.language_code for t in transcript_list]:  
            # Fetch Hindi transcript if English is unavailable
            transcript = transcript_list.find_transcript(['hi']).fetch()
        else:
            return None  # No suitable transcript found

        return " ".join([t['text'] for t in transcript])
    
    except TranscriptsDisabled:
        return None
    except Exception as e:
        return f"Error retrieving transcript: {str(e)}"

# Function to translate text if it's in Hindi
def translate_text(text):
    model = genai.GenerativeModel("gemini-1.5-pro")
    response = model.generate_content(f"Translate this Hindi text to English: {text}")
    return response.text if response else "Translation error."

# Function to analyze transcript using Gemini AI
def analyze_with_gemini(text):
    try:
        model = genai.GenerativeModel("gemini-1.5-pro")
        response = model.generate_content(f"Summarize and analyze this YouTube transcript: {text}")
        return response.text if response and response.text else "No response generated."
    except Exception as e:
        return f"Error analyzing transcript: {str(e)}"

# Extract YouTube Video ID using regex
def extract_video_id(url):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    return match.group(1) if match else None

# Home route
@app.route('/')
def home_page():
    return render_template('home.html')

# Main Analysis Page
@app.route('/index')
def index():
    return render_template('index.html')

# Analyze video and redirect to result page
@app.route('/analyze', methods=['POST'])
def analyze():
    youtube_url = request.form.get("youtube_url")
    video_id = extract_video_id(youtube_url)

    if video_id:
        transcript = get_youtube_transcript(video_id)

        if transcript:
            if "Error retrieving transcript" in transcript:
                return render_template('result.html', error=transcript)
            
            # If transcript is in Hindi, translate it
            if not transcript.isascii():  
                transcript = translate_text(transcript)

            summary = analyze_with_gemini(transcript)
            return render_template('result.html', transcript=transcript, summary=summary)
        else:
            return render_template('result.html', error="No transcript available. Try another video.")
    else:
        return render_template('result.html', error="Invalid YouTube URL. Please enter a valid link.")

if __name__ == '__main__':
    app.run(debug=True)
