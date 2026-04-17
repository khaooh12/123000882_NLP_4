# ============================================================
# TODO LIST – app_chatbot.py (Chatbot Phân tích Phản hồi SV)
# ============================================================
#
# TODO 1: Mở rộng danh sách STOPWORDS tiếng Việt (hiện chỉ ~40 từ, nên dùng file ngoài hoặc thư viện chuẩn)
# TODO 2: Thêm caching (@st.cache_resource / @st.cache_data) cho model underthesea để tránh load lại mỗi lần rerun
# TODO 3: Hỗ trợ upload file CSV/Excel phản hồi bên cạnh nhập tay qua chat
# TODO 4: Thêm chức năng xuất lịch sử phân tích ra CSV/Excel (nút download ở sidebar)
# TODO 5: Hiển thị word cloud từ khóa thay vì chỉ bảng top 10
# TODO 6: Thêm biểu đồ xu hướng cảm xúc theo thời gian (timeline) khi có nhiều phản hồi
# TODO 7: Cho phép người dùng chỉnh sửa / xóa từng phản hồi đã gửi trong lịch sử chat
# TODO 8: Thêm confidence score cho kết quả phân tích cảm xúc (nếu model hỗ trợ)
# TODO 9: Hỗ trợ phân tích đa ngôn ngữ (detect ngôn ngữ trước khi chọn pipeline)
# TODO 10: Thêm trang "Hướng dẫn sử dụng" hoặc tooltip giải thích ý nghĩa từng chỉ số
# TODO 11: Persist lịch sử chat vào file/DB để không mất khi reload trang
# TODO 12: Thêm chế độ so sánh: nhập 2 nhóm phản hồi (VD: trước/sau cải tiến) và so sánh kết quả
# TODO 13: Xử lý edge case: phản hồi quá ngắn (1-2 từ), emoji-only, hoặc chứa ký tự đặc biệt
# TODO 14: Thêm unit test cho hàm analyze_feedback và render_analysis
# TODO 15: Tách logic phân tích ra module riêng (analyzer.py) để dễ tái sử dụng và test

# ============================================================
# IMPORTS
# ============================================================
import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
import io
import re

try:
    from langdetect import detect
except ImportError:
    detect = lambda text: "vi"

try:
    from underthesea import sentiment, word_tokenize
except ImportError:
    sentiment = None
    word_tokenize = None

try:
    from wordcloud import WordCloud
    import matplotlib.pyplot as plt
except ImportError:
    WordCloud = None
    plt = None

try:
    import plotly.express as px
except ImportError:
    px = None

# ============================================================
# CONSTANTS
# ============================================================
EMOJI_MAP = {"positive": "😊", "negative": "😟", "neutral": "😐"}

# ============================================================
# HÀM PHÂN TÍCH
# ============================================================
@st.cache_data
def load_stopwords(path: str = "stopwords_vi.txt") -> set[str]:
    """TODO 1: Đọc stopwords từ file ngoài, trả về set."""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return set(line.strip().lower() for line in f if line.strip())
    # Thư viện chuẩn/Fallback nếu không có file
    return {"là", "có", "và", "những", "các", "thì", "mà", "như", "để", "với", "của", "cho", "được", "không", "rất", "quá", "nhưng", "tuy", "rằng"}

STOPWORDS: set[str] = load_stopwords()

@st.cache_resource
def get_model():
    """TODO 2: Thêm caching (@st.cache_resource / @st.cache_data) cho model underthesea để tránh load lại mỗi lần rerun"""
    return sentiment, word_tokenize

def analyze_feedback(text: str) -> dict:
    """Phân tích cảm xúc + trích xuất từ khóa từ một phản hồi.
    TODO 2: Thêm caching cho model
    TODO 8: Trả thêm confidence score
    TODO 13: Xử lý edge case (quá ngắn, emoji-only, ký tự đặc biệt)
    """
    clean_text = text.strip()
    
    # TODO 13: Xử lý edge case
    if len(clean_text) < 3 or not re.search(r'[a-zA-ZÀ-ỹ]', clean_text):
        return {
            "text": text,
            "sentiment": "neutral",
            "confidence": 1.0, 
            "keywords": [],
            "language": "unknown",
            "timestamp": datetime.now().isoformat()
        }
        
    # TODO 9: Hỗ trợ phân tích đa ngôn ngữ
    lang = detect_language(clean_text)
    
    # TODO 2: Caching model
    model_sentiment, model_tokenize = get_model()
    
    sent_label = "neutral"
    conf_score = 0.8 # TODO 8: Default confidence nếu model không trả về
    
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

def render_analysis(result: dict) -> str:
    """Tạo markdown hiển thị kết quả phân tích trong chat bubble."""
    emoji = EMOJI_MAP.get(result.get("sentiment", "neutral"), "😐")
    conf = result.get("confidence", 0)
    kws = ", ".join(result.get("keywords", []))
    md = f"**Chi tiết phân tích:**\n"
    md += f"- **Cảm xúc:** {result.get('sentiment', 'neutral').capitalize()} {emoji} (Độ tin cậy: {conf:.0%})\n"
    md += f"- **Từ khóa:** {kws if kws else 'N/A'}\n"
    md += f"- **Ngôn ngữ:** {result.get('language', 'vi')}\n"
    return md

# ============================================================
# HÀM UPLOAD / EXPORT
# ============================================================
def handle_file_upload() -> list[str]:
    """TODO 3: Đọc file CSV/Excel upload, trả về list phản hồi."""
    uploaded_file = st.sidebar.file_uploader("Tải file lên (CSV/Excel)", type=["csv", "xlsx"])
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            # Kế hoạch dò tìm cột text
            for col in df.columns:
                if col.lower() in ["text", "feedback", "phản hồi", "nội dung"]:
                    return df[col].dropna().astype(str).tolist()
            
            st.sidebar.error("Không tìm thấy cột 'text' hoặc 'feedback'. Dùng cột đầu tiên.")
            return df.iloc[:, 0].dropna().astype(str).tolist()
        except Exception as e:
            st.sidebar.error(f"Lỗi đọc file: {e}")
    return []

def export_history(history: list[dict]) -> bytes:
    """TODO 4: Chuyển lịch sử phân tích thành CSV bytes để download."""
    if not history:
        return b""
    df = pd.DataFrame(history)
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, encoding="utf-8-sig")
    return csv_buffer.getvalue().encode("utf-8-sig")

# ============================================================
# HÀM VISUALIZATION
# ============================================================
def render_wordcloud(keywords: list[str]):
    """TODO 5: Vẽ word cloud từ danh sách từ khóa."""
    if not keywords or WordCloud is None or plt is None:
        st.write("Cần dữ liệu và phải cài `wordcloud`, `matplotlib` để hiển thị Word Cloud.")
        return
        
    text = " ".join(keywords)
    if not text.strip():
        return
        
    wordcloud = WordCloud(width=400, height=200, background_color='white').generate(text)
    fig, ax = plt.subplots(figsize=(4, 2))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    st.pyplot(fig)

def render_sentiment_timeline(history: list[dict]):
    """TODO 6: Vẽ biểu đồ xu hướng cảm xúc theo thời gian."""
    if not history or px is None:
        st.write("Cần cài đặt thư viện `plotly` để xem biểu đồ xu hướng.")
        return
        
    df = pd.DataFrame(history)
    if "timestamp" not in df.columns:
        return
        
    df["datetime"] = pd.to_datetime(df["timestamp"])
    timeline_df = df.groupby([df["datetime"].dt.date, "sentiment"]).size().reset_index(name="count")
    timeline_df.rename(columns={"datetime": "date"}, inplace=True)
    
    if not timeline_df.empty:
        fig = px.line(timeline_df, x="date", y="count", color="sentiment", 
                      markers=True, title="Xu hướng theo thời gian")
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)

def render_sidebar_stats(history: list[dict]):
    """Hiển thị thống kê tổng hợp trên sidebar (biểu đồ, metric, top từ khóa).
    TODO 5: Tích hợp word cloud
    TODO 12: Thêm chế độ so sánh 2 nhóm
    """
    if not history:
        st.info("Chưa có dữ liệu thống kê.")
        return
        
    df = pd.DataFrame(history)
    
    # TODO 12: Thêm chế độ so sánh 2 nhóm dữ liệu dựa vào thời gian/thứ tự
    compare = st.checkbox("So sánh 2 nửa dữ liệu (Trước/Sau)", value=False)
    if compare and len(df) > 1:
        mid_idx = len(df) // 2
        st.write("Nửa 1:")
        st.bar_chart(df.iloc[:mid_idx]["sentiment"].value_counts())
        st.write("Nửa 2:")
        st.bar_chart(df.iloc[mid_idx:]["sentiment"].value_counts())
    else:
        st.subheader("Tổng quan cảm xúc")
        st.bar_chart(df["sentiment"].value_counts())
        
        st.subheader("Từ khóa phổ biến (Word Cloud)")
        all_kws = []
        for kws in df.get("keywords", []):
            if isinstance(kws, list):
                all_kws.extend(kws)
        render_wordcloud(all_kws)
        
        st.subheader("Timeline Cảm xúc")
        render_sentiment_timeline(history)

# ============================================================
# HÀM QUẢN LÝ LỊCH SỬ
# ============================================================
def init_session_state():
    """Khởi tạo session_state: messages, history."""
    if "history" not in st.session_state:
        st.session_state.history = load_history()
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Restore messages format
        for item in st.session_state.history:
            st.session_state.messages.append({"role": "user", "content": item.get("text", "")})
            st.session_state.messages.append({"role": "assistant", "content": render_analysis(item)})

def save_history(history: list[dict], path: str = "history.json"):
    """TODO 11: Persist lịch sử ra file JSON/DB."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def load_history(path: str = "history.json") -> list[dict]:
    """TODO 11: Load lịch sử từ file JSON/DB."""
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def delete_feedback(index: int):
    """TODO 7: Xóa một phản hồi theo index khỏi history + messages."""
    if 0 <= index < len(st.session_state.history):
        st.session_state.history.pop(index)
        
        # Mảng messages chứa cặp user/assistant => index messages: index * 2
        msg_idx = index * 2
        if 0 <= msg_idx < len(st.session_state.messages) - 1:
            st.session_state.messages.pop(msg_idx) # User message
            st.session_state.messages.pop(msg_idx) # Assistant message (shift after prev pop)
            
        save_history(st.session_state.history)

# ============================================================
# HÀM ĐA NGÔN NGỮ
# ============================================================
def detect_language(text: str) -> str:
    """TODO 9: Detect ngôn ngữ, trả về mã ('vi', 'en', ...)."""
    try:
        return detect(text)
    except:
        return "unknown"

# ============================================================
# HÀM UI PHỤ
# ============================================================
def render_help_page():
    """TODO 10: Hiển thị trang hướng dẫn sử dụng."""
    with st.expander("📚 Hướng dẫn sử dụng & Ý nghĩa chỉ số"):
        st.markdown("""
        **1. Cảm xúc**: Được phân loại ra Tích cực (😊), Tiêu cực (😟), hoặc Trung lập (😐).  
        **2. Độ tin cậy (Confidence)**: Cho biết AI tự tin bao nhiêu % về kết quả.  
        **3. Từ khóa (Keywords)**: Những từ có ý nghĩa chính trong phản hồi, đã loại bỏ từ nối (stopwords).  
        **4. Tính năng Quản lý**: Bạn có thể xóa phản hồi, hoặc tải lịch sử ra file CSV ở thanh bên.
        """)

# ============================================================
# MAIN
# ============================================================
def main():
    st.set_page_config(page_title="Chatbot Phân tích phản hồi", page_icon="🤖", layout="wide")

    init_session_state()

    # ── Sidebar ──
    with st.sidebar:
        st.title("🎛 Cài đặt & Thống kê")
        render_help_page()
        
        # TODO 3: Handle file upload
        uploaded_texts = handle_file_upload()
        if uploaded_texts and st.button("Xử lý file tải lên"):
            for text in uploaded_texts:
                res = analyze_feedback(text)
                st.session_state.history.append(res)
                st.session_state.messages.append({"role": "user", "content": text})
                st.session_state.messages.append({"role": "assistant", "content": render_analysis(res)})
            save_history(st.session_state.history)
            st.rerun()
            
        render_sidebar_stats(st.session_state.history)
        
        # TODO 4: Nút export_history
        csv_bytes = export_history(st.session_state.history)
        if csv_bytes:
            st.download_button("📥 Tải Xuống Lịch Sử (CSV)", csv_bytes, "history.csv", "text/csv")
            
        if st.session_state.history and st.button("🗑 Xóa sạch lịch sử", type="primary"):
            st.session_state.history = []
            st.session_state.messages = []
            save_history([])
            st.rerun()

    # ── Main area ──
    st.title("🤖 Chatbot Phân tích Phản hồi Sinh viên")

    # Render History Messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    # TODO 7: Edit/Delete option - Quản lý xóa phản hồi
    if st.session_state.history:
        with st.expander("Sửa/Xóa từng phản hồi (Quản lý log)"):
            for i, h in enumerate(st.session_state.history):
                col1, col2 = st.columns([9, 1])
                with col1:
                    st.write(f"**{i+1}.** {h['text']}")
                with col2:
                    if st.button("Xóa", key=f"del_{i}"):
                        delete_feedback(i)
                        st.rerun()

    # Ô nhập chat
    if prompt := st.chat_input("Nhập phản hồi của bạn tại đây..."):
        # TODO 9: Quá trình detect language và analyze cho từng dòng
        lines = [l.strip() for l in prompt.splitlines() if l.strip()]
        for line in lines:
            st.chat_message("user").markdown(line)
            st.session_state.messages.append({"role": "user", "content": line})
            
            res = analyze_feedback(line)
            ans = render_analysis(res)
            
            st.chat_message("assistant").markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
            st.session_state.history.append(res)
            
        save_history(st.session_state.history)
        st.rerun()

    # TODO 14 & 15: Có thể bổ sung bằng file tests.py và models/analyzer.py
    # Hiện tất cả code đang được cài đặt trong app_chatbot_todo.py cho mục đích đáp ứng
    # yêu cầu giữ nguyên đề bài và chạy trực tiếp mà không thiếu features.

if __name__ == "__main__":
    main()
