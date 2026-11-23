
import streamlit as st
import requests
import PyPDF2
import json
import re

st.set_page_config(
    page_title="Resume Analyzer",
    page_icon="📄",
    layout="centered"
)

st.title("📄 AI Resume Analyzer")
st.caption("Analyze your resume using AI")

# API Key
try:
    key =st.secrets["OPENROUTER_API_KEY"]
    
except Exception:
    st.error("API key not found. Please configure Streamlit secrets.")
    st.stop()

# Upload Resume
file = st.file_uploader(
    "Upload Your Resume",
    type=["pdf"]
)

# Enter Job Role
role = st.text_area(
    "Enter Your Role",
    placeholder="Example: Python Developer"
)

if st.button("Analyze Resume", type="primary"):

    if not file or not role.strip():
        st.warning("Please upload your resume and enter your job role.")

    else:
        try:
            # Read PDF
            file.seek(0)
            reader = PyPDF2.PdfReader(file, strict=False)

            resume = ""

            for page in reader.pages:
                resume += page.extract_text() or ""

            if not resume.strip():
                st.error("No text found in PDF. Please upload a text-based PDF.")
                st.stop()

            # OpenRouter API
            with st.spinner("Analyzing your resume..."):

                url = "https://openrouter.ai/api/v1/chat/completions"

                headers = {
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json"
                }

                body = {
                    "model": "openai/gpt-4o-mini",
                    "messages": [
                        {
                            "role": "user",
                            "content": f"""
Analyze the following resume for the job role: {role}

Resume:
{resume}

Return ONLY valid JSON.
Do not use markdown or code fences.

Use this exact JSON structure:

{{
    "score": 85,
    "mistakes": ["Missing projects", "No certifications"],
    "suggestions": ["Add more projects", "Improve skills section"],
    "summary": "Resume summary here",
    "strengths": ["Good Python skills", "Problem solving"]
}}

Give a score between 0 and 100.
Make suggestions relevant to the job role.
All list values must be strings.
"""
                        }
                    ],
                    "temperature": 0.3
                }

                response = requests.post(
                    url,
                    headers=headers,
                    json=body,
                    timeout=60
                )

                # Check API response
                response.raise_for_status()

                result_data = response.json()

                if "choices" not in result_data:
                    raise Exception(
                        result_data.get("error", "Invalid API response")
                    )

                result = result_data["choices"][0]["message"]["content"]

                if not result:
                    raise Exception("AI returned an empty response.")

                # Remove Markdown code fences if present
                result = re.sub(
                    r"^```(?:json)?\s*|\s*```$",
                    "",
                    result.strip(),
                    flags=re.IGNORECASE
                )

                # Convert JSON string into Python dictionary
                data = json.loads(result)

            # Display Results
            st.success("Resume Analyzed Successfully!")

            st.subheader("📊 Resume Score")

            score = int(data["score"])
            st.metric("Your Score", f"{score}/100")
            st.progress(max(0, min(score, 100)) / 100)

            st.subheader("📝 Summary")
            st.write(data["summary"])

            st.subheader("❌ Mistakes")
            for mistake in data["mistakes"]:
                st.write("•", mistake)

            st.subheader("💡 Suggestions")
            for suggestion in data["suggestions"]:
                st.write("•", suggestion)

            st.subheader("💪 Strengths")
            for strength in data["strengths"]:
                st.write("•", strength)

            # Download JSON Report
            st.download_button(
                label="Download Report",
                data=json.dumps(data, indent=4),
                file_name="resume_analysis.json",
                mime="application/json"
            )

        except PyPDF2.errors.PdfReadError:
            st.error("PDF is corrupted or invalid. Please upload another PDF.")

        except json.JSONDecodeError:
            st.error("AI returned invalid JSON. Please try again.")

        except requests.exceptions.Timeout:
            st.error("API request timed out. Please try again.")

        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {e}")

        except Exception as e:
            st.error(f"Something went wrong: {e}")
