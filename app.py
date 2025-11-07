import streamlit as st
import PyPDF2
import google.generativeai as genai

# Access the API key securely from Streamlit secrets
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
def gemini_analysis(resume_text):
    """
    Sends the resume text to the Gemini API for analysis and scoring.    """
    if not GEMINI_API_KEY:
        st.error("API key not found. Please add your GEMINI_API_KEY to Streamlit's secrets.")
    return None

    # Configure Gemini API
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')    # The prompt is the most important part! This tells the AI what to do.
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

    try:
        # Generate content using Gemini
        response = model.generate_content(prompt)
        
        import json
        # Parse the response text to extract JSON
        response_text = response.text.strip()
        # Remove markdown code blocks if present
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        analysis_data = json.loads(response_text.strip())
        return analysis_data
    except Exception as e:
        st.error(f"An error occurred while calling the Gemini API: {e}")
    return None

def extract_text_from_pdf(uploaded_file):
    """
    Extracts text from a PDF file.
    """
    try:
        reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page_num in range(len(reader.pages)):
            text += reader.pages[page_num].extract_text()
        return text
    except Exception as e:
        st.error(f"An error occurred while reading the PDF: {e}")
    return None

# Streamlit UI
st.set_page_config(page_title="ATS Resume Scanner", page_icon="📄")
st.title("ATS Resume Scanner 🤖📄")
st.markdown("Upload your resume (PDF) to get an ATS-friendly score and personalized feedback.")

uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    with st.spinner("Scanning your resume... This may take a moment."):
        # Extract text
        resume_text = extract_text_from_pdf(uploaded_file)

        if resume_text:
                # Get analysis from Gemini AI
            analysis = gemini_analysis(resume_text)

            if analysis:
                st.subheader("Your ATS Score")
                score = analysis['score']
                
                # Display score with a progress bar and emojis
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
                feedback = analysis['feedback']
                
                # Display feedback in an expandable format
                with st.expander("Overall Summary"):
                    st.write(feedback['overall_summary'])
                
                with st.expander("Action Verbs"):
                    st.write(feedback['action_verbs'])
                
                with st.expander("Quantifiable Achievements"):
                    st.write(feedback['quantifiable_achievements'])
                    
                with st.expander("Keywords"):
                    st.write(feedback['keywords'])
                    
                with st.expander("Formatting Tips"):
                    st.write(feedback['formatting_tips'])
