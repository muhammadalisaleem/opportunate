import re
from preprocessor.skills import extract_skills_fuzzy, extract_soft_skills_fuzzy
from preprocessor.spacy_nlp import load_spacy_nlp_model
from collections import Counter

nlp = load_spacy_nlp_model("en_core_web_sm")

def run_local_ats_analysis(text, uploaded_file):
    doc = nlp(text)
    sections = []

    # Step 1: Contact Information
    email = re.search(r"[\w\.-]+@[\w\.-]+", text)
    phone = re.search(r"\+?\d[\d\s\-]{7,15}", text)
    linkedin = re.search(r"linkedin\.com/in/\S+", text)
    section_1 = {
        "step": 1,
        "title": "Contact Information Check",
        "findings": [],
    }
    section_1["findings"].append(("success", "Email detected") if email else ("warning", "No email found"))
    section_1["findings"].append(("success", "Phone number detected") if phone else ("warning", "No phone number found"))
    section_1["findings"].append(("success", "LinkedIn profile found") if linkedin else ("warning", "LinkedIn profile missing"))
    sections.append(section_1)

    # Step 2: Grammar (basic)
    grammar_errors = re.findall(r"\b[A-Z][a-z]+ [a-z]+ [A-Z][a-z]+\b", text)
    sections.append({
        "step": 2,
        "title": "Spelling & Grammar Check",
        "findings": [("success", "No obvious grammar/spelling issues detected")] if len(grammar_errors) < 2 else [("warning", "Possible grammar or capitalization issues found")]
    })

    # Step 3: Personal Pronouns
    personal_pronouns = re.findall(r"\b(I|me|my|mine|we|our)\b", text, re.IGNORECASE)
    sections.append({
        "step": 3,
        "title": "Personal Pronoun Check",
        "findings": [("success", "No personal pronouns used")] if not personal_pronouns else [("warning", f"{len(personal_pronouns)} personal pronouns found. Avoid them.")]
    })

    # Step 4: Skills & Keywords
    tech_skills = extract_skills_fuzzy(doc)
    soft_skills = extract_soft_skills_fuzzy(doc)
    findings = []
    if tech_skills:
        findings.append(("success", f"Detected Technical Skills: {', '.join(tech_skills)}"))
    else:
        findings.append(("warning", f"Technical Skills not detected"))
    if soft_skills:
        findings.append(("success", f"Detected Soft Skills: {', '.join(soft_skills)}"))
    else:
        findings.append(("warning", f"Soft Skills not detected"))
    sections.append({
        "step": 4,
        "title": "Skills & Keyword Targeting",
        "findings": findings
    })

    # Step 5: Complex Sentences
    long_sents = [sent.text for sent in doc.sents if len(sent.text.split()) > 40]
    sections.append({
        "step": 5,
        "title": "Long Sentences",
        "findings": [("warning", f"Long sentence: {s[:80]}...") for s in long_sents] if long_sents else [("success", "No long sentences found")]
    })

    
    # Step 6: Generic Sentences
    generic_phrases = [
        "responsible for", "worked on", "helped", "tasked with", "participated in", "assisted with", "handled",
        "involved in", "part of", "supported", "duties included", "played a role in", "knowledge of", "familiar with",
        "exposure to", "experience in", "performed", "used to", "took part in", "made", "did", "contributed to", "led",
        "managed", "oversaw", "ran", "coordinated", "scheduled", "organized", "arranged", "created", "built", "developed",
        "designed", "engineered", "deployed", "launched", "implemented", "executed", "collaborated with", "worked closely with",
        "worked as", "worked under", "followed up on", "took responsibility for", "supervised", "trained", "mentored",
        "assumed responsibility for", "provided support", "provided assistance", "gave input on", "attended", "joined",
        "contributed", "assumed the role of", "followed", "performed duties", "assigned to", "utilized", "used",
        "applied knowledge of", "leveraged", "made sure", "ensured", "ensured compliance", "validated", "checked",
        "verified", "responded to", "answered", "dealt with", "addressed", "resolved", "fixed", "improved", "streamlined",
        "upgraded", "enhanced", "maintained", "supported users", "gave feedback", "filled in", "acted as", "liaised with",
        "followed procedures", "enforced policies", "interfaced with", "contributed ideas", "wrote", "edited", "documented",
        "reported on", "compiled", "tracked", "monitored", "recorded", "calculated", "evaluated", "tested", "analyzed data",
        "reviewed", "produced", "submitted"
    ]

    text_lower = text.lower()
    phrase_counter = Counter()

    for phrase in generic_phrases:
        count = text_lower.count(phrase)
        if count > 2:
            phrase_counter[phrase] = count

    if phrase_counter:
        findings = [
            ("warning", f"Generic phrase used: '{phrase}' — {count} times")
            for phrase, count in phrase_counter.items()
        ]
    else:
        findings = [("success", "No overused generic phrases found")]

    sections.append({
        "step": 6,
        "title": "Generic Sentences",
        "findings": findings
    })

    # Step 7: Passive Voice
    passive_indicators = [
        "was", "were", "is", "are", "been", "being", "be",
        "has been", "have been", "had been",
        "will be", "would be", "shall be", "should be", "can be", "could be", "may be", "might be", "must be"
    ]
    passive_patterns = [
    re.compile(rf"\b{aux}\b\s+\b\w+(ed|en)\b", re.IGNORECASE) for aux in passive_indicators
    ]

    passive_sentences = []
    for sent in doc.sents:
        for pattern in passive_patterns:
            if pattern.search(sent.text):
                passive_sentences.append(sent.text.strip())
                break

    sections.append({
        "step": 7,
        "title": "Passive Sentences",
        "findings": [("warning", f"Passive: {p[:80]}...") for p in passive_sentences] if passive_sentences else [("success", "No passive voice detected")]
    })

    # Step 8: Quantified Achievements
    metrics = re.findall(r"\d+%|\d{2,}", text)
    sections.append({
        "step": 8,
        "title": "Quantified Points",
        "findings": [("success", f"{len(metrics)} quantified results found")] if metrics else [("warning", "No quantified achievements (%, numbers) found")]
    })

    # Step 9: Essential Resume Sections
    required_sections = ["summary", "education", "experience", "skills"]
    missing_sections = [s for s in required_sections if s not in text.lower()]
    sections.append({
        "step": 9,
        "title": "Essential Resume Sections",
        "findings": [("warning", f"Missing section: {', '.join(missing_sections)}")] if missing_sections else [("success", "All essential sections found")]
    })

    # Step 10: Repeated Action Verbs
    action_verb_list = [
        "achieved", "administered", "analyzed", "arranged", "built", "calculated", "collaborated", "communicated",
        "completed", "conducted", "created", "debugged", "designed", "developed", "directed", "documented", "enhanced",
        "engineered", "executed", "facilitated", "formulated", "generated", "handled", "implemented", "improved",
        "initiated", "inspired", "integrated", "led", "managed", "monitored", "negotiated", "organized", "oversaw",
        "performed", "planned", "presented", "programmed", "provided", "redesigned", "researched", "resolved", "reviewed",
        "scheduled", "solved", "streamlined", "supervised", "supported", "tested", "trained", "translated", "upgraded",
        "utilized", "validated", "wrote"
    ]

    action_verb_counter = Counter()
    text_tokens = re.findall(r"\b\w+\b", text.lower())

    for token in text_tokens:
        if token in action_verb_list:
            action_verb_counter[token] += 1

    overused_verbs = {verb: count for verb, count in action_verb_counter.items() if count > 2}

    if overused_verbs:
        findings = [
            ("warning", f"Repeated action verb: '{verb}' used {count} times")
            for verb, count in overused_verbs.items()
        ]
    else:
        findings = [("success", "No repetitive action verbs")]

    sections.append({
        "step": 10,
        "title": "Repeated Action Verbs",
        "findings": findings
    })


    # Step 11: Document Properties
    findings = []

    # Word Count Check
    word_count = len(text.split())
    if word_count <= 350:
        findings.append(("warning", f"Resume too short: {word_count} words. Aim for 350–600."))
    elif word_count > 900:
        findings.append(("warning", f"Resume too long: {word_count} words. Try shortening it."))
    else:
        findings.append(("success", f"Good resume length: {word_count} words."))

    # File Type Check
    if not uploaded_file.name.lower().endswith(".pdf"):
        findings.append(("warning", "Resume is not in PDF format. Use PDF for better ATS compatibility."))
    else:
        findings.append(("success", "PDF format detected. ATS-friendly!"))

    # File Size Check
    if uploaded_file.size > 2 * 1024 * 1024:  # 2MB = 2 * 1024 * 1024 bytes
        findings.append(("warning", f"File size is too large: {round(uploaded_file.size / (1024*1024), 2)} MB. Reduce to under 2MB."))
    else:
        findings.append(("success", f"Good file size: {round(uploaded_file.size / 1024, 1)} KB."))

    sections.append({
        "step": 11,
        "title": "Document Properties",
        "findings": findings
    })

    # Step 12: Formatting Consistency
    inconsistent_bullets = re.findall(r"\n[^\n•\-–●\*]", text)
    findings = [("warning", "Bullet formatting may be inconsistent. Kindly verify")] if len(inconsistent_bullets) > 5 else [("success", "Formatting looks consistent")]
    sections.append({
        "step": 12,
        "title": "Formatting Consistency",
        "findings": findings
    })

    return sections