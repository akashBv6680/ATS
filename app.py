import streamlit as st
import PyPDF2
import google.generativeai as genai
import json

# Load Gemini API key from Streamlit secrets
# Note: st.secrets.get() is the correct modern way to access secrets.
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", None)

def gemini_analysis(resume_text):
    """
    Sends the resume text to the Gemini API for analysis and scoring.
    Returns a dictionary response on success, None on failure.
    """
    if not GEMINI_API_KEY:
        st.error("API key not found. Please add your GEMINI_API_KEY to Streamlit's secrets.")
        return None

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
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
        
        # --- CORRECTION APPLIED HERE ---
        # The AI often wraps JSON in a markdown block like ```json ... ```
        # We need to strip this. The issue was with multiline string checks.

        # Check for and strip common starting markdown fences
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        elif response_text.startswith('```'):
            response_text = response_text[3:]

        # Check for and strip the closing markdown fence
        if response_text.endswith('```'):
            response_text = response_text[:-3]

        # Parse JSON safely
        return json.loads(response_text.strip())
    except Exception as e:
        st.error(f"An error occurred while calling the Gemini API: {e}")
        st.error(f"Attempted to parse: {response_text.strip() if 'response_text' in locals() else 'No response received'}")
    return None

def extract_text_from_pdf(uploaded_file):
    """
    Extracts text from a PDF file.
    """
    try:
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

uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
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
        st.markdown(f"**Score: {score}/100**")
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
        
        with st.expander("Overall Summary"):
            st.write(feedback.get('overall_summary', 'No summary provided.'))
        with st.expander("Action Verbs"):
            st.write(feedback.get('action_verbs', 'No feedback provided.'))
        with st.expander("Quantifiable Achievements"):
            st.write(feedback.get('quantifiable_achievements', 'No feedback provided.'))
        with st.expander("Keywords"):
            st.write(feedback.get('keywords', 'No feedback provided.'))
        with st.expander("Formatting Tips"):
            st.write(feedback.get('formatting_tips', 'No feedback provided.'))
