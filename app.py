# app.py  -- Single-file Streamlit app with SQLite + JWT + Readability
import streamlit as st
import sqlite3
import jwt
import datetime
from passlib.hash import pbkdf2_sha256
import textstat
import matplotlib.pyplot as plt
from PyPDF2 import PdfReader
import os  # NEW for environment variables

# -------------------------
# CONFIG - change for prod
# -------------------------
# Use env variable for SECRET_KEY (best practice), fallback to default in dev
SECRET_KEY = os.getenv("SECRET_KEY", "replace_this_with_a_strong_secret")
DB_FILE = "users.db"
TOKEN_EXPIRE_HOURS = 12  # token validity

# -------------------------
# DATABASE SETUP
# -------------------------
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()
c.execute(
    """
    CREATE TABLE IF NOT EXISTS users (
        email TEXT PRIMARY KEY,
        password_hash TEXT NOT NULL,
        name TEXT,
        age_group TEXT,
        language TEXT
    )
    """
)
conn.commit()

# -------------------------
# HELPERS: password & db
# -------------------------
def hash_password(pw: str) -> str:
    return pbkdf2_sha256.hash(pw)

def verify_password(pw: str, pw_hash: str) -> bool:
    return pbkdf2_sha256.verify(pw, pw_hash)

def add_user(email: str, password: str) -> bool:
    try:
        c.execute("INSERT INTO users (email, password_hash) VALUES (?, ?)", (email, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def user_exists(email: str) -> bool:
    c.execute("SELECT 1 FROM users WHERE email = ?", (email,))
    return c.fetchone() is not None

def validate_user(email: str, password: str) -> bool:
    c.execute("SELECT password_hash FROM users WHERE email = ?", (email,))
    row = c.fetchone()
    if not row:
        return False
    return verify_password(password, row[0])

def save_profile(email: str, name: str, age_group: str, language: str):
    c.execute(
        """
        UPDATE users SET name = ?, age_group = ?, language = ?
        WHERE email = ?
        """,
        (name, age_group, language, email),
    )
    conn.commit()

def get_profile(email: str):
    c.execute("SELECT name, age_group, language FROM users WHERE email = ?", (email,))
    row = c.fetchone()
    if row:
        return {"name": row[0] or "", "age_group": row[1] or "", "language": row[2] or ""}
    return {"name": "", "age_group": "", "language": ""}

# -------------------------
# HELPERS: JWT
# -------------------------
def generate_token(email: str) -> str:
    payload = {
        "email": email,
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=TOKEN_EXPIRE_HOURS),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

def verify_token(token: str):
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded
    except jwt.ExpiredSignatureError:
        st.error("⚠️ Session expired. Please log in again.")
    except jwt.InvalidTokenError:
        st.error("❌ Invalid token.")
    return None

# -------------------------
# HELPERS: file & readability
# -------------------------
def extract_text_from_upload(uploaded_file) -> str:
    if uploaded_file is None:
        return ""
    name = uploaded_file.name.lower()
    if name.endswith(".txt"):
        raw = uploaded_file.read()
        try:
            text = raw.decode("utf-8")
        except:
            text = raw.decode("latin-1", errors="ignore")
        return text
    elif name.endswith(".pdf"):
        try:
            pdf = PdfReader(uploaded_file)
            texts = []
            for p in pdf.pages:
                t = p.extract_text()
                if t:
                    texts.append(t)
            return "\n".join(texts)
        except Exception as e:
            st.error("Error reading PDF: " + str(e))
            return ""
    else:
        st.warning("Unsupported file type. Please upload .txt or .pdf for now.")
        return ""

def compute_readability(text: str):
    if not text or len(text.split()) < 30:
        return None
    flesch = textstat.flesch_reading_ease(text)
    gunning = textstat.gunning_fog(text)
    smog = textstat.smog_index(text)

    flesch_ease = max(0.0, min(100.0, float(flesch)))
    gunning_ease = max(0.0, min(100.0, 100.0 - float(gunning) * 5.0))
    smog_ease = max(0.0, min(100.0, 100.0 - float(smog) * 5.0))

    combined = (flesch_ease + gunning_ease + smog_ease) / 3.0

    if combined >= 70:
        label = "Beginner-friendly — easy to read"
    elif combined >= 50:
        label = "Intermediate — some prerequisite knowledge helpful"
    else:
        label = "Advanced — requires background knowledge"

    return {
        "flesch": flesch,
        "gunning": gunning,
        "smog": smog,
        "flesch_ease": flesch_ease,
        "gunning_ease": gunning_ease,
        "smog_ease": smog_ease,
        "combined_score": combined,
        "label": label,
    }

# -------------------------
# STREAMLIT UI
# -------------------------
st.set_page_config(page_title="Auth + Readability", layout="wide")
st.title("🔐 Authentication & Readability Analyzer")

if "token" not in st.session_state:
    st.session_state.token = None

left_col, right_col = st.columns([1, 1.2])

with left_col:
    st.markdown("### 🔑 User Authentication")
    auth_tab = st.radio("", ["Login", "Register"], horizontal=True, key="auth_mode")

    email_in = st.text_input("Email", key="email_input")
    password_in = st.text_input("Password", type="password", key="password_input")

    if auth_tab == "Login":
        if st.button("Sign In"):
            if not email_in or not password_in:
                st.error("Please enter email and password.")
            else:
                if validate_user(email_in, password_in):
                    token = generate_token(email_in)
                    st.session_state.token = token
                    st.success("✅ Logged in successfully.")
                    st.rerun()
                else:
                    if user_exists(email_in):
                        st.error("❌ Incorrect password.")
                    else:
                        st.error("⚠️ Account doesn't exist. Please register.")
    else:
        if st.button("Create Account"):
            if not email_in or not password_in:
                st.error("Please enter email and password for registration.")
            else:
                if user_exists(email_in):
                    st.warning("⚠️ Account already exists. Please sign in.")
                else:
                    ok = add_user(email_in, password_in)
                    if ok:
                        st.success("✅ Account created. Now sign in.")
                    else:
                        st.error("❌ Could not create account. Try again.")

    st.markdown("---")
    st.markdown("### 👤 Profile Management")
    if st.session_state.token:
        payload = verify_token(st.session_state.token)
        if not payload:
            st.session_state.token = None
            st.experimental_rerun()
        user_email = payload.get("email")
        st.write(f"**Signed in as:** {user_email}")

        profile = get_profile(user_email)
        name_val = st.text_input("Full Name", value=profile["name"], key="profile_name")
        age_choices = ["", "<18", "18-25", "26-35", "36-50", "50+"]
        age_index = age_choices.index(profile["age_group"]) if profile["age_group"] in age_choices else 0
        age_val = st.selectbox("Age Group", age_choices, index=age_index, key="profile_age")
        lang_choices = ["English", "Tamil", "Hindi"]
        lang_index = lang_choices.index(profile["language"]) if profile["language"] in lang_choices else 0
        lang_val = st.selectbox("Language Preference", lang_choices, index=lang_index, key="profile_lang")

        if st.button("Save Profile"):
            save_profile(user_email, name_val, age_val, lang_val)
            st.success("✅ Profile saved.")

        if st.button("Logout"):
            st.session_state.token = None
            st.experimental_rerun()
    else:
        st.info("Please sign in to manage your profile.")

with right_col:
    st.markdown("### 📄 Upload Document & Readability")
    if not st.session_state.token:
        st.info("Sign in to upload documents and analyze readability.")
    else:
        uploaded_file = st.file_uploader("Upload a .txt or .pdf file", type=["txt", "pdf"])
        if uploaded_file:
            # -------------------------
            # NEW: Show File Details
            # -------------------------
            st.markdown("### 📂 File Details")
            st.write(f"- **File name:** {uploaded_file.name}")
            st.write(f"- **File type:** {uploaded_file.type}")
            st.write(f"- **File size:** {uploaded_file.size/1024:.2f} KB")

            with st.spinner("Extracting text and computing readability..."):
                text = extract_text_from_upload(uploaded_file)
                if not text or len(text.split()) < 30:
                    st.error("File is empty or too short for reliable readability metrics (need ~30+ words).")
                else:
                    res = compute_readability(text)
                    if res is None:
                        st.error("Unable to compute readability reliably.")
                    else:
                        st.success(f"Overall: **{res['combined_score']:.1f}** — {res['label']}")
                        st.markdown("**Raw metrics:**")
                        st.write(f"- Flesch Reading Ease: {res['flesch']:.2f}")
                        st.write(f"- Gunning Fog Index: {res['gunning']:.2f}")
                        st.write(f"- SMOG Index: {res['smog']:.2f}")

                        labels = ["Flesch (ease)", "Gunning (ease)", "SMOG (ease)"]
                        vals = [res["flesch_ease"], res["gunning_ease"], res["smog_ease"]]
                        fig, ax = plt.subplots(figsize=(6, 3))
                        bars = ax.bar(labels, vals)
                        ax.set_ylim(0, 100)
                        ax.set_ylabel("Ease (0=hard, 100=very easy)")
                        ax.set_title("Readability (normalized)")
                        for b in bars:
                            h = b.get_height()
                            ax.annotate(f"{h:.1f}", xy=(b.get_x() + b.get_width() / 2, h),
                                        xytext=(0, 4), textcoords="offset points",
                                        ha="center", va="bottom")
                        st.pyplot(fig)

                        st.markdown("### Suggestions to improve readability")
                        st.write("- Use shorter sentences and break long paragraphs.")
                        st.write("- Replace rare/complex words with simpler alternatives.")
                        st.write("- Add examples and use active voice where possible.")
                        st.write("- Use headings, bullet lists, and whitespace to structure content.")