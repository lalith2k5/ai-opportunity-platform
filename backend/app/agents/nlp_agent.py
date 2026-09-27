import re
import spacy
from nltk.corpus import stopwords
from nltk.sentiment import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import NMF

class NLPAgent:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except Exception:
            self.nlp = None
        self.stop_words = set(stopwords.words("english"))
        self.sia = SentimentIntensityAnalyzer()

    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r"http\S+", "", text)
        text = re.sub(r"[^a-zA-Z\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def extract_keywords(self, text: str, top_n: int = 10) -> list:
        cleaned = self.clean_text(text)
        if not cleaned or len(cleaned) < 20:
            return []
        try:
            vectorizer = TfidfVectorizer(max_features=top_n, stop_words="english", ngram_range=(1, 2))
            vectorizer.fit_transform([cleaned])
            return list(vectorizer.get_feature_names_out())
        except Exception:
            return []

    # Words that signal the end of a real entity — RSS artifacts.
    _ENTITY_TAIL_BLOCKLIST = {
        "email", "blurb", "figure", "figures", "photo", "image", "images",
        "author", "authors", "researcher", "researchers", "student", "students",
        "university", "universities", "institute", "institutes",
        "department", "departments", "newsletter", "brief", "congratulations",
        "thanks", "acknowledgments", "acknowledgements", "abstract",
        "introduction", "conclusion", "references", "appendix",
        "january", "february", "march", "april", "may", "june", "july",
        "august", "september", "october", "november", "december",
        "monday", "tuesday", "wednesday", "thursday", "friday",
        "saturday", "sunday", "today", "tomorrow", "yesterday",
        "page", "pages", "figure", "table", "section", "chapter",
        "software", "hardware", "framework", "kernel", "kernels",
        "center", "centre", "college", "director", "showcase",
        "artificial", "machine", "learning", "deep", "data", "science",
        "intelligence", "computing", "quantum", "cloud", "healthcare",
        "medical", "medicine", "statistics", "modern", "honors", "internship",
    }

    _ENTITY_ACRONYMS = {"ai", "ml", "nlp", "llm", "iot", "api", "sdk", "cli", "gpu", "cpu"}

    def _is_valid_entity(self, text: str, label: str) -> bool:
        """Shape-based validation. Reject anything that doesn't look like a
        real named entity — proper noun casing, reasonable length, no markup."""
        if not text:
            return False

        text = text.strip().rstrip(".,;:!?()[]{}")

        # Reject HTML / URL / punctuation soup
        if any(ch in text for ch in "<>\"={}"):
            return False
        if "://" in text or text.startswith("http"):
            return False

        # Reject if contains ':' (RSS "Name: Role" fragments)
        if ":" in text:
            return False

        # Reject if too short or too long
        if len(text) < 3 or len(text) > 40:
            return False

        # Alpha ratio must be reasonable
        alpha = sum(c.isalpha() for c in text)
        if alpha < 3 or alpha / max(len(text), 1) < 0.5:
            return False

        words = text.split()
        if not words:
            return False

        # Title-case check for multi-word: at least one word must start uppercase
        # (proper noun signal). But allow single-word acronyms.
        if len(words) > 1:
            # Last word must not be a stoplist word
            if words[-1].lower().rstrip(".,;:!?") in self._ENTITY_TAIL_BLOCKLIST:
                return False
            # At least half the words must be title-cased or known acronyms
            proper = sum(
                1 for w in words
                if w[:1].isupper() or w.lower() in self._ENTITY_ACRONYMS
            )
            if proper < len(words) / 2:
                return False

        # Label-specific rules
        if label == "PERSON":
            # Real person names: 2-3 words, or single word if clearly title-cased
            if len(words) == 1:
                return False  # single-word PERSON almost always noise
            if len(words) > 4:
                return False
        elif label == "ORG":
            if len(words) > 5:
                return False
        elif label == "PRODUCT":
            if len(words) > 4:
                return False

        # Reject if the entire entity is just stoplist words
        lowered = [w.lower().rstrip(".,;:!?") for w in words]
        if all(w in self._ENTITY_TAIL_BLOCKLIST for w in lowered):
            return False

        return True

    def extract_entities(self, text: str) -> list:
        if not self.nlp or not text:
            return []
        # Strip HTML tags/attributes BEFORE passing to spaCy
        cleaned = re.sub(r"<[^>]+>", " ", text)
        cleaned = re.sub(r"&[a-zA-Z#0-9]+;", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        doc = self.nlp(cleaned[:10000])
        out = []
        seen = set()
        for ent in doc.ents:
            label = ent.label_
            if label not in ("PERSON", "ORG", "PRODUCT"):
                continue
            txt = ent.text.strip()
            if not self._is_valid_entity(txt, label):
                continue
            key = txt.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append({"text": txt, "label": label})
            if len(out) >= 20:
                break
        return out

    def analyze_sentiment(self, text: str) -> float:
        if not text:
            return 0.0
        return self.sia.polarity_scores(text)["compound"]


    def extract_topics_nmf(self, texts: list, n_topics: int = 5) -> list:
        """Proper topic modeling using NMF on TF-IDF matrix."""
        if not texts or len(texts) < 2:
            return []
        try:
            vectorizer = TfidfVectorizer(max_features=200, stop_words="english", ngram_range=(1, 2))
            X = vectorizer.fit_transform(texts)
            n_topics = min(n_topics, max(2, len(texts) // 2))
            nmf = NMF(n_components=n_topics, random_state=42, init='nndsvda', max_iter=1000)
            nmf.fit(X)
            feature_names = vectorizer.get_feature_names_out()
            topics = []
            for topic_idx, topic in enumerate(nmf.components_):
                top_indices = topic.argsort()[-6:][::-1]
                top_words = [feature_names[i] for i in top_indices]
                topics.append({
                    "topic_id": topic_idx,
                    "keywords": top_words,
                    "label": ", ".join(top_words[:3]),
                })
            return topics
        except Exception as e:
            print(f"NMF topic modeling error: {e}")
            return []


    def tokenize(self, text: str) -> list:
        """Tokenize into lowercase word tokens."""
        if not text:
            return []
        if self.nlp:
            doc = self.nlp(text[:5000])
            return [t.text.lower() for t in doc if t.is_alpha]
        # fallback: simple split
        import re
        return re.findall(r"\b[a-zA-Z]+\b", text.lower())

    def remove_stopwords(self, tokens: list) -> list:
        """Filter out English stopwords."""
        return [t for t in tokens if t not in self.stop_words and len(t) > 2]

    def process(self, text: str) -> dict:
        tokens = self.tokenize(text)
        return {
            "cleaned_text": self.clean_text(text),
            "tokens": tokens[:50],
            "filtered_tokens": self.remove_stopwords(tokens)[:30],
            "keywords": self.extract_keywords(text),
            "entities": self.extract_entities(text),
            "topics": self.extract_keywords(text, top_n=5),
            "sentiment_score": self.analyze_sentiment(text)
        }
