import spacy

def load_spacy_nlp_model(model_name="en_core_web_sm"):
    return spacy.load(model_name)
