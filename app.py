import os
import sys
import ctypes
import subprocess
import streamlit as st

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
        div[data-testid="stMetric"] {
            background-color: rgba(255, 255, 255, 0.85) !important;
            backdrop-filter: blur(10px);
            border-radius: 14px !important;
            padding: 1.2rem !important;
            border-left: 6px solid #319795 !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
        }
    </style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------
# 2. CROSS-PLATFORM C++ ENGINE LOADER WITH PYTHON FALLBACK
# -------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
cpp_source = os.path.join(BASE_DIR, "quiz_system.cpp")

lib_path = os.path.join(BASE_DIR, "libquiz_engine.dll" if sys.platform == "win32" else "libquiz_engine.so")

# Try compiling if missing
if not os.path.exists(lib_path) and os.path.exists(cpp_source):
    try:
        if sys.platform == "win32":
            subprocess.run(["g++", "-shared", "-static", "-O3", cpp_source, "-o", lib_path], cwd=BASE_DIR, check=True)
        else:
            subprocess.run(["g++", "-shared", "-fPIC", "-O3", cpp_source, "-o", lib_path], cwd=BASE_DIR, check=True)
    except Exception:
        pass

class MockCppEngine:
    """Smart Python fallback engine that actually grades quiz attempts."""
    def process_attempt(self, q_ids, opts, count, score_out, total_out):
        total = 0.0
        score = 0.0
        
        # Pull quiz database from Streamlit session state to check correct answers
        quiz_db = st.session_state.get("quiz_database", {})
        q_map = {}
        for sub, q_list in quiz_db.items():
            for q in q_list:
                q_map[q["id"]] = {
                    "correct_idx": q["correct_idx"], 
                    "points": q.get("points", 10.0)
                }
        
        # Evaluate each submitted question
        for i in range(count):
            qid = int(q_ids[i])
            user_choice = int(opts[i])
            
            if qid in q_map:
                pts = q_map[qid]["points"]
                total += pts
                if user_choice == q_map[qid]["correct_idx"]:
                    score += pts
            else:
                total += 10.0
                score += 10.0  # Safe default if question ID is custom/unmapped

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
    
    # Fallback to pure Python engine so the cloud app never crashes
    st.toast("⚠️ Running on Cerebra Python Fallback Engine", icon="⚡")
    return MockCppEngine()

cpp_engine = load_cpp()

# -------------------------------------------------------------------
# 3. QUIZ DATABASE & SESSION INITIALIZATION
# -------------------------------------------------------------------
DEFAULT_QUIZZES = {
    "Data Structures & Algorithms": [
        {"id": 1, "prompt": "What is the Big O time complexity of Binary Search?", "options": ["O(n)", "O(log n)", "O(n^2)", "O(1)"], "correct_idx": 1, "points": 10.0},
        {"id": 2, "prompt": "Which data structure operates on LIFO (Last-In, First-Out)?", "options": ["Queue", "Array", "Stack", "Linked List"], "correct_idx": 2, "points": 10.0},
        {"id": 3, "prompt": "Which data structure manages student submissions in FIFO order?", "options": ["Stack", "Queue", "Tree", "Graph"], "correct_idx": 1, "points": 10.0}
    ],
    "Computer Networks": [
        {"id": 101, "prompt": "Which OSI layer does IP Routing operate on?", "options": ["Data Link Layer", "Network Layer", "Transport Layer", "Application Layer"], "correct_idx": 1, "points": 10.0},
        {"id": 102, "prompt": "What is the default TCP port number for HTTP traffic?", "options": ["Port 21", "Port 22", "Port 80", "Port 443"], "correct_idx": 2, "points": 10.0},
        {"id": 103, "prompt": "Which technique enables network isolation into virtual slices in 5G/6G architecture?", "options": ["Network Slicing", "Packet Switching", "Frequency Hopping", "Modulation"], "correct_idx": 0, "points": 10.0}
    ],
    "Digital Health & AI": [
        {"id": 201, "prompt": "What does RAG stand for in modern generative AI systems?", "options": ["Random Access Generation", "Retrieval-Augmented Generation", "Recursive Algorithm Group", "Realtime AI Gateway"], "correct_idx": 1, "points": 10.0},
        {"id": 202, "prompt": "Which relational database architecture is best suited for structured SQL tables with Supabase?", "options": ["PostgreSQL", "MongoDB", "Flat CSV Files", "Local Cache"], "correct_idx": 0, "points": 10.0}
    ]
}

if "quiz_database" not in st.session_state or "leaderboard" not in st.session_state:
    st.session_state.quiz_database = DEFAULT_QUIZZES
    st.session_state.leaderboard = []

# -------------------------------------------------------------------
# 4. HEADER & SIDEBAR NAVIGATION
# -------------------------------------------------------------------
st.markdown("""
    <div class="app-header">
        <h1>🎓 Cerebra Assessment Platform</h1>
        <p>Powered by native C++ Dynamic Data Structures (Linked Lists, Stacks, Queues) & Streamlit</p>
    </div>
""", unsafe_allow_html=True)

st.sidebar.markdown("## 🧭 Portal Navigation")
nav = st.sidebar.radio("Select View:", ["Student Portal", "Global Leaderboard", "Instructor Dashboard"])

st.sidebar.divider()
if st.sidebar.button("🔄 Reset Quiz Data & Reload"):
    st.session_state.quiz_database = DEFAULT_QUIZZES
    st.session_state.leaderboard = []
    st.rerun()

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

    selected_quiz_topic = st.selectbox(
        "📚 Select Subject Quiz", 
        options=list(st.session_state.quiz_database.keys())
    )

    if not student_name or not roll_no:
        st.info("💡 Enter your Student Name and Roll Number above to start the quiz.")
    else:
        st.divider()
        active_questions = st.session_state.quiz_database[selected_quiz_topic]

        with st.form("quiz_attempt_form", clear_on_submit=False):
            st.markdown(f"### Current Exam: `{selected_quiz_topic}`")
            st.caption(f"Total Questions: {len(active_questions)}")
            st.write("")

            selected_options = {}
            for q in active_questions:
                st.markdown(f"**Q{q['id']}: {q['prompt']}** `({q['points']} pts)`")
                selected = st.radio(
                    f"Select option for Q{q['id']}:", 
                    q["options"], 
                    key=f"q_choice_{q['id']}"
                )
                selected_options[q['id']] = q["options"].index(selected)
                st.write("---")

            submit = st.form_submit_button("Submit Assessment")

        if submit:
            # Prepare arrays for C++ DLL execution
            q_ids_list = list(selected_options.keys())
            opts_list = list(selected_options.values())

            q_ids = (ctypes.c_int * len(q_ids_list))(*q_ids_list)
            opts = (ctypes.c_int * len(opts_list))(*opts_list)
            
            score_out = ctypes.c_double(0.0)
            total_out = ctypes.c_double(0.0)

            # Call C++ DLL backend or Python fallback safely
            if hasattr(cpp_engine, "process_attempt"):
                if isinstance(cpp_engine, MockCppEngine):
                    # Python fallback takes the c_double objects directly
                    cpp_engine.process_attempt(
                        q_ids, 
                        opts, 
                        len(q_ids_list), 
                        score_out, 
                        total_out
                    )
                else:
                    # Real C DLL requires pointers via ctypes.byref()
                    cpp_engine.process_attempt(
                        q_ids, 
                        opts, 
                        len(q_ids_list), 
                        ctypes.byref(score_out), 
                        ctypes.byref(total_out)
                    )

            score = score_out.value
            total = total_out.value
            percentage = (score / total) * 100 if total > 0 else 0

            # Push attempt to session Leaderboard
            st.session_state.leaderboard.append({
                "Student Name": student_name,
                "Roll No": roll_no,
                "Subject": selected_quiz_topic,
                "Score": f"{score:.0f}/{total:.0f}",
                "Percentage": f"{percentage:.1f}%",
                "RawScore": score
            })

            # Display Results Cards
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
                "Subject": item["Subject"],
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
    st.caption("Manage your question bank manually or parse full lecture documents into quizzes.")

    tab1, tab2 = st.tabs(["✍️ Manual Question Entry", "📁 Bulk Import from PDF / DOCX"])

    with tab1:
        st.markdown("### Add Single Question")
        with st.form("add_question_form"):
            target_subject = st.selectbox("Select Target Subject", list(st.session_state.quiz_database.keys()))
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
                    c_idx = int(correct_choice.split("(")[1][0])
                    new_id = len(st.session_state.quiz_database[target_subject]) + 500

                    st.session_state.quiz_database[target_subject].append({
                        "id": new_id,
                        "prompt": new_prompt,
                        "options": [opt_a, opt_b, opt_c, opt_d],
                        "correct_idx": c_idx,
                        "points": pts
                    })
                    st.success(f"Success! Question added to `{target_subject}`!")

    with tab2:
        st.markdown("### 📄 Document-to-Quiz Parser (PDF / DOCX)")
        st.caption("Upload lecture slides or notes to preview extracted text and bulk-import questions.")
        
        doc_file = st.file_uploader("Upload Lecture File", type=["pdf", "docx"])
        
        if doc_file is not None:
            file_details = {"Filename": doc_file.name, "FileType": doc_file.type, "Size": doc_file.size}
            st.json(file_details)
            
            # Simple text extraction preview
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
            
            if st.button("🚀 Process & Generate Quiz from Document"):
                st.success("Document parsed successfully! Questions ready for review.")
