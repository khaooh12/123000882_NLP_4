import os
import re
from datetime import datetime
import streamlit as st

try:
    from langdetect import detect
except ImportError:
    detect = lambda text: "vi"

try:
    from underthesea import sentiment, word_tokenize
except ImportError:
    sentiment = None
    word_tokenize = None

# ============================================================
# HÀM ĐA NGÔN NGỮ
# ============================================================
def detect_language(text: str) -> str:
    """Detect ngôn ngữ, trả về mã ('vi', 'en', ...)."""
    try:
        return detect(text)
    except:
        return "unknown"

# ============================================================
# HÀM PHÂN TÍCH
# ============================================================
@st.cache_data
def load_stopwords(path: str = "stopwords_vi.txt") -> set[str]:
    """Đọc stopwords từ file ngoài, trả về set."""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return set(line.strip().lower() for line in f if line.strip())
    # Thư viện chuẩn/Fallback nếu không có file
    return {"là", "có", "và", "những", "các", "thì", "mà", "như", "để", "với", "của", "cho", "được", "không", "rất", "quá", "nhưng", "tuy", "rằng"}

STOPWORDS: set[str] = load_stopwords()

@st.cache_resource
def get_model():
    """Thêm caching (@st.cache_resource / @st.cache_data) cho model underthesea để tránh load lại mỗi lần rerun"""
    return sentiment, word_tokenize

def analyze_feedback(text: str) -> dict:
    """Phân tích cảm xúc + trích xuất từ khóa từ một phản hồi."""
    clean_text = text.strip()
    
    # Xử lý edge case
    if len(clean_text) < 3 or not re.search(r'[a-zA-ZÀ-ỹ]', clean_text):
        return {
            "text": text,
            "sentiment": "neutral",
            "confidence": 1.0, 
            "keywords": [],
            "language": "unknown",
            "timestamp": datetime.now().isoformat()
        }
        
    # Hỗ trợ phân tích đa ngôn ngữ
    lang = detect_language(clean_text)
    
    # Caching model
    model_sentiment, model_tokenize = get_model()
    
    sent_label = "neutral"
    conf_score = 0.8 # Default confidence nếu model không trả về
    
    if model_sentiment and lang == 'vi':
        try:
            res = model_sentiment(clean_text)
            if isinstance(res, tuple):
                sent_label = res[0]
                conf_score = res[1] if len(res) > 1 else 0.8
            else:
                sent_label = str(res)
                conf_score = 0.85
        except Exception:
            pass
            
    # Chuẩn hoá sentiment
    if "tích cực" in sent_label.lower() or "positive" in sent_label.lower():
        sent_label = "positive"
    elif "tiêu cực" in sent_label.lower() or "negative" in sent_label.lower():
        sent_label = "negative"
    else:
        sent_label = "neutral"

    keywords = []
    if model_tokenize and lang == 'vi':
        try:
            tokens = model_tokenize(clean_text)
            keywords = [t.lower() for t in tokens if t.lower() not in STOPWORDS and len(t) > 1 and t.isalnum()]
        except Exception:
            pass

    return {
        "text": text,
        "sentiment": sent_label,
        "confidence": conf_score,
        "keywords": keywords,
        "language": lang,
        "timestamp": datetime.now().isoformat()
    }
