import re
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()


class LanguageDetector:
    """语言检测工具类"""
    
    @staticmethod
    def detect_language(text):
        """
        检测文本语言
        优先级：日文 > 英文 > 中文
        
        Args:
            text (str): 要检测的文本
            
        Returns:
            str: 语言代码 'ja', 'en', 'cn'
        """
        if not text or not isinstance(text, str):
            return 'cn'  # 默认返回中文
        
        # 移除空格和标点符号进行检测
        clean_text = re.sub(r'[^\w]', '', text)
        
        if not clean_text:
            return 'cn'
        
        # 日文检测 - 平假名、片假名、日文汉字
        japanese_chars = 0
        # 平假名范围: \u3040-\u309F
        # 片假名范围: \u30A0-\u30FF  
        # 日文汉字范围: \u4E00-\u9FAF (部分与中文重叠，需结合假名判断)
        for char in clean_text:
            if '\u3040' <= char <= '\u309F' or '\u30A0' <= char <= '\u30FF':
                japanese_chars += 1
        
        # 如果包含假名，判断为日文
        if japanese_chars > 0:
            logger.bind(tag=TAG).debug(f"检测到日文字符，文本: {text[:50]}...")
            return 'ja'
        
        # 英文检测 - ASCII字母
        english_chars = 0
        for char in clean_text:
            if 'a' <= char.lower() <= 'z':
                english_chars += 1
        
        # 中文检测 - 中日韩统一表意文字
        chinese_chars = 0
        for char in clean_text:
            if '\u4E00' <= char <= '\u9FAF':
                chinese_chars += 1
        
        # 计算比例
        total_chars = len(clean_text)
        english_ratio = english_chars / total_chars if total_chars > 0 else 0
        chinese_ratio = chinese_chars / total_chars if total_chars > 0 else 0
        
        # 判断逻辑：英文字符占比 > 50% 认为是英文
        if english_ratio > 0.5:
            logger.bind(tag=TAG).debug(f"检测到英文，文本: {text[:50]}...")
            return 'en'
        
        # 包含中文字符或其他情况默认为中文
        if chinese_ratio > 0 or english_ratio <= 0.5:
            logger.bind(tag=TAG).debug(f"检测到中文，文本: {text[:50]}...")
            return 'cn'
        
        # 默认返回中文
        return 'cn'
    
    @staticmethod
    def get_language_code_mapping():
        """
        获取语言代码映射关系
        
        Returns:
            dict: 语言代码映射
        """
        return {
            'cn': '中文',
            'en': '英文', 
            'ja': '日文'
        }


# 测试函数
if __name__ == "__main__":
    detector = LanguageDetector()
    
    test_texts = [
        "这是一段中文文本",
        "This is an English text",
        "これは日本語のテストです",
        "こんにちは、世界！",
        "Hello 世界",
        "中文English日本語混合文本",
        "123456",
        "",
        None
    ]
    
    for text in test_texts:
        lang = detector.detect_language(text)
        print(f"文本: '{text}' -> 语言: {lang}")
