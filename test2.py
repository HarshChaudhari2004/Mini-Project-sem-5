import streamlit as st
from dotenv import load_dotenv
import youtube_transcript_api
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
import os
import google.generativeai as genai

load_dotenv()  # Load all the environment variables

genai.configure(api_key = "AIzaSyC9ILUdqq2VGYKMaTOWBOUNi42Ei9egCa4")

prompt = """You are a YouTube video summarizer and note maker. You will be taking the transcript text 
and summarizing the entire video and providing the summary and notes. Please provide the summary 
and notes of the text given here: """

question_prompt = """You are an intelligent assistant. Answer the following question based on the video content: """

# Getting the transcript data from YouTube videos
def extract_transcript_details(youtube_video_url):
    try:
        video_id = youtube_video_url.split("v=")[1].split("&")[0]
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_transcript(['en', 'hi', 'mr'])
        transcript_text = " ".join([entry["text"] for entry in transcript.fetch()])
        return transcript_text
    except NoTranscriptFound as e:
        st.error(f"No transcript found: {e}")
        return None
    except Exception as e:
        st.error(f"Error retrieving transcript: {e}")
        return None

# Generate summary using Google Gemini API
def generate_gemini_content(transcript_text, prompt):
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt + transcript_text)
    return response.text

# Generate response to a question
def generate_question_response(transcript_text, question):
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(question_prompt + transcript_text + " Question: " + question)
    return response.text

# Clear chat history if video link changes
def clear_chat_history():
    if 'previous_youtube_link' in st.session_state:
        if st.session_state['previous_youtube_link'] != st.session_state['current_youtube_link']:
            st.session_state['questions'] = []
    st.session_state['previous_youtube_link'] = st.session_state['current_youtube_link']

st.title("YouTube Transcript to Detailed Notes Converter")
youtube_link = st.text_input("Enter YouTube Video Link:", key="current_youtube_link", on_change=clear_chat_history)

if youtube_link:
    video_id = youtube_link.split("v=")[1].split("&")[0]
    st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", use_column_width=True)

if 'summary' not in st.session_state:
    st.session_state['summary'] = None

if 'questions' not in st.session_state:
    st.session_state['questions'] = []

def get_notes():
    transcript_text = extract_transcript_details(st.session_state['current_youtube_link'])
    if transcript_text:
        summary = generate_gemini_content(transcript_text, prompt)
        st.session_state['summary'] = summary

if st.button("Get Detailed Notes") or st.session_state.get("notes_triggered", False):
    get_notes()
    st.session_state["notes_triggered"] = False

if st.session_state['summary']:
    st.markdown("## Detailed Notes:")
    st.write(st.session_state['summary'])

def ask_question():
    transcript_text = extract_transcript_details(st.session_state['current_youtube_link'])
    if transcript_text:
        question = st.session_state.get("current_question")
        answer = generate_question_response(transcript_text, question)
        st.session_state['questions'].append((question, answer))
        st.session_state["question_triggered"] = False

st.markdown("## Chat with Video")
question = st.text_input("Ask a question about the video:", key="current_question")

if st.button("Ask") or st.session_state.get("question_triggered", False):
    ask_question()

# Display previous questions and answers
if st.session_state['questions']:
    for q, a in st.session_state['questions']:
        st.markdown(f"**Q:** {q}")
        st.markdown(f"**A:** {a}")

# JavaScript to trigger button click on Enter key press
st.markdown("""
<script>
document.getElementById('current_youtube_link').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        document.querySelector('button[aria-label="Get Detailed Notes"]').click();
    }
});
document.getElementById('current_question').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        document.querySelector('button[aria-label="Ask"]').click();
    }
});
</script>
""", unsafe_allow_html=True)