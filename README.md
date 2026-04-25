# Opportunate

A modular, intelligent career toolkit built with Streamlit for resume analysis, role matching, skill-gap discovery, resume building, and ATS optimization.

## Why Opportunate
Opportunate helps job seekers move faster by keeping all critical workflows in one place:
- Discover jobs quickly
- Match resume to target roles
- Identify missing skills
- Build ATS-friendly resumes
- Improve ATS readiness with rule-based, ML, and AI insights

## Core Modules

### JobRadar
Purpose: Fast job search redirection with role and location inputs.

- Default location set to Pakistan
- Direct listing links for LinkedIn and Indeed
- Clean input flow for role, location, and experience filters

### JobMatcher
Purpose: Compare a resume against a job description.

- Resume upload (PDF/DOCX)
- JD upload or paste mode
- Hard-skill and soft-skill scoring
- Semantic match integration
- Missing skills and suggested learning resources

### CareerMatch
Purpose: Recommend likely job roles and related opportunities from resume content.

- Extracts personal/education/skills signals
- ML role prediction with confidence
- Top-N recommendation slider
- Displays matched skills and role context

### SkillBridge
Purpose: Identify and prioritize skill gaps for a target role.

- Resume parsing and skill extraction
- Role-skill comparison using dataset mappings
- AI-ranked skill-gap prioritization
- Resource recommendations for upskilling

### ResumeBuilder
Purpose: Generate a structured ATS-friendly resume.

- Dynamic form sections (education, experience, projects, certifications)
- Validation and ATS-oriented warnings
- Optional Gemini-powered content enhancement
- DOCX export

### ATS TuneUp
Purpose: Evaluate ATS compatibility using multiple strategies.

- Local rule-based ATS checks
- ML ATS score prediction
- Optional Gemini-enhanced ATS analysis
- Consolidated feedback and recommended external ATS tools

## Tech Stack
- Python
- Streamlit
- spaCy
- RapidFuzz
- scikit-learn
- sentence-transformers
- PyMuPDF
- python-docx
- Jinja2
- Google Gemini API (optional)

## Project Structure
```text
opportune-jobMate-main/
├── analyzer/
├── builder/
├── data/
│   ├── dataset/
│   ├── job_descriptions/
│   ├── models/
│   ├── resume_templates/
│   └── resumes/
├── datasets/
├── pages/
│   ├── JobRadar.py
│   ├── JobMatcher.py
│   ├── CareerMatch.py
│   ├── SkillBridge.py
│   ├── ResumeBuilder.py
│   └── ATS_TuneUp.py
├── preprocessor/
├── recommender/
├── scripts/
├── ui/
│   ├── assets/
│   ├── icons.py
│   ├── render_footer.py
│   ├── render_header.py
│   └── theme.py
├── Home.py
├── requirements.txt
└── README.md
```

## Setup

### 1. Clone and enter project
```bash
git clone https://github.com/<muhammadalisaleem>/opportunate.git
cd opportune-jobMate-main
```

### 2. Create virtual environment
Windows PowerShell:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:
```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the app
```bash
streamlit run Home.py
```

## Optional: Model Training
Pretrained artifacts are expected under `data/models/`. If you need to retrain models, use scripts in `scripts/`:
- `train_ats_score_model.py`
- `train_job_recommender.py`
- `train_resume_role_model.py`
- `train_skill_gap_ranker.py`

## Configuration Notes
- Gemini-based features are optional and require an API key entered inside relevant app modules.
- Supported resume formats across modules are primarily PDF and DOCX.
- If a model is unavailable, the app falls back to non-ML logic where possible.

## Data Attribution
Open datasets used in this project include:- 
IT Roles and Skills: https://www.kaggle.com/datasets/dhivyadharunaba/it-job-roles-skills-data

## Notes for Public Streamlit Deployment
- Set GEMINI_API_KEY in Streamlit app Secrets to enable AI features by default.
- App entrypoint is Home.py.
- Ensure all asset paths remain case-consistent (especially on Linux-based hosting).



## License
MIT License
