import streamlit as st
import PyPDF2
import google.generativeai as genai
import json
import re

# Load Gemini API key from Streamlit secrets
# Note: st.secrets.get() is the correct modern way to access secrets.
# Ensure you have a file named .streamlit/secrets.toml with:
# GEMINI_API_KEY="YOUR_API_KEY_HERE"
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", None)

def gemini_analysis(resume_text):
    """
    Sends the resume text to the Gemini API for analysis and scoring.
    Returns a dictionary response on success, None on failure.
    """
    if not GEMINI_API_KEY:
        st.error("API key not found. Please add your GEMINI_API_KEY to Streamlit's secrets.")
        return None

    response_text = "No response received" # Initialize outside try block

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        
        # --- CRITICAL CORRECTION: Changed model for stability ---
        # The 'gemini-1.5-flash' error is fixed by using a stable model name.
        # 'gemini-1.0-pro' is a widely-supported model for complex generation tasks.
        model = genai.GenerativeModel('gemini-1.0-pro') 
        
        # Using a triple-quoted string for the prompt
        prompt = f"""
        You are an expert ATS (Applicant Tracking System) scanner. Your task is to analyze a resume and provide a score from 1 to 100 based on its ATS compatibility and overall quality.

        The analysis should be a JSON object with the following structure:
        {{
            "score": (integer),
            "feedback": {{
                "overall_summary": "A brief summary of the resume's strengths and weaknesses.",
                "action_verbs": "Feedback on the use of action verbs with examples of what to improve.",
                "quantifiable_achievements": "Feedback on measurable results with examples of what to improve.",
                "keywords": "Feedback on keyword usage and how to better align with a job description (if provided).",
                "formatting_tips": "Suggestions for formatting for better ATS parsing."
            }}
        }}

        Here is the resume text to analyze:

        <resume>
        {resume_text}
        </resume>

        Provide only the JSON object in your response, nothing else.
        """
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # --- ROBUST JSON PARSING CORRECTION ---
        # Use regex to find and extract the JSON object, ignoring markdown fences.
        json_match = re.search(r'(\{[\s\S]*\})', response_text)
        if json_match:
            json_string = json_match.group(1)
        else:
            # Fallback to simple stripping if regex fails (for very clean responses)
            json_string = response_text.replace('```json', '').replace('```', '').strip()

        # Parse JSON safely
        return json.loads(json_string)
        
    except Exception as e:
        st.error(f"An error occurred while calling the Gemini API: {e}")
        # The API key error (e.g., 400 or 401) is often masked here.
        # If you see a 401/403/404 error again, check the API key and model name.
        st.error(f"Attempted to parse: {response_text.strip()}")
    return None

def extract_text_from_pdf(uploaded_file):
    """
    Extracts text from a PDF file.
    """
    try:
        # Check if file is not None and has content
        uploaded_file.seek(0)
        reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted
        return text.strip()
    except Exception as e:
        st.error(f"An error occurred while reading the PDF: {e}")
    return None

# Streamlit UI setup
st.set_page_config(page_title="ATS Resume Scanner", page_icon="📄")
st.title("ATS Resume Scanner 🤖📄")
st.markdown("Upload your resume (PDF) to get an ATS-friendly score and personalized feedback.")

uploaded_file = st.file_uploader("Choose a PDF file (Limit 200MB per file)", type="pdf")

if uploaded_file is not None:
    # Check for file size
    if uploaded_file.size > 200 * 1024 * 1024:
        st.error("File size exceeds the 200MB limit.")
        st.stop()
        
    # Adding a check for PyPDF2 installation
    try:
        import PyPDF2
    except ImportError:
        st.error("PyPDF2 is not installed. Please install it using: pip install PyPDF2")
        st.stop()
        
    with st.spinner("Scanning your resume... This may take a moment."):
        resume_text = extract_text_from_pdf(uploaded_file)
        
        if not resume_text:
            st.error("Failed to extract text from PDF. Make sure the file isn't scanned/image-only and try again.")
            st.stop()
            
        analysis = gemini_analysis(resume_text)
        
        if not analysis:
            st.error("Failed to analyze the resume via Gemini API. Please check your API key and try again.")
            st.stop()
            
        st.subheader("Your ATS Score")
        score = analysis.get('score', 0)
        
        # Display score and progress
        col1, col2 = st.columns([1, 4])
        with col1:
            st.markdown(f"# **{score}**")
        with col2:
            st.markdown("out of 100")
            st.progress(score / 100)
            
        if score >= 80:
            st.success("Great job! Your resume is highly ATS-friendly. 🚀")
        elif score >= 50:
            st.warning("Good, but there's room for improvement. Follow the tips below. 💪")
        else:
            st.error("Your resume needs significant changes to pass an ATS. 🚨")
            
        st.markdown("---")
        st.subheader("Actionable Feedback")
        feedback = analysis.get('feedback', {})
        
        # Display feedback in expandable sections
        with st.expander("📝 Overall Summary"):
            st.write(feedback.get('overall_summary', 'No summary provided.'))
        with st.expander("💪 Action Verbs"):
            st.write(feedback.get('action_verbs', 'No feedback provided.'))
        with st.expander("📊 Quantifiable Achievements"):
            st.write(feedback.get('quantifiable_achievements', 'No feedback provided.'))
        with st.expander("🔑 Keywords"):
            st.write(feedback.get('keywords', 'No feedback provided.'))
        with st.expander("✨ Formatting Tips"):
            st.write(feedback.get('formatting_tips', 'No feedback provided.'))
