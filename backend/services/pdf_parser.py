import pdfplumber
from typing import Optional
import logging
import os

logger = logging.getLogger(__name__)

# OCR相关导入（可选，如果库不存在会有警告但不影响基本功能）
try:
    from pdf2image import convert_from_path
    import pytesseract
    from PIL import Image
    from config import Config
    OCR_AVAILABLE = True
    
    # 配置Tesseract路径（如果不在PATH中）
    if Config.TESSERACT_CMD:
        pytesseract.pytesseract.tesseract_cmd = Config.TESSERACT_CMD
        logger.info(f"使用自定义Tesseract路径: {Config.TESSERACT_CMD}")
    
    # 配置Poppler路径（如果不在PATH中）
    if Config.POPPLER_PATH:
        # pdf2image需要在导入时设置环境变量
        import os
        os.environ['PATH'] = Config.POPPLER_PATH + os.pathsep + os.environ.get('PATH', '')
        logger.info(f"使用自定义Poppler路径: {Config.POPPLER_PATH}")
        
except ImportError:
    OCR_AVAILABLE = False
    logger.warning("OCR库未安装，扫描版PDF将无法提取文本。安装命令: pip install pytesseract pdf2image Pillow")

class PDFParser:
    """PDF解析器"""
    
    @staticmethod
    def extract_text(file_path: str, use_ocr: bool = False) -> Optional[str]:
        """
        从PDF文件中提取文本内容
        
        Args:
            file_path: PDF文件路径
            use_ocr: 如果无法提取文本，是否尝试OCR识别
            
        Returns:
            提取的文本内容，如果失败返回None
        """
        # 首先尝试pdfplumber提取文本
        try:
            text_content = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
            
            if text_content:
                logger.info(f"成功从PDF提取文本: {len(text_content)} 页")
                return "\n\n".join(text_content)
            
            logger.warning(f"PDF文件 {file_path} 无法通过pdfplumber提取文本，可能是扫描版PDF")
            
            # 如果无法提取文本且允许OCR，尝试OCR识别
            if use_ocr and OCR_AVAILABLE:
                logger.info(f"尝试使用OCR识别PDF文本: {file_path}")
                return PDFParser._extract_text_with_ocr(file_path)
            
            return None
        
        except Exception as e:
            import traceback
            logger.error(f"解析PDF文件失败: {str(e)}")
            logger.error(f"错误详情: {traceback.format_exc()}")
            # 如果基本解析失败，尝试OCR
            if use_ocr and OCR_AVAILABLE:
                logger.info(f"尝试使用OCR识别PDF文本: {file_path}")
                try:
                    return PDFParser._extract_text_with_ocr(file_path)
                except Exception as ocr_error:
                    import traceback
                    logger.error(f"OCR识别失败: {str(ocr_error)}")
                    logger.error(f"OCR错误详情: {traceback.format_exc()}")
            return None
    
    @staticmethod
    def _extract_text_with_ocr(file_path: str) -> Optional[str]:
        """
        使用OCR从PDF中提取文本（用于扫描版PDF）
        
        Args:
            file_path: PDF文件路径
            
        Returns:
            提取的文本内容，如果失败返回None
        """
        if not OCR_AVAILABLE:
            logger.error("OCR库未安装，无法进行OCR识别")
            return None
        
        try:
            # 检查poppler是否可用
            import subprocess
            try:
                result = subprocess.run(['pdftoppm', '-v'], capture_output=True, text=True, timeout=5)
                logger.info(f"poppler检查: pdftoppm可用")
            except FileNotFoundError:
                logger.error("poppler未安装或不在PATH中。请安装poppler并添加到PATH环境变量。")
                logger.error("Windows安装: https://github.com/oschwartz10612/poppler-windows/releases/")
                logger.error("或使用: choco install poppler")
                return None
            except Exception as e:
                logger.warning(f"poppler检查失败: {str(e)}，但继续尝试...")
            
            # 将PDF转换为图片
            logger.info(f"正在将PDF转换为图片: {file_path}")
            logger.info(f"文件大小: {os.path.getsize(file_path) / 1024 / 1024:.2f} MB")
            
            try:
                # 如果配置了POPPLER_PATH，使用它
                if Config.POPPLER_PATH:
                    logger.info(f"使用配置的Poppler路径: {Config.POPPLER_PATH}")
                    images = convert_from_path(
                        file_path, 
                        dpi=200,
                        poppler_path=Config.POPPLER_PATH
                    )
                else:
                    images = convert_from_path(file_path, dpi=200)  # 200 DPI 平衡质量和速度
            except Exception as pdf_error:
                import traceback
                logger.error(f"PDF转图片失败: {str(pdf_error)}")
                logger.error(f"错误类型: {type(pdf_error).__name__}")
                logger.error(f"错误详情: {traceback.format_exc()}")
                
                # 提供详细的解决建议
                logger.error("=" * 60)
                logger.error("Poppler配置建议:")
                if not Config.POPPLER_PATH:
                    logger.error("1. 如果poppler已安装但不在PATH中，请在.env文件中设置:")
                    logger.error("   POPPLER_PATH=C:\\poppler\\Library\\bin")
                    logger.error("2. 或添加到系统PATH环境变量")
                logger.error("3. Windows下载: https://github.com/oschwartz10612/poppler-windows/releases/")
                logger.error("4. 或使用: choco install poppler")
                logger.error("=" * 60)
                
                raise
            
            if not images:
                logger.warning("PDF转换为图片失败：未生成任何图片")
                return None
            
            logger.info(f"成功转换 {len(images)} 页为图片，开始OCR识别...")
            
            # 检查Tesseract是否可用
            try:
                tesseract_version = pytesseract.get_tesseract_version()
                logger.info(f"Tesseract版本: {tesseract_version}")
            except Exception as e:
                logger.error(f"Tesseract检查失败: {str(e)}")
                logger.error("请确保Tesseract已安装并在PATH中")
                return None
            
            # 检查中文语言包
            try:
                langs = pytesseract.get_languages()
                logger.info(f"可用语言包: {', '.join(langs)}")
                if 'chi_sim' not in langs:
                    logger.warning("中文语言包(chi_sim)未安装，将使用英文识别")
            except Exception as e:
                logger.warning(f"无法检查语言包: {str(e)}")
            
            # 对每页进行OCR识别
            text_content = []
            for i, image in enumerate(images):
                try:
                    logger.info(f"开始OCR识别第 {i+1}/{len(images)} 页...")
                    # 使用pytesseract进行OCR（支持中文）
                    try:
                        text = pytesseract.image_to_string(image, lang='chi_sim+eng')  # 中文简体+英文
                    except Exception as lang_error:
                        logger.warning(f"使用中文语言包失败: {str(lang_error)}，尝试仅使用英文")
                        text = pytesseract.image_to_string(image, lang='eng')
                    
                    if text.strip():
                        text_content.append(text.strip())
                        logger.info(f"第 {i+1} 页OCR识别成功，文本长度: {len(text.strip())} 字符")
                    else:
                        logger.warning(f"第 {i+1} 页OCR未识别到文本")
                except Exception as e:
                    import traceback
                    logger.error(f"第 {i+1} 页OCR识别失败: {str(e)}")
                    logger.error(f"错误详情: {traceback.format_exc()}")
                    continue
            
            if not text_content:
                logger.warning("OCR识别完成，但未提取到文本")
                return None
            
            result = "\n\n".join(text_content)
            logger.info(f"OCR识别完成，共提取 {len(text_content)} 页文本，总长度: {len(result)}")
            return result
        
        except Exception as e:
            import traceback
            logger.error(f"OCR识别过程失败: {str(e)}")
            logger.error(f"错误类型: {type(e).__name__}")
            logger.error(f"完整错误信息: {traceback.format_exc()}")
            
            # 提供具体的解决建议
            error_str = str(e).lower()
            if 'poppler' in error_str or 'pdftoppm' in error_str:
                logger.error("=" * 60)
                logger.error("poppler未正确安装或配置")
                logger.error("解决方案:")
                logger.error("1. Windows: 下载 https://github.com/oschwartz10612/poppler-windows/releases/")
                logger.error("2. 解压后添加到PATH环境变量")
                logger.error("3. 或使用: choco install poppler")
                logger.error("=" * 60)
            elif 'tesseract' in error_str:
                logger.error("=" * 60)
                logger.error("Tesseract未正确安装或配置")
                logger.error("解决方案:")
                logger.error("1. 下载安装: https://github.com/UB-Mannheim/tesseract/wiki")
                logger.error("2. 确保添加到PATH环境变量")
                logger.error("3. 安装中文语言包到tessdata目录")
                logger.error("=" * 60)
            
            return None
    
    @staticmethod
    def get_page_count(file_path: str) -> int:
        """
        获取PDF页数
        
        Args:
            file_path: PDF文件路径
            
        Returns:
            PDF页数
        """
        try:
            with pdfplumber.open(file_path) as pdf:
                return len(pdf.pages)
        except Exception as e:
            logger.error(f"获取PDF页数失败: {str(e)}")
            return 0

