import re
import json
from rapidfuzz import fuzz, process  # type: ignore

# Email extractor
def extract_mail(text: str):
    match = re.search(r"[\w\.-]+@[\w\.-]+", text)
    return match.group(0) if match else None

# Phone number extractor (10-digit)
def extract_phone(text: str):
    pattern = re.compile(
        r'''(?x)
        (?:(?:\+?\d{1,4}[\s\-\.])?)
        (?:\(?\d{3}\)?[\s\-\.]?)
        \d{3}[\s\-\.]?\d{4}
        |
        (?<!\d)(\d{5}[\s\-]?\d{5})(?!\d)
        ''')
    
    match = pattern.search(text)
    return match.group(0) if match else None


# Name extractor (needs spaCy Doc object, not raw string)
def extract_name(doc, text):
    # 1. Try NER with blacklist filter
    blacklist = {
        "java", "python", "sql", "flask", "django", "matplotlib", "jenkins", "github"
    }

    for ent in doc.ents:
        if ent.label_ == "PERSON":
            name = ent.text.strip()
            if name.lower() not in blacklist and len(name.split()) <= 3:
                return name

    # 2. Fallback: Regex on "Name:" or header
    name_match = re.search(r"(?:^|\n)name[:\-–\s]*([A-Z][a-z]+(?:\s[A-Z][a-z]+)+)", text, re.IGNORECASE)
    if name_match:
        return name_match.group(1).strip()

    return "Not found"

def extract_education_details(
    text,
    degree_json_path="data/dataset/degrees.json",
    university_json_path="data/dataset/universities.json",
    threshold=85
):
    # Load degrees.json
    with open(degree_json_path, "r", encoding="utf-8") as f:
        degree_map = json.load(f)

    alias_to_canonical = {}
    for canonical, aliases in degree_map.items():
        for alias in aliases:
            alias_to_canonical[alias.lower().replace(".", "").strip()] = canonical

    # Load universities.json (list of {name: [aliases]})
    with open(university_json_path, "r", encoding="utf-8") as f:
        university_data = json.load(f)

    result = {
        "degree": None,
        "specialization": None,
        "university": None,
        "year": None
    }

    # Step 1: Extract education block
    lines = text.splitlines()
    edu_block = []
    for i, line in enumerate(lines):
        if "education" in line.lower():
            edu_block = lines[i:i+8]
            break
    if not edu_block:
        return result

    # Step 2: Best fuzzy degree match
    best_match = {
        "score": 0,
        "line": None,
        "alias": None,
        "canonical": None
    }

    for line in edu_block:
        clean_line = line.strip().lower().replace(".", "")
        if "certified" in clean_line or "certification" in clean_line:
            continue

        for alias, canonical in alias_to_canonical.items():
            score = fuzz.token_set_ratio(alias, clean_line)
            if score >= threshold and score > best_match["score"]:
                best_match.update({
                    "score": score,
                    "line": line.strip(),
                    "alias": alias,
                    "canonical": canonical
                })

    # Step 3: Extract specialization, university, year
    if best_match["canonical"]:
        result["degree"] = best_match["canonical"]
        line = best_match["line"]
        alias = best_match["alias"]

        # Specialization
        match = re.search(rf"{alias}[\s:-]*in[\s:-]*(.*?)(?:,|\n|\.|\d{{4}}|$)", line.lower().replace(".", ""))
        if match:
            result["specialization"] = match.group(1).strip(" ,.-\n\t").title()
        else:
            tail = line.lower().split(alias)[-1]
            if tail and len(tail.split()) >= 2:
                result["specialization"] = tail.strip(" ,.-\n\t").title()

        # University (regex match against all aliases)
        for uni in university_data:
            for name, aliases in uni.items():  # e.g., { "VIT": ["VIT", "VIT Vellore"] }
                for alt_name in aliases:
                    pattern = re.compile(rf"\b{re.escape(alt_name.lower())}\b", re.IGNORECASE)
                    if pattern.search(line.lower()):
                        result["university"] = name  # Return canonical name
                        break
                if result["university"]:
                    break
            if result["university"]:
                break

        # Year
        year_match = re.search(r"\b(19[5-9]\d|20[0-3]\d)\b", line)
        if year_match:
            result["year"] = year_match.group(0)

    return result