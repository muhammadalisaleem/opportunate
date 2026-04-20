import re
from rapidfuzz import process, fuzz

# These weights determine the scoring importance of each section
SECTION_WEIGHTS = {
    "title": 3,
    "must-have": 3,
    "requirements": 2,
    "responsibilities": 2,
    "qualifications": 2,
    "mandatory": 2,
    "preferred": 1,
    "nice-to-have": 1,
    "summary": 1,
    "other": 0.5
}

# Heuristic phrases that help identify implicit section types
SECTION_HINTS = {
    "must-have": [
        "must have",
        "you must",
        "candidates must",
        "we require",
        "mandatory skills",
        "required skills",
        "essential experience",
        "must demonstrate",
        "strong understanding of",
        "proficiency in",
        "hands-on experience with",
        "required qualifications"
    ],
    "preferred": [
        "nice to have",
        "preferred skills",
        "bonus if",
        "a plus",
        "would be beneficial",
        "ideal if",
        "good to have",
        "optional but helpful",
        "preferred qualifications",
        "experience with (not required)"
    ],
    "responsibilities": [
        "you will",
        "responsibilities include",
        "expected to",
        "your role",
        "day-to-day duties",
        "tasks involve",
        "you will be expected to",
        "role responsibilities",
        "key deliverables",
        "position overview",
        "in this role"
    ],
    "qualifications": [
        "qualifications include",
        "ideal candidate",
        "background in",
        "experience in",
        "we're looking for someone with",
        "skills and experience",
        "candidate profile",
        "educational background",
        "academic requirements",
        "desired experience",
        "minimum qualifications"
    ],
    "summary": [
        "we are looking for",
        "join our team",
        "about the role",
        "who we are",
        "company overview",
        "our mission",
        "introduction",
        "about us",
        "team description",
        "why this role",
        "position summary",
        "what we do"
    ]
}


def guess_section_from_line(line: str, threshold: int = 85):
    line_lower = line.lower()
    best_match = ("other", 0)

    for section, phrases in SECTION_HINTS.items():
        result = process.extractOne(
            line_lower,
            phrases,
            scorer=fuzz.partial_ratio
        )
        if result:
            match_phrase, score, _ = result
            if score > best_match[1] and score >= threshold:
                best_match = (section, score)

    return best_match[0]

def split_jd_sections_with_guesses(jd_text: str):
    sections = []
    current_section = "other"
    buffer = []

    lines = jd_text.splitlines()

    for line in lines:
        line_clean = line.strip()
        line_lower = line_clean.lower()

        matched_section = None
        for keyword in SECTION_WEIGHTS:
            if re.fullmatch(fr"\b{keyword}\b", line_lower):
                matched_section = keyword
                break

        if matched_section:
            if buffer:
                sections.append((current_section, "\n".join(buffer)))
                buffer = []
            current_section = matched_section

        else:
            guessed_section = guess_section_from_line(line_clean)
            if guessed_section != current_section and buffer:
                sections.append((current_section, "\n".join(buffer)))
                buffer = []
                current_section = guessed_section
            buffer.append(line_clean)

    if buffer:
        sections.append((current_section, "\n".join(buffer)))

    return sections
