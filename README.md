# Milestone-1
# 🔐 Authentication & Readability Analyzer  

A Streamlit web app that combines **user authentication** and **document readability analysis**.  

It allows users to:  
- Register/Login securely with **SQLite + JWT**  
- Manage personal profile (name, age group, language preference)  
- Upload `.txt` or `.pdf` files  
- Analyze readability using **Flesch Reading Ease**, **Gunning Fog**, and **SMOG** indexes  
- View results as charts and get suggestions to improve readability  

---

## 🚀 Features  
- ✅ Secure password hashing (`pbkdf2_sha256`)  
- ✅ JWT token-based session handling  
- ✅ Profile management (name, age, language)  
- ✅ File upload: `.txt` and `.pdf` supported  
- ✅ Readability metrics with **Textstat**  
- ✅ Visualizations with **Matplotlib**  
- ✅ Readability improvement suggestions  

---

## 📦 Installation  

### 1. Clone the repo  
```bash
git clone https://github.com/your-username/readability-analyzer.git
cd readability-analyzer
2. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
3. Install dependencies
pip install -r requirements.txt
4. Run the app
streamlit run app.py
⚙️ Configuration

This app requires a JWT secret key for token generation.
Set it as an environment variable before running:

Linux/macOS:
export SECRET_KEY="your_strong_secret_here"
Windows (PowerShell):
setx SECRET_KEY "your_strong_secret_here"
📊 Example Output

Upload a file

Readability metrics are displayed (Flesch, Gunning Fog, SMOG)

A bar chart shows readability ease (0 = hard, 100 = easy)

Suggestions appear to improve clarity and simplicity

🛠️ Tech Stack

* Streamlit
* SQLite
* Passlib
* PyJWT
* Textstat
* Matplotlib
* PyPDF2
