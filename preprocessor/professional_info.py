import re
from datetime import datetime

def extract_experience_from_resume(text: str):
    exp = {"total_years": 0, "titles": set(), "seniority": set()}
    current_year = datetime.now().year

    # 🔍 Match work experience durations
    duration_matches = re.findall(r'(\d{4})\s*(?:–|-|to)?\s*(present|\d{4})?', text.lower())
    total_experience = 0

    for start, end in duration_matches:
        try:
            start_year = int(start)
            end_year = current_year if not end or "present" in end.lower() else int(end)

            if 1900 <= start_year <= end_year <= current_year:
                total_experience += (end_year - start_year)
        except:
            continue

    exp["total_years"] = total_experience

    # 🔍 Match roles and seniority (simple titles)
    matches = re.findall(r"(senior|junior|lead|entry|principal)?\s*(developer|engineer|manager|analyst|scientist)", text.lower())
    for s, r in matches:
        full_title = f"{s.strip()} {r.strip()}" if s else r.strip()
        exp["titles"].add(full_title.strip())
        if s:
            exp["seniority"].add(s.strip())

    return exp

def extract_experience_criteria_from_jd(jd_text: str):
    criteria = {"min_years": 0, "expected_titles": set(), "seniority_keywords": set()}

    # Years required
    years_match = re.findall(r"(\d+)\+?\s+years? of experience", jd_text.lower())
    if years_match:
        criteria["min_years"] = max(map(int, years_match))

    # Seniority levels
    seniority_terms = ["entry", "junior", "mid", "senior", "lead", "principal"]
    for word in seniority_terms:
        if word in jd_text.lower():
            criteria["seniority_keywords"].add(word)

    # Job titles
    title_keywords = re.findall(r"(?:as|in|for|as a|for a|as an|in a)\s+([a-zA-Z ]+(developer|engineer|manager|analyst|scientist))", jd_text.lower())
    for role, _ in title_keywords:
        criteria["expected_titles"].add(role.strip())

    return criteria
