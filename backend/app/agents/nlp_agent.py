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

    def extract_entities(self, text: str) -> list:
        if not self.nlp or not text:
            return []
        doc = self.nlp(text[:10000])
        return [{"text": ent.text, "label": ent.label_} for ent in doc.ents][:20]

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
