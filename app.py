import os
import sys
import ctypes
import random
import subprocess
import streamlit as st
from supabase import create_client, Client

# -------------------------------------------------------------------
# SUPABASE CLIENT INITIALIZATION
# -------------------------------------------------------------------
from supabase import create_client, Client

SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

if not SUPABASE_URL or SUPABASE_URL == "YOUR_SUPABASE_URL":
    st.error("⚠️ SUPABASE_URL is missing! Please configure it in your Streamlit Cloud Secrets settings.")
    st.stop()

@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# Helper function to fetch DSA questions dynamically from Supabase
SUBJECT_TABLES = {
    "Data Structures & Algorithms": "dsa_questions",
    "Computer Networks": "cn_questions"
}

def fetch_quiz_from_supabase(subject_name, quiz_name):
    table_name = SUBJECT_TABLES.get(subject_name)
    if not table_name:
        return []
    try:
        response = supabase.table(table_name) \
            .select("*") \
            .eq("quiz_name", quiz_name) \
            .execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching from Supabase: {e}")
        return []

# -------------------------------------------------------------------
# 1. PAGE SETUP & INDIGO / VIOLET BRANDING
# -------------------------------------------------------------------
st.set_page_config(
    page_title="Cerebra | Quiz Management System",
    page_icon="🎓",
    layout="wide"
)

st.markdown("""
    <style>
        /* Import a clean modern font from Google Fonts */
        @import url('[https://fonts.googleapis.com/css2?
        family=Inter:wght@400;500;600;700&display=swap]
        (https://fonts.googleapis.com/css2?
        family=Inter:wght@400;500;600;700&display=swap)');

        /* Apply the font globally to all app elements, text, buttons, and headers */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif !important;
        }

      /* Restored Teal, Blue, & Purple Gradient Background */
        .stApp {
            background: linear-gradient(135deg, #E6FFFA 0%, #E0F2FE 50%, #F5F3FF 100%) !important;
        }

        .app-header {
            background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 50%, #EC4899 100%);
            padding: 2.2rem;
            border-radius: 20px;
            color: white !important;
            box-shadow: 0 12px 30px -5px rgba(99, 102, 241, 0.4);
            margin-bottom: 2rem;
        }
        
        .app-header h1 {
            color: #FFFFFF !important;
            font-size: 2.6rem !important;
            font-weight: 800 !important;
            margin: 0 !important;
        }
        
        .app-header p {
            color: #F3E8FF !important;
            font-size: 1.1rem !important;
            margin-top: 0.5rem !important;
        }
        
        div[role="radiogroup"] {
            background: rgba(255, 255, 255, 0.85);
            backdrop-filter: blur(10px);
            padding: 16px;
            border-radius: 12px;
            border: 1px solid rgba(178, 245, 234, 0.6);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.03);
        }
        
        .stButton>button, .stFormSubmitButton>button {
            background: linear-gradient(90deg, #6366F1 0%, #8B5CF6 100%) !important;
            color: white !important;
            border: none !important;
            padding: 0.65rem 1.6rem !important;
            border-radius: 10px !important;
            font-weight: 700 !important;
            box-shadow: 0 4px 14px rgba(99, 102, 241, 0.3) !important;
        }
    </style>
""", unsafe_allow_html=True)
# -------------------------------------------------------------------
# 2. CROSS-PLATFORM C++ ENGINE LOADER WITH SMART PYTHON FALLBACK
# -------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
cpp_source = os.path.join(BASE_DIR, "quiz_system.cpp")
lib_path = os.path.join(BASE_DIR, "libquiz_engine.dll" if sys.platform == "win32" else "libquiz_engine.so")

if not os.path.exists(lib_path) and os.path.exists(cpp_source):
    try:
        if sys.platform == "win32":
            subprocess.run(["g++", "-shared", "-static", "-O3", cpp_source, "-o", lib_path], cwd=BASE_DIR, check=True)
        else:
            subprocess.run(["g++", "-shared", "-fPIC", "-O3", cpp_source, "-o", lib_path], cwd=BASE_DIR, check=True)
    except Exception:
        pass

class MockCppEngine:
    """Smart Python fallback engine that grades based on randomized option indices."""
    def process_attempt(self, q_ids, opts, count, score_out, total_out, shuffled_mapping):
        total = 0.0
        score = 0.0
        
        for i in range(count):
            qid = int(q_ids[i])
            user_choice_idx = int(opts[i])
            
            if qid in shuffled_mapping:
                q_data = shuffled_mapping[qid]
                pts = q_data["points"]
                total += pts
                if user_choice_idx == q_data["new_correct_idx"]:
                    score += pts

        score_out.value = float(score)
        total_out.value = float(total)

    def add_custom_question(self, q_id, prompt, o1, o2, o3, o4, c_idx, pts):
        pass

def load_cpp():
    if os.path.exists(lib_path):
        try:
            if sys.platform == "win32":
                os.add_dll_directory(BASE_DIR)
                return ctypes.CDLL(lib_path, winmode=0)
            return ctypes.CDLL(lib_path)
        except Exception:
            pass
    return MockCppEngine()

cpp_engine = load_cpp()

# -------------------------------------------------------------------
# 3. REALISTIC QUESTION BANK (Quiz 1-10 per Subject)
# -------------------------------------------------------------------
# -------------------------------------------------------------------
# QUIZ DATABASE INITIALIZATION
# -------------------------------------------------------------------
if "quiz_database" not in st.session_state:
    st.session_state.quiz_database = {
        "Data Structures & Algorithms": [f"Quiz {i}" for i in range(1, 11)],
        "Computer Networks": [f"Quiz {i}" for i in range(1, 11)],
    }

if "leaderboard" not in st.session_state:
    st.session_state.leaderboard = []

# -------------------------------------------------------------------
# 4. HEADER & SIDEBAR NAVIGATION
# -------------------------------------------------------------------
st.markdown("""
    <div class="app-header">
        <h1>🎓 Cerebra Assessment Platform</h1>
        <p>Showcasing Basic C++ Data Structures with Streamlit</p>
    </div>
""", unsafe_allow_html=True)

st.sidebar.markdown("## 🧭 Portal Navigation")
nav = st.sidebar.radio("Select View:", ["Student Portal", "Global Leaderboard", "Instructor Dashboard"])

st.sidebar.divider()
if st.sidebar.button("🔄 Reset Quiz Data & Reload"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# -------------------------------------------------------------------
# VIEW 1: STUDENT PORTAL (Shuffled Questions & Answer Options)
# -------------------------------------------------------------------
# -------------------------------------------------------------------
# VIEW 1: STUDENT PORTAL
# -------------------------------------------------------------------
if nav == "Student Portal":
    st.subheader("📝 Take an Assessment")

    c1, c2 = st.columns(2)
    with c1:
        student_name = st.text_input("Student Full Name", placeholder="e.g., Ayesha Shahbaz")
    with c2:
        roll_no = st.text_input("Roll / Registration Number", placeholder="e.g., CS-2026-88")

    selected_subject = st.selectbox(
        "📚 Select Subject", 
        options=list(st.session_state.quiz_database.keys())
    )

    available_quizzes = st.session_state.quiz_database[selected_subject]
    selected_quiz_num = st.selectbox(
        "📋 Select Assessment Quiz", 
        options=available_quizzes
    )

    if not student_name or not roll_no:
        st.info("💡 Enter your Student Name and Roll Number above to start the quiz.")
    else:
        st.divider()
        
        session_key = f"supabase_session_{selected_subject}_{selected_quiz_num}_{student_name}"
        
        # Fetch from Supabase and apply randomization shuffle if not already loaded for this session
        if session_key not in st.session_state:
           if selected_subject in SUBJECT_TABLES:
               raw_questions = fetch_quiz_from_supabase(selected_subject, selected_quiz_num)
           else:
                # Fallback for Object Oriented Programming or other local subjects
                raw_questions = []
            if not raw_questions:
                st.warning(f"⚠️ No questions found in Supabase for `{selected_quiz_num}` under Data Structures & Algorithms. Please populate your `dsa_questions` table in Supabase.")
                st.stop()
            else:
                shuffled_questions = list(raw_questions)
                random.shuffle(shuffled_questions)
                
                shuffled_mapping = {}
                for q in shuffled_questions:
                    paired_opts = [(opt, idx == q["correct_idx"]) for idx, opt in enumerate(q["options"])]
                    random.shuffle(paired_opts)
                    
                    new_opts = [item[0] for item in paired_opts]
                    new_correct_idx = next(i for i, item in enumerate(paired_opts) if item[1])
                    
                    shuffled_mapping[q["id"]] = {
                        "prompt": q["prompt"],
                        "points": float(q["points"]),
                        "shuffled_options": new_opts,
                        "new_correct_idx": new_correct_idx
                    }
                
                st.session_state[session_key] = {
                    "questions": shuffled_questions,
                    "mapping": shuffled_mapping
                }

        quiz_session = st.session_state[session_key]
        active_questions = quiz_session["questions"]
        shuffled_mapping = quiz_session["mapping"]

        with st.form("quiz_attempt_form", clear_on_submit=False):
            st.markdown(f"### Current Exam: `{selected_subject} — {selected_quiz_num}` (Supabase Live Backend 🌐)")
            st.caption(f"Total Questions: {len(active_questions)}")
            st.write("")

            selected_options = {}
            for idx_q, q in enumerate(active_questions, start=1):
                q_data = shuffled_mapping[q["id"]]
                st.markdown(f"**Q{idx_q}: {q_data['prompt']}** `({q_data['points']} pts)`")
                
                selected = st.radio(
                    f"Select option for question {idx_q}:", 
                    q_data["shuffled_options"], 
                    key=f"q_choice_{session_key}_{q['id']}"
                )
                selected_options[q['id']] = q_data["shuffled_options"].index(selected)
                st.write("---")

            submit = st.form_submit_button("Submit Assessment")

        if submit:
            q_ids_list = list(selected_options.keys())
            opts_list = list(selected_options.values())

            q_ids = (ctypes.c_int * len(q_ids_list))(*q_ids_list)
            opts = (ctypes.c_int * len(opts_list))(*opts_list)
            
            score_out = ctypes.c_double(0.0)
            total_out = ctypes.c_double(0.0)

            if hasattr(cpp_engine, "process_attempt"):
                if isinstance(cpp_engine, MockCppEngine):
                    cpp_engine.process_attempt(q_ids, opts, len(q_ids_list), score_out, total_out, shuffled_mapping)
                else:
                    cpp_engine.process_attempt(q_ids, opts, len(q_ids_list), ctypes.byref(score_out), ctypes.byref(total_out))

            score = score_out.value
            total = total_out.value
            percentage = (score / total) * 100 if total > 0 else 0

            st.session_state.leaderboard.append({
                "Student Name": student_name,
                "Roll No": roll_no,
                "Subject": f"{selected_subject} ({selected_quiz_num})",
                "Score": f"{score:.0f}/{total:.0f}",
                "Percentage": f"{percentage:.1f}%",
                "RawScore": score
            })

            st.markdown("---")
            st.markdown("### 📊 Official Assessment Results")
            r1, r2, r3 = st.columns(3)
            r1.metric("Final Score", f"{score:.0f} / {total:.0f}")
            r2.metric("Percentage", f"{percentage:.1f}%")
            if percentage >= 50:
                r3.success("Status: PASSED 🎓")
            else:
                r3.error("Status: NEEDS IMPROVEMENT ⚠️")

            st.progress(percentage / 100.0)

# -------------------------------------------------------------------
# VIEW 2: GLOBAL LEADERBOARD
# -------------------------------------------------------------------
elif nav == "Global Leaderboard":
    st.subheader("🏆 Assessment Hall of Fame")
    
    if not st.session_state.leaderboard:
        st.info("No quiz submissions recorded yet! Complete a quiz in the Student Portal to see your rank.")
    else:
        sorted_board = sorted(st.session_state.leaderboard, key=lambda x: x["RawScore"], reverse=True)
        top_student = sorted_board[0]
        st.success(f"🥇 **Current Top Rank:** **{top_student['Student Name']}** ({top_student['Subject']}) — Score: **{top_student['Percentage']}**")
        
        formatted_table = []
        for rank, item in enumerate(sorted_board, start=1):
            badge = "🥇 1st" if rank == 1 else ("🥈 2nd" if rank == 2 else ("🥉 3rd" if rank == 3 else f"#{rank}"))
            formatted_table.append({
                "Rank": badge,
                "Student Name": item["Student Name"],
                "Roll Number": item["Roll No"],
                "Subject / Quiz": item["Subject"],
                "Score": item["Score"],
                "Percentage": item["Percentage"]
            })

        st.table(formatted_table)

# -------------------------------------------------------------------
# VIEW 3: INSTRUCTOR DASHBOARD
# -------------------------------------------------------------------
# -------------------------------------------------------------------
# VIEW 3: INSTRUCTOR DASHBOARD
# -------------------------------------------------------------------
elif nav == "Instructor Dashboard":
    st.subheader("⚙️ Faculty Dashboard & Question Bank")
    st.caption("Manage question pools manually or parse lecture documents to automatically append questions.")

    tab1, tab2 = st.tabs(["✍️ Manual Question Entry", "📁 Bulk Import from PDF / DOCX"])

    with tab1:
        st.markdown("### Add Single Question")
        with st.form("add_question_form"):
            target_subject = st.selectbox("Select Target Subject", list(st.session_state.quiz_database.keys()), key="man_sub")
            target_quiz = st.selectbox("Select Target Quiz", st.session_state.quiz_database[target_subject], key="man_quiz")
            new_prompt = st.text_input("Enter Question Prompt")
            
            c1, c2 = st.columns(2)
            with c1:
                opt_a = st.text_input("Option A")
                opt_b = st.text_input("Option B")
            with c2:
                opt_c = st.text_input("Option C")
                opt_d = st.text_input("Option D")

            correct_choice = st.selectbox("Correct Choice", ["Option A (0)", "Option B (1)", "Option C (2)", "Option D (3)"])
            pts = st.number_input("Points Value", min_value=1.0, value=10.0)

            if st.form_submit_button("Add Question to Memory Pool"):
                if not new_prompt or not opt_a or not opt_b:
                    st.error("Please fill in the question prompt and options!")
                else:
                    st.success("Success! Question validated.")

    with tab2:
        st.markdown("### 📄 Smart Document-to-Quiz Parser (PDF / DOCX)")
        st.caption("Upload lecture sheets or MCQs (with a, b, c, d options and Answer keys) to automatically extract and push them to Supabase.")
        
        parse_subject = st.selectbox("Target Subject for Import", list(st.session_state.quiz_database.keys()), key="parser_sub")
        parse_quiz = st.selectbox("Target Quiz for Import", st.session_state.quiz_database[parse_subject], key="parser_quiz")
        
        doc_file = st.file_uploader("Upload Lecture File", type=["pdf", "docx"])
        
        if doc_file is not None:
            extracted_text = ""
            if doc_file.type == "application/pdf":
                try:
                    import pypdf
                    reader = pypdf.PdfReader(doc_file)
                    for page in reader.pages:
                        extracted_text += page.extract_text() or ""
                except Exception as e:
                    extracted_text = f"Error reading PDF: {e}"
            else:
                try:
                    import docx
                    doc = docx.Document(doc_file)
                    for para in doc.paragraphs:
                        extracted_text += para.text + "\n"
                except Exception as e:
                    extracted_text = f"Error reading DOCX: {e}"

            st.text_area("🔍 Extracted Document Preview", extracted_text[:2000], height=250)
            
            if st.button("🚀 Parse Real MCQs & Insert into Supabase"):
                import re
                
                # Split text into blocks or lines to parse structured MCQs
                lines = [line.strip() for line in extracted_text.split('\n') if line.strip()]
                
                parsed_questions = []
                current_q = None
                current_options = []
                correct_idx = 0
                
                for line in lines:
                    # Detect question start (e.g., "1. What is...", "12. Process of...")
                    q_match = re.match(r'^(\d+)[.)]\s+(.*)', line)
                    if q_match:
                        # Save previous question if exists
                        if current_q and len(current_options) >= 2:
                            parsed_questions.append({
                                "prompt": current_q,
                                "options": current_options[:4], # Keep up to 4 options
                                "correct_idx": min(correct_idx, len(current_options)-1)
                            })
                        current_q = q_match.group(2)
                        current_options = []
                        correct_idx = 0
                        continue
                    
                    # Detect options (e.g., "a) Push", "b) Pop", "A. Create")
                    opt_match = re.match(r'^([a-dA-D])[.)]\s+(.*)', line)
                    if opt_match and current_q:
                        opt_text = opt_match.group(2)
                        current_options.append(opt_text)
                        continue
                        
                    # Detect answer key (e.g., "Answer: b", "Ans: a")
                    ans_match = re.search(r'(?:Answer|Ans)[:\s]+([a-dA-D])', line, re.IGNORECASE)
                    if ans_match and current_q:
                        ans_char = ans_match.group(1).lower()
                        correct_idx = ord(ans_char) - ord('a') # 'a'->0, 'b'->1, etc.
                
                # Append the last question
                if current_q and len(current_options) >= 2:
                    parsed_questions.append({
                        "prompt": current_q,
                        "options": current_options[:4],
                        "correct_idx": min(correct_idx, len(current_options)-1)
                    })
                
                added_count = 0
                if not parsed_questions:
                    st.warning("⚠️ Could not automatically detect structured MCQ patterns (e.g., '1. Question ... a) ... b) ... Answer: b'). Try a cleaner text layout.")
                else:
                    for pq in parsed_questions:
                        # Ensure we have at least 4 options to keep quiz formatting consistent
                        while len(pq["options"]) < 4:
                            pq["options"].append(f"Alternate Option {len(pq['options']) + 1}")
                            
                        try:
                            supabase.table("dsa_questions").insert({
                                "quiz_name": parse_quiz,
                                "prompt": pq["prompt"],
                                "options": pq["options"],
                                "correct_idx": pq["correct_idx"],
                                "points": 1.0
                            }).execute()
                            added_count += 1
                        except Exception as e:
                            st.error(f"Supabase Insertion Error: {e}")

                    if added_count > 0:
                        st.success(f"Successfully parsed and inserted {added_count} real MCQs into Supabase for `{parse_quiz}`!")
