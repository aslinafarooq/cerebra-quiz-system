import os
import sys
import ctypes
import random
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
if "quiz_database" not in st.session_state:
    subjects_data = {
        "Data Structures & Algorithms": [
            ("What is the worst-case time complexity of QuickSort?", ["O(n log n)", "O(n^2)", "O(n)", "O(log n)"], 1),
            ("Which data structure uses LIFO (Last In, First Out) ordering?", ["Stack", "Queue", "Array", "Linked List"], 0),
            ("What is the time complexity of searching in a balanced Binary Search Tree (BST)?", ["O(log n)", "O(n)", "O(n log n)", "O(1)"], 0),
            ("Which traversal algorithm uses a Queue data structure?", ["Breadth-First Search (BFS)", "Depth-First Search (DFS)", "In-order traversal", "Post-order traversal"], 0),
            ("What is the auxiliary space complexity of Merge Sort?", ["O(n)", "O(log n)", "O(1)", "O(n^2)"], 0),
            ("Which hashing collision resolution method uses linked lists at index buckets?", ["Separate Chaining", "Linear Probing", "Quadratic Probing", "Double Hashing"], 0),
            ("What is the time complexity of accessing an element by index in a dynamic array?", ["O(1)", "O(n)", "O(log n)", "O(n log n)"], 0),
            ("In a Min-Heap, where is the smallest element always located?", ["At the root", "At the rightmost leaf", "At a random position", "At the deepest level"], 0),
            ("Which graph algorithm finds the shortest path from a single source with non-negative edge weights?", ["Dijkstra's Algorithm", "Bellman-Ford Algorithm", "Kruskal's Algorithm", "Prim's Algorithm"], 0),
            ("What data structure is fundamentally used to implement function call stacks and recursion?", ["Stack", "Queue", "Heap", "Graph"], 0)
        ],
        "Computer Networks": [
            ("Which OSI layer is responsible for reliable end-to-end message delivery and flow control?", ["Transport Layer", "Network Layer", "Data Link Layer", "Application Layer"], 0),
            ("What protocol is used for secure encrypted communication over the web on Port 443?", ["HTTPS / TLS", "HTTP", "FTP", "Telnet"], 0),
            ("Which device operates primarily at Layer 3 (Network Layer) to forward packets across different subnets?", ["Router", "Hub", "Layer 2 Switch", "Repeater"], 0),
            ("What is the primary function of DNS (Domain Name System)?", ["Translating domain names to IP addresses", "Assigning MAC addresses", "Encrypting TCP packets", "Routing BGP traffic"], 0),
            ("Which 5G/6G architecture feature enables partitioning a physical network into multiple virtual networks?", ["Network Slicing", "Packet Filtering", "Carrier Aggregation", "Beamforming"], 0),
            ("What is the default port number for SSH (Secure Shell)?", ["Port 22", "Port 80", "Port 21", "Port 443"], 0),
            ("Which address uniquely identifies a network interface card (NIC) at the Data Link Layer?", ["MAC Address", "IP Address", "Port Number", "Session ID"], 0),
            ("What mechanism does TCP use to ensure reliable delivery and prevent network congestion?", ["Three-way handshake & sliding window", "Broadcast storms", "Random packet drop", "Stateless datagram transmission"], 0),
            ("Which routing protocol is an exterior gateway protocol used to route traffic between autonomous systems on the internet?", ["BGP (Border Gateway Protocol)", "OSPF", "RIP", "EIGRP"], 0),
            ("What is the purpose of a subnet mask in IPv4 addressing?", ["To divide an IP address into network and host portions", "To encrypt packet headers", "To assign dynamic IP leases", "To resolve MAC collisions"], 0)
        ],
        "Digital Health & AI": [
            ("What does RAG stand for in modern generative AI and LLM architectures?", ["Retrieval-Augmented Generation", "Random Access Gateway", "Recursive Algorithm Group", "Realtime Analytics Graph"], 0),
            ("Which database management system is standard for relational SQL data storage with Supabase?", ["PostgreSQL", "MongoDB", "Redis", "Cassandra"], 0),
            ("What is a primary ethical concern when deploying AI models in clinical healthcare settings?", ["Algorithmic bias and patient data privacy", "High font rendering speed", "CSS stylesheet compatibility", "Static code compilation times"], 0),
            ("Which neural network component underpins modern Large Language Models like GPT?", ["Transformer Self-Attention Mechanism", "Convolutional Filter Bank", "Recurrent Feedback Loop", "Markov Decision Matrix"], 0),
            ("What is the purpose of Electronic Health Record (EHR) interoperability standards like HL7/FHIR?", ["To enable secure exchange of health data across disparate systems", "To compile C++ shared libraries", "To compress medical imaging files", "To design Streamlit user interfaces"], 0),
            ("In medical AI diagnostics, what does 'explainability' (XAI) refer to?", ["The ability of the model to output understandable rationales for its predictions", "The speed at which inference runs on a GPU", "The total number of parameters in the model", "The cost of cloud hosting APIs"], 0),
            ("Which Python framework is widely used for rapid interactive data science and web app deployment?", ["Streamlit", "Django REST Framework", "Spring Boot", "Laravel"], 0),
            ("What is the role of data anonymization in health informatics?", ["Protecting patient identity by removing Personally Identifiable Information (PII)", "Accelerating database query execution", "Increasing model training loss", "Formatting PDF documents"], 0),
            ("Which machine learning paradigm trains models on decentralized medical data without sharing raw patient records?", ["Federated Learning", "Supervised Fine-Tuning", "Reinforcement Learning from Human Feedback", "Unsupervised Clustering"], 0),
            ("What type of machine learning model is commonly used to predict patient readmission risk based on tabular clinical records?", ["Gradient Boosting / Random Forest", "Generative Adversarial Network", "StyleTransfer CNN", "Word2Vec Embedding"], 0)
        ]
    }
    
    default_db = {}
    for sub, q_list in subjects_data.items():
        default_db[sub] = {}
        for q_num in range(1, 11):
            quiz_key = f"Quiz {q_num}"
            quiz_questions = []
            for j, (prompt, opts, c_idx) in enumerate(q_list, start=1):
                quiz_questions.append({
                    "id": q_num * 100 + j,
                    "prompt": f"{prompt}",
                    "options": opts,
                    "correct_idx": c_idx,
                    "points": 10.0
                })
            default_db[sub][quiz_key] = quiz_questions
            
    st.session_state.quiz_database = default_db

if "leaderboard" not in st.session_state:
    st.session_state.leaderboard = []

# -------------------------------------------------------------------
# 4. HEADER & SIDEBAR NAVIGATION
# -------------------------------------------------------------------
st.markdown("""
    <div class="app-header">
        <h1>🎓 Cerebra Assessment Platform</h1>
        <p>Powered by Randomized Shuffling Algorithms & Streamlit Cloud</p>
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

    available_quizzes = list(st.session_state.quiz_database[selected_subject].keys())
    selected_quiz_num = st.selectbox(
        "📋 Select Assessment Quiz", 
        options=available_quizzes
    )

    if not student_name or not roll_no:
        st.info("💡 Enter your Student Name and Roll Number above to start the quiz.")
    else:
        st.divider()
        
        session_key = f"shuffled_session_{selected_subject}_{selected_quiz_num}_{student_name}"
        
        if session_key not in st.session_state:
            raw_questions = st.session_state.quiz_database[selected_subject][selected_quiz_num]
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
                    "points": q["points"],
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
            st.markdown(f"### Current Exam: `{selected_subject} — {selected_quiz_num}` (Randomized Shuffle Active 🔀)")
            st.caption(f"Total Questions: {len(active_questions)}")
            st.write("")

            selected_options = {}
            for q in active_questions:
                q_data = shuffled_mapping[q["id"]]
                st.markdown(f"**Q{q['id']}: {q_data['prompt']}** `({q_data['points']} pts)`")
                
                selected = st.radio(
                    f"Select option for Q{q['id']}:", 
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
elif nav == "Instructor Dashboard":
    st.subheader("⚙️ Faculty Dashboard & Question Bank")
    st.caption("Manage question pools manually or parse lecture documents to automatically append questions.")

    tab1, tab2 = st.tabs(["✍️ Manual Question Entry", "📁 Bulk Import from PDF / DOCX"])

    with tab1:
        st.markdown("### Add Single Question")
        with st.form("add_question_form"):
            target_subject = st.selectbox("Select Target Subject", list(st.session_state.quiz_database.keys()), key="man_sub")
            target_quiz = st.selectbox("Select Target Quiz", list(st.session_state.quiz_database[target_subject].keys()), key="man_quiz")
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
                    new_id = len(st.session_state.quiz_database[target_subject][target_quiz]) + 8000

                    st.session_state.quiz_database[target_subject][target_quiz].append({
                        "id": new_id,
                        "prompt": new_prompt,
                        "options": [opt_a, opt_b, opt_c, opt_d],
                        "correct_idx": c_idx,
                        "points": pts
                    })
                    st.success(f"Success! Question added to `{target_subject} -> {target_quiz}`!")

    with tab2:
        st.markdown("### 📄 Document-to-Quiz Parser (PDF / DOCX)")
        st.caption("Upload lecture slides or notes to extract text and automatically add questions to your selected quiz bank.")
        
        parse_subject = st.selectbox("Target Subject for Import", list(st.session_state.quiz_database.keys()), key="parser_sub")
        parse_quiz = st.selectbox("Target Quiz for Import", list(st.session_state.quiz_database[parse_subject].keys()), key="parser_quiz")
        
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
            
            if st.button("🚀 Process Document & Add Extracted Questions"):
                valid_lines = [line.strip() for line in extracted_text.split('\n') if len(line.strip()) > 15]
                added_count = 0
                
                for idx, line in enumerate(valid_lines[:15]):
                    fake_options = [
                        f"Valid Concept: {line[:30]}...",
                        "Incorrect Alternate A",
                        "Incorrect Alternate B",
                        "None of the above"
                    ]
                    random.shuffle(fake_options)
                    correct_index = fake_options.index(f"Valid Concept: {line[:30]}...")

                    parsed_question = {
                        "id": 9000 + idx,
                        "prompt": f"Derived from notes: {line[:90]}?",
                        "options": fake_options,
                        "correct_idx": correct_index,
                        "points": 10.0
                    }
                    st.session_state.quiz_database[parse_subject][parse_quiz].append(parsed_question)
                    added_count += 1

                st.success(f"Successfully added {added_count} parsed questions into `{parse_subject} -> {parse_quiz}`!")
