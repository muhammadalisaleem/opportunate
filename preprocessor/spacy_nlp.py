from functools import lru_cache

import spacy


@lru_cache(maxsize=1)
def load_spacy_nlp_model(model_name="en_core_web_sm"):
    try:
        return spacy.load(model_name)
    except Exception:
        nlp = spacy.blank("en")
        if "sentencizer" not in nlp.pipe_names:
            nlp.add_pipe("sentencizer")
        return nlp
