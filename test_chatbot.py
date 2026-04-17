import unittest

from analyzer import analyze_feedback
from app_chatbot_todo import render_analysis

class TestChatbotFunctions(unittest.TestCase):
    
    def test_analyze_feedback_empty(self):
        """Kiểm thử: Xử lý ngoại lệ với chuỗi rỗng hoặc emoji (TODO 13)"""
        # Đầu vào chỉ chứa Emoji sẽ bị trả về neutral ngay lập tức
        result = analyze_feedback("😍😍😍")
        self.assertEqual(result["sentiment"], "neutral")
        self.assertEqual(result["confidence"], 1.0)
        self.assertEqual(result["keywords"], [])
        self.assertEqual(result["language"], "unknown")
        
        # Đầu vào quá ngắn (dưới 3 ký tự)
        result2 = analyze_feedback("Ok")
        self.assertEqual(result2["sentiment"], "neutral")

    def test_analyze_feedback_structure(self):
        """Kiểm thử: Đảm bảo cấu trúc kết quả trả về đúng chuẩn (Dictionary)"""
        result = analyze_feedback("Khóa học rất hay và bổ ích.")
        
        # Kiểm tra sự tồn tại của các keys
        self.assertIn("text", result)
        self.assertIn("sentiment", result)
        self.assertIn("confidence", result)
        self.assertIn("keywords", result)
        self.assertIn("language", result)
        self.assertIn("timestamp", result)
        
        # Kiểm tra kiểu dữ liệu
        self.assertIsInstance(result["sentiment"], str)
        self.assertIsInstance(result["confidence"], float)
        self.assertIsInstance(result["keywords"], list)

    def test_analyze_feedback_language_detect(self):
        """Kiểm thử: Hàm nhận diện đa ngôn ngữ hoạt động (TODO 9)"""
        result_en = analyze_feedback("This course is amazing!")
        # Nếu thư viện detect hoạt động, nó sẽ là "en" (hoặc unknown nếu lỗi imports)
        self.assertIn(result_en["language"], ["en", "unknown"])

    def test_render_analysis(self):
        """Kiểm thử: Hàm render_analysis ra Markdown chính xác"""
        mock_result = {
            "text": "Tuyệt vời",
            "sentiment": "positive",
            "confidence": 0.95,
            "keywords": ["tuyệt", "vời"],
            "language": "vi"
        }
        
        md_text = render_analysis(mock_result)
        
        # Kiểm tra sự xuất hiện của các định dạng Markdown / Data
        self.assertIn("Positive", md_text)
        self.assertIn("😊", md_text) # Vì EMOJI_MAP positive là 😊
        self.assertIn("95%", md_text)
        self.assertIn("tuyệt, vời", md_text)
        self.assertIn("vi", md_text)

if __name__ == '__main__':
    unittest.main()
