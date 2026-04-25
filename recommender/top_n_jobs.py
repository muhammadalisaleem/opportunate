import json
from collections import defaultdict


def _boost_recommendations_for_preferred_role(recommendations, preferred_role):
    preferred_role_text = (preferred_role or "").strip().lower()
    if not preferred_role_text:
        return recommendations

    boosted = []
    for item in recommendations:
        recommendation = dict(item)
        job_title = str(recommendation.get("title", ""))
        title_lower = job_title.lower()

        boost = 0.0
        if preferred_role_text in title_lower:
            boost += 8.0
        if any(part.strip().lower() == preferred_role_text for part in job_title.split("/")):
            boost += 12.0

        recommendation["preferred_role_bonus"] = boost
        boosted.append(recommendation)

    boosted.sort(
        key=lambda row: (
            float(row.get("preferred_role_bonus", 0) or 0),
            float(row.get("confidence", 0) or 0),
            float(row.get("match_count", 0) or 0),
        ),
        reverse=True,
    )

    for recommendation in boosted:
        recommendation.pop("preferred_role_bonus", None)

    return boosted


def _rule_based_recommend_top_jobs(resume_skills, top_n=5, preferred_role=None):
    skill_to_job_path = "data/dataset/skill_to_job.json"
    job_definitions_path = "data/dataset/job_definition.json"

    with open(skill_to_job_path, "r", encoding="utf-8") as f:
        raw_skill_to_job = json.load(f)
    with open(job_definitions_path, "r", encoding="utf-8") as f:
        job_descriptions = json.load(f)

    skill_to_job = {skill.lower(): job for skill, job in raw_skill_to_job.items()}

    job_scores = defaultdict(lambda: {"count": 0, "skills": []})
    for skill in resume_skills:
        matching_jobs = skill_to_job.get(skill.lower(), [])
        for job in matching_jobs:
            job_scores[job]["count"] += 1  # type: ignore
            job_scores[job]["skills"].append(skill)  # type: ignore

    preferred_role_text = (preferred_role or "").strip().lower()

    def score_job(item):
        job_name, info = item
        score = info["count"]
        if preferred_role_text:
            job_name_lower = job_name.lower()
            if preferred_role_text in job_name_lower:
                score += 3
            elif any(part.strip().lower() == preferred_role_text for part in job_name.split("/")):
                score += 4
        return score

    sorted_jobs = sorted(job_scores.items(), key=score_job, reverse=True)

    top_jobs = []
    for job, info in sorted_jobs[:top_n]:
        matched_skills = sorted(set(info["skills"]))  # type: ignore
        descriptions = []

        parts = [j.strip() for j in job.split("/")]

        for part in parts:
            desc = job_descriptions.get(part)
            if desc:
                descriptions.append(f"<strong>{part}</strong>: {desc}")

        if descriptions:
            full_description = "".join(
                f"<div style='padding-left: 20px; margin-bottom: 10px;'>{desc}</div>"
                for desc in descriptions
            )
        else:
            full_description = None

        top_jobs.append(
            {
                "title": job,
                "match_count": info["count"],
                "matched_skills": matched_skills,
                "description": full_description,
                "confidence": min(
                    100,
                    info["count"] * 20 + (15 if preferred_role_text and preferred_role_text in job.lower() else 0),
                ),
                "source": "rule-based",
            }
        )

    return top_jobs


def recommend_top_jobs(resume_skills, top_n=5, resume_text=None, preferred_role=None):
    try:
        from recommender.ml_job_recommender import recommend_top_jobs as recommend_top_jobs_ml

        ml_recommendations = recommend_top_jobs_ml(
            resume_skills,
            top_n=top_n,
            resume_text=resume_text,
        )
        if ml_recommendations:
            return _boost_recommendations_for_preferred_role(ml_recommendations, preferred_role)
    except Exception:
        pass

    return _rule_based_recommend_top_jobs(
        resume_skills,
        top_n=top_n,
        preferred_role=preferred_role,
    )
