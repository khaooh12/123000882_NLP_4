# ============================================================
# app_chatbot.py (Chatbot Phân tích Phản hồi SV)
# ============================================================

import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
import io
import re

# Import từ module tách rời (TODO 15)
from analyzer import load_stopwords, get_model, analyze_feedback, detect_language, STOPWORDS

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
# HÀM VIEW
# ============================================================

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
    """Đọc file CSV/Excel upload, trả về list phản hồi."""
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
    """Chuyển lịch sử phân tích thành CSV bytes để download."""
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
    """Vẽ word cloud từ danh sách từ khóa."""
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
    """Vẽ biểu đồ xu hướng cảm xúc theo thời gian."""
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
    """Hiển thị thống kê tổng hợp trên sidebar."""
    if not history:
        st.info("Chưa có dữ liệu thống kê.")
        return
        
    df = pd.DataFrame(history)
    # Chế độ so sánh 2 nửa dữ liệu dựa vào thời gian/thứ tự
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
    """Persist lịch sử ra file JSON/DB."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def load_history(path: str = "history.json") -> list[dict]:
    """Load lịch sử từ file JSON/DB."""
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def delete_feedback(index: int):
    """Xóa một phản hồi theo index khỏi history + messages."""
    if 0 <= index < len(st.session_state.history):
        st.session_state.history.pop(index)
        
        # Mảng messages chứa cặp user/assistant => index messages: index * 2
        msg_idx = index * 2
        if 0 <= msg_idx < len(st.session_state.messages) - 1:
            st.session_state.messages.pop(msg_idx) # User message
            st.session_state.messages.pop(msg_idx) # Assistant message (shift after prev pop)
            
        save_history(st.session_state.history)



# ============================================================
# HÀM UI PHỤ
# ============================================================
def render_help_page():
    """Hiển thị trang hướng dẫn sử dụng."""
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
        
        # Handle file upload
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
        
        # Nút export_history
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
            
    # Edit/Delete option - Quản lý xóa phản hồi
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
        # Quá trình detect language và analyze cho từng dòng
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



if __name__ == "__main__":
    main()
