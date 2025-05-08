from dotenv import load_dotenv
import os
import json
import openai
import streamlit as st
import time

# ─── 1. Page config (wide layout) ───
st.set_page_config(
    page_title="HireMe BlueJay Coach (HBC) Mock Interview",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── 2. Background styling ───
bg_path = os.path.join(os.path.dirname(__file__), "AI background.png")
background_css = f'''
<style>
  .stApp {{
    background: url("file://{bg_path}") no-repeat center center fixed;
    background-size: cover;
  }}
  .css-1d391kg, .css-1d391kg * {{
    background-color: rgba(255,255,255,0.85) !important;
  }}
  footer {{visibility: hidden;}}
</style>
'''
st.markdown(background_css, unsafe_allow_html=True)

# ─── 3. Display JHU logo ───
logo_path = os.path.join(os.path.dirname(__file__), "JHU_Logo.jpg")
st.image(logo_path, width=200)

# ─── 4. Title & Introduction ───
st.markdown(
    '<h1 style="color:#005EB8; text-align:center; margin-bottom:0.2em;">'
    'HireMe BlueJay Coach (HBC) Mock Interview'
    '</h1>',
    unsafe_allow_html=True
)
st.markdown(
    """
    **Wouldn't it be invaluable to anticipate the exact questions recruiters will ask—and master your responses before you ever walk into the interview room?**  
    This mock interview experience empowers MS BAAI students at Carey Business School to:
    - Rehearse high-impact answers to role-specific questions  
    - Refine your delivery and non-verbal cues  
    - Gain a competitive edge in today’s hiring landscape  

    **Master the most common interview questions—the ones that make or break your first impression**
    """,
    unsafe_allow_html=True
)

# ─── 5. Timer (minutes:seconds since load) ───
if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()
elapsed = int(time.time() - st.session_state.start_time)
mins, secs = divmod(elapsed, 60)
st.markdown(f"**Time elapsed:** {mins:02d}:{secs:02d}")

# ─── 6. Load & validate OpenAI key ───
load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "").strip()
if not OPENAI_KEY:
    st.error(
        "❌ **OPENAI_API_KEY** not found. Please add it to a `.env` file next to `app.py`, e.g.:\n\n"
        "`OPENAI_API_KEY=sk-…`"
    )
    st.stop()
openai.api_key = OPENAI_KEY

# ─── 7. Load & sort the question bank ───
QUESTIONS_PATH = os.path.join(os.path.dirname(__file__), "questions", "questions.json")
try:
    with open(QUESTIONS_PATH, "r", encoding="utf-8") as f:
        question_bank = json.load(f)
except FileNotFoundError:
    st.error(f"❌ `questions.json` not found at `{QUESTIONS_PATH}`")
    st.stop()
question_bank = sorted(question_bank, key=lambda item: item["id"])

# ─── 8. Initialize answer tracking ───
if "answers" not in st.session_state:
    st.session_state.answers = []

# ─── 9. Build the Streamlit UI ───
st.subheader("Select a Question to Practice")
choice = st.number_input(
    "Choose question ID",
    min_value=1,
    max_value=len(question_bank),
    value=1,
    step=1
)
q = question_bank[choice - 1]

st.markdown(f"### Question {q['id']}")
st.write(q["prompt"])

student_answer = st.text_area(
    "Your Answer",
    placeholder="Type your answer here...",
    height=150,
    key="student_answer_input"
)

col1, col2 = st.columns(2)
with col1:
    if st.button("Show Hints", key="show_hints_btn"):
        st.write("**Verbal hint:**", q["verbal_hint"])
        st.write("**Non-verbal hint:**", q["nonverbal_hint"])
with col2:
    if st.button("Show Model Answer", key="show_model_answer_btn"):
        st.write(q["ideal_response"])

# ─── 10. Submit & Grade with ChatGPT ───
if st.button("Submit Answer", key="submit_answer_btn"):
    if not student_answer.strip():
        st.warning("Please type your answer before submitting.")
    else:
        eval_prompt = (
            f"You are an expert technical interviewer.\n"
            f"Question: {q['prompt']}\n"
            f"Ideal answer: {q['ideal_response']}\n"
            f"Student's answer: {student_answer}\n\n"
            "Please:\n"
            "1. Tell me if the student's answer is correct or incorrect.\n"
            "2. Provide a brief explanation (1–2 sentences)."
        )
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful, precise evaluator."},
                {"role": "user",   "content": eval_prompt}
            ],
            temperature=0
        )
        feedback = response.choices[0].message.content.strip()
        st.markdown("**Feedback:**")
        st.write(feedback)

        # ─── Save this result ───
        correct = feedback.lower().strip().startswith("correct")
        st.session_state.answers.append({
            "id": q["id"],
            "feedback": feedback,
            "correct": correct
        })

# ─── 11. Finish Test & Show Summary ───
if st.button("🏁 Finish Test", key="finish_test_btn"):
    num_questions = len(question_bank)
    num_correct   = sum(a["correct"] for a in st.session_state.answers)
    points_each   = 100 // num_questions
    score         = num_correct * points_each

    st.markdown("## 📝 Test Summary")
    st.write(f"**Score:** {score}/100")

    if score >= 90:
        st.success("🏅 Excellent (90–100)")
    elif score >= 70:
        st.info("👍 Good (70–89)")
    elif score >= 50:
        st.warning("⚠️ Fair (50–69)")
    else:
        st.error("❌ Needs Improvement (0–49)")

    st.markdown("### 🔍 Detailed Feedback")
    for rec in st.session_state.answers:
        st.write(f"**Q{rec['id']}**: {rec['feedback']}")

# ─── 12. Footer ───
footer_html = '''
<style>
  #custom-footer {
    position: fixed;
    bottom: 0;
    width: 100%;
    text-align: center;
    color: black;
    background-color: rgba(255,255,255,0.8);
    padding: 5px 0;
  }
</style>
<div id="custom-footer">
  Created by Sheila Morgan BU.330.760.42.SP25 Generative AI © 2025
</div>
'''
st.markdown(footer_html, unsafe_allow_html=True)

