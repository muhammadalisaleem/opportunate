import json
from rapidfuzz import process, fuzz
from preprocessor.jd_section_parser import split_jd_sections_with_guesses, SECTION_WEIGHTS

# Load skill aliases as flat list
with open("data/dataset/skills.json") as f:
    skill_alias_map = json.load(f)

skills_alias_to_canonical = {
    alias.lower().strip(): canonical.strip()
    for canonical, aliases in skill_alias_map.items()
    for alias in aliases
}

ALL_SKILL_ALIASES = list(skills_alias_to_canonical.keys())

# Load soft skills
with open("data/dataset/soft_skills.json") as f:
    soft_skills_map = json.load(f)

sskills_alias_to_canonical = {
    alias.lower().strip(): canonical.strip()
    for canonical, aliases in soft_skills_map.items()
    for alias in aliases
}

ALL_SSKILLS_ALIASES = list(sskills_alias_to_canonical.keys())


# Generate 1- to 5-gram phrases from a spaCy Doc
def get_ngrams(doc, max_n=5):
    ngrams = set()
    tokens = [token.text.lower() for token in doc if token.is_alpha and not token.is_stop]

    for n in range(1, max_n + 1):
        for i in range(len(tokens) - n + 1):
            ngram = " ".join(tokens[i:i+n])
            ngrams.add(ngram)

    return ngrams


# Resume fuzzy skill extractor → returns canonical hard skills
def extract_skills_fuzzy(doc, threshold=90):
    ngram_phrases = get_ngrams(doc)
    matched_canonical = set()

    for phrase in ngram_phrases:
        result = process.extractOne(phrase, ALL_SKILL_ALIASES, scorer=fuzz.token_sort_ratio)
        if result:
            best_alias, score, _ = result
            if score >= threshold:
                canonical = skills_alias_to_canonical[best_alias]
                matched_canonical.add(canonical)

    return list(matched_canonical)


# Resume fuzzy soft skill extractor
def extract_soft_skills_fuzzy(doc, threshold=80):
    ngram_phrases = get_ngrams(doc)
    matched_canonical = set()

    for phrase in ngram_phrases:
        result = process.extractOne(phrase, ALL_SSKILLS_ALIASES, scorer=fuzz.token_sort_ratio)
        if result:
            best_alias, score, _ = result
            if score >= threshold:
                canonical = sskills_alias_to_canonical[best_alias]
                matched_canonical.add(canonical)

    return list(matched_canonical)


# Parse Job Description → section-wise weighted skill map
def weighted_skill_analysis(jd_text, nlp):
    sections = split_jd_sections_with_guesses(jd_text)
    hard_skills_weighted = {}
    soft_skills = set()

    for section_type, section_text in sections:
        weight = SECTION_WEIGHTS.get(section_type, 0.5)
        section_doc = nlp(section_text)
        section_ngrams = get_ngrams(section_doc)

        # Hard skills per section
        for phrase in section_ngrams:
            result = process.extractOne(phrase, ALL_SKILL_ALIASES, scorer=fuzz.token_sort_ratio)
            if result:
                best_alias, score, _ = result
                if score >= 90:
                    canonical = skills_alias_to_canonical[best_alias]
                    hard_skills_weighted[canonical] = hard_skills_weighted.get(canonical, 0) + weight

        # Soft skills per section
        for phrase in section_ngrams:
            result = process.extractOne(phrase, ALL_SSKILLS_ALIASES, scorer=fuzz.token_sort_ratio)
            if result:
                best_alias, score, _ = result
                if score >= 80:
                    canonical = sskills_alias_to_canonical[best_alias]
                    soft_skills.add(canonical)

    return hard_skills_weighted, soft_skills
