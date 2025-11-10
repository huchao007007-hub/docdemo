from openai import OpenAI
from config import Config
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class AIService:
    """AI服务，使用DeepSeek API"""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=Config.DEEPSEEK_API_KEY,
            base_url=Config.DEEPSEEK_BASE_URL
        )
    
    def summarize_text(self, text: str, max_tokens: int = 2000) -> Tuple[Optional[str], Optional[int]]:
        """
        使用DeepSeek API总结文本
        
        Args:
            text: 要总结的文本内容
            max_tokens: 最大输出token数
            
        Returns:
            总结内容，如果失败返回None
        """
        try:
            # 如果文本太长，需要截断（DeepSeek支持128K，但为了安全起见，我们限制在更小的范围内）
            # 如果文本超过128K tokens，需要分块处理
            max_input_tokens = 120000  # 保留一些buffer
            
            # 简单估算：1 token ≈ 4个字符（中文）
            if len(text) > max_input_tokens * 4:
                logger.warning(f"文本过长，将截断到 {max_input_tokens * 4} 字符")
                text = text[:max_input_tokens * 4]
            
            prompt = f"""请对以下文档内容进行总结，要求：
1. 总结要全面、准确，涵盖文档的主要内容和要点
2. 使用清晰的结构，可以使用标题和段落
3. 突出文档的核心观点和关键信息
4. 如果文档较长，请按章节或主题进行分段总结
5. 总结语言要简洁明了，便于理解

文档内容：
{text}

请开始总结："""
            
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个专业的文档总结助手，擅长提取和总结文档的核心内容。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            summary = response.choices[0].message.content
            token_used = response.usage.total_tokens if response.usage else None
            
            logger.info(f"AI总结成功，使用token数: {token_used}")
            return summary, token_used
        
        except Exception as e:
            logger.error(f"AI总结失败: {str(e)}")
            return None, None
    
    def summarize_long_text(self, text: str, chunk_size: int = 100000) -> Tuple[Optional[str], Optional[int]]:
        """
        处理超长文本，分块总结后再合并
        
        Args:
            text: 要总结的文本内容
            chunk_size: 每块文本的大小（字符数）
            
        Returns:
            总结内容
        """
        if len(text) <= chunk_size:
            return self.summarize_text(text)
        
        # 分块处理
        chunks = []
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i + chunk_size]
            summary, _ = self.summarize_text(chunk, max_tokens=1500)
            if summary:
                chunks.append(summary)
        
        if not chunks:
            return None, None
        
        # 合并所有块的总结
        combined_summary = "\n\n".join(chunks)
        final_summary, token_used = self.summarize_text(
            combined_summary, 
            max_tokens=2000
        )
        
        return final_summary, token_used

