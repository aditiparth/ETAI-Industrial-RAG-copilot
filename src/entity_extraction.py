import spacy
import re

nlp = spacy.load("en_core_web_sm")
# Whitelist of real equipment-tag prefixes (pumps, valves, tanks, compressors, etc.)
EQUIPMENT_PATTERN = re.compile(r"\b(?:P|V|T|C|E|HX|PSV|D|K|R)-\d{2,4}[A-Z]?\b")

# Non-capturing group so findall returns the FULL match, not just "STD"/"GDN"
STANDARD_PATTERN = re.compile(r"\bOISD[-\s]?(?:STD|GDN|RP)?[-\s]?\d+\b", re.IGNORECASE)

def extract_entities(text):

    doc = nlp(text)
    entities = {
        "dates": [],
        "orgs": [],
        "persons": [],
        "equipment_tags": [],
        "standards": []
    }
    for ent in doc.ents:
        if ent.label_ == "DATE":
            entities["dates"].append(ent.text)
        elif ent.label_ == "ORG":
            entities["orgs"].append(ent.text)
        elif ent.label_ == "PERSON":
            entities["persons"].append(ent.text)

    entities["equipment_tags"] = list(set(EQUIPMENT_PATTERN.findall(text)))
    entities["standards"] = list(set(m.upper() for m in STANDARD_PATTERN.findall(text)))
    return entities

def extract_entities_from_chunks(chunks):
    for c in chunks:
        c["entities"] = extract_entities(c["text"])
    return chunks