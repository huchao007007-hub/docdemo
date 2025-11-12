from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from openai import OpenAI
from config import Config
from typing import List, Optional, Dict, Any
import logging
import uuid
import os

logger = logging.getLogger(__name__)

# 重要：在导入 sentence_transformers 之前设置 HF_ENDPOINT 环境变量
# 这样 huggingface_hub 才能正确使用镜像源
if Config.HF_ENDPOINT:
    os.environ['HF_ENDPOINT'] = Config.HF_ENDPOINT
    logger.info(f"设置HuggingFace镜像源: {Config.HF_ENDPOINT}")

# 尝试导入本地embedding模型（可选）
try:
    from sentence_transformers import SentenceTransformer
    LOCAL_EMBEDDING_AVAILABLE = True
except ImportError:
    LOCAL_EMBEDDING_AVAILABLE = False
    logger.info("sentence-transformers未安装，将尝试使用DeepSeek API生成向量")

class VectorService:
    """向量服务，用于语义搜索"""
    
    def __init__(self):
        """初始化向量服务"""
        try:
            # 初始化 Qdrant 客户端（添加超时配置）
            self.qdrant_client = QdrantClient(
                host=Config.QDRANT_HOST,
                port=Config.QDRANT_PORT,
                timeout=Config.QDRANT_TIMEOUT
            )
            # 测试连接
            try:
                self.qdrant_client.get_collections()
                logger.info(f"Qdrant客户端连接成功: {Config.QDRANT_HOST}:{Config.QDRANT_PORT}")
            except Exception as test_error:
                logger.warning(f"Qdrant连接测试失败: {str(test_error)}，但客户端已创建")
                logger.warning("提示：请检查Qdrant服务是否运行，或网络连接是否正常")
        except Exception as e:
            logger.error(f"Qdrant客户端连接失败: {str(e)}")
            logger.error("提示：请检查Qdrant服务是否运行在正确的地址和端口")
            self.qdrant_client = None
        
        # 初始化 DeepSeek Embeddings 客户端
        try:
            self.embeddings_client = OpenAI(
                api_key=Config.DEEPSEEK_API_KEY,
                base_url=Config.DEEPSEEK_BASE_URL
            )
            logger.info("DeepSeek Embeddings客户端初始化成功")
        except Exception as e:
            logger.error(f"DeepSeek Embeddings客户端初始化失败: {str(e)}")
            self.embeddings_client = None
        
        # 不在这里加载模型，改为延迟加载（避免阻塞服务启动）
        self.local_embedder = None
        self._model_loading = False  # 标记是否正在加载模型
        
        # 确保集合存在
        self._ensure_collection()
    
    def _ensure_collection(self):
        """确保Qdrant集合存在"""
        if not self.qdrant_client:
            return
        
        try:
            collection_name = Config.QDRANT_COLLECTION_NAME
            if not self.qdrant_client.collection_exists(collection_name):
                self.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=Config.EMBEDDING_DIMENSION,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"创建Qdrant集合: {collection_name}")
            else:
                logger.info(f"Qdrant集合已存在: {collection_name}")
        except Exception as e:
            logger.error(f"确保集合存在失败: {str(e)}")
    
    def _split_text(self, text: str) -> List[str]:
        """
        将文本分块，用于长文本处理
        优化：按段落和句子分块，保持语义完整
        
        Args:
            text: 原始文本
            
        Returns:
            文本块列表
        """
        if not text:
            return []
        
        import re
        
        chunks = []
        chunk_size = Config.TEXT_CHUNK_SIZE
        overlap = Config.TEXT_CHUNK_OVERLAP
        
        # 首先按段落分割（双换行、段落标记等）
        # 支持多种段落分隔符
        paragraph_separators = ['\n\n', '\r\n\r\n', '\n\r\n\r']
        paragraphs = [text]
        
        for sep in paragraph_separators:
            new_paragraphs = []
            for para in paragraphs:
                new_paragraphs.extend(para.split(sep))
            paragraphs = new_paragraphs
        
        # 处理每个段落
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # 如果段落长度在合理范围内，直接作为一个块
            if len(para) <= chunk_size:
                chunks.append(para)
            else:
                # 段落太长，按句子分割
                # 支持中文和英文句子结束符
                sentence_endings = r'[。！？\n]|\.\s+|!\s+|\?\s+'
                sentences = re.split(sentence_endings, para)
                
                current_chunk = ""
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    
                    # 如果当前块加上新句子不超过限制，添加到当前块
                    if len(current_chunk) + len(sentence) + 1 <= chunk_size:
                        if current_chunk:
                            current_chunk += " " + sentence
                        else:
                            current_chunk = sentence
                    else:
                        # 当前块已满，保存并开始新块
                        if current_chunk:
                            chunks.append(current_chunk)
                        
                        # 如果单个句子就超过限制，需要强制分割
                        if len(sentence) > chunk_size:
                            # 按字符数强制分割，但尽量在标点处分割
                            start = 0
                            while start < len(sentence):
                                end = start + chunk_size
                                if end < len(sentence):
                                    # 尝试在标点符号处分割
                                    punctuation = ['，', ',', '；', ';', '、', '：', ':']
                                    best_split = end
                                    for punct in punctuation:
                                        last_punct = sentence.rfind(punct, start, end)
                                        if last_punct > start:
                                            best_split = last_punct + 1
                                            break
                                    
                                    chunk = sentence[start:best_split]
                                    if chunk:
                                        chunks.append(chunk)
                                    start = best_split
                                else:
                                    chunk = sentence[start:]
                                    if chunk:
                                        chunks.append(chunk)
                                    break
                            current_chunk = ""
                        else:
                            current_chunk = sentence
                
                # 添加最后一个块
                if current_chunk:
                    chunks.append(current_chunk)
        
        # 如果没有分到任何块（可能是没有段落分隔符），使用原来的方法
        if not chunks:
            start = 0
            while start < len(text):
                end = start + chunk_size
                chunk = text[start:end]
                chunks.append(chunk)
                
                # 如果有重叠，下次从重叠位置开始
                if end < len(text):
                    start = end - overlap
                else:
                    break
        
        # 过滤空块和过短的块（除非是最后一个）
        filtered_chunks = []
        for i, chunk in enumerate(chunks):
            chunk = chunk.strip()
            if chunk and len(chunk) > 10:  # 至少10个字符
                filtered_chunks.append(chunk)
            elif chunk and i == len(chunks) - 1:  # 最后一个块即使短也保留
                filtered_chunks.append(chunk)
        
        return filtered_chunks if filtered_chunks else chunks
    
    def _ensure_model_loaded(self):
        """确保模型已加载（延迟加载，避免阻塞服务启动）"""
        if self.local_embedder is not None:
            return True
        
        if self._model_loading:
            # 如果正在加载，等待一下
            import time
            time.sleep(0.1)
            return self.local_embedder is not None
        
        if not LOCAL_EMBEDDING_AVAILABLE:
            return False
        
        self._model_loading = True
        try:
            logger.info("开始加载本地embedding模型（首次使用时加载）...")
            
            # 确保环境变量已设置（已在文件顶部设置，这里再次确认）
            if Config.HF_ENDPOINT and 'HF_ENDPOINT' not in os.environ:
                os.environ['HF_ENDPOINT'] = Config.HF_ENDPOINT
                logger.info(f"使用HuggingFace镜像源: {Config.HF_ENDPOINT}")
            
            # 使用配置的embedding模型（默认使用中文优化模型）
            model_name = Config.EMBEDDING_MODEL
            logger.info(f"加载embedding模型: {model_name}")
            logger.info(f"当前HF_ENDPOINT环境变量: {os.environ.get('HF_ENDPOINT', '未设置')}")
            self.local_embedder = SentenceTransformer(model_name)
            logger.info(f"本地embedding模型加载成功: {model_name}")
            return True
        except Exception as e:
            logger.warning(f"本地embedding模型加载失败: {str(e)}")
            logger.warning("提示：如果网络无法访问huggingface.co，可以：")
            logger.warning("1. 在.env文件中设置HF_ENDPOINT=https://hf-mirror.com（推荐）")
            logger.warning("2. 使用代理或VPN")
            logger.warning("3. 手动下载模型到本地缓存目录")
            logger.warning("4. 使用DeepSeek Embeddings API（如果支持）")
            self.local_embedder = None
            return False
        finally:
            self._model_loading = False
    
    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        生成文本向量
        
        优先级：
        1. 本地sentence-transformers模型（如果可用，推荐）
        2. DeepSeek embeddings API（如果支持）
        3. 其他embedding服务
        
        Args:
            text: 要生成向量的文本
            
        Returns:
            向量列表，如果失败返回None
        """
        if not text:
            return None
        
        # 延迟加载模型（首次使用时才加载，避免阻塞服务启动）
        if LOCAL_EMBEDDING_AVAILABLE:
            self._ensure_model_loaded()
        
        # 方法1：使用本地embedding模型（推荐，免费且稳定）
        if self.local_embedder:
            try:
                embedding = self.local_embedder.encode(text, convert_to_numpy=True)
                # sentence-transformers通常返回384维，需要调整维度或使用适配层
                embedding_list = embedding.tolist()
                logger.debug(f"使用本地embedding模型生成向量成功，维度: {len(embedding_list)}")
                # 注意：如果维度不匹配，需要调整Qdrant集合的配置
                return embedding_list
            except Exception as e:
                logger.warning(f"本地embedding生成失败: {str(e)}")
        
        # 方法2：尝试使用DeepSeek的embeddings接口
        if self.embeddings_client:
            try:
                response = self.embeddings_client.embeddings.create(
                    model="text-embedding-3-small",  # 尝试标准模型名
                    input=text
                )
                
                if response and response.data:
                    embedding = response.data[0].embedding
                    logger.debug(f"使用DeepSeek embeddings接口生成向量成功，维度: {len(embedding)}")
                    return embedding
            except Exception as e1:
                logger.debug(f"DeepSeek embeddings接口不可用: {str(e1)}")
        
        # 如果都失败，记录警告
        logger.warning("无法生成向量，建议安装sentence-transformers或配置其他embedding服务")
        return None
    
    def add_document(self, pdf_file_id: int, user_id: int, filename: str, text_content: str) -> bool:
        """
        添加文档向量到Qdrant
        
        Args:
            pdf_file_id: PDF文件ID
            user_id: 用户ID
            filename: 文件名
            text_content: 文本内容
            
        Returns:
            是否成功
        """
        if not self.qdrant_client or not text_content:
            logger.warning("Qdrant客户端未初始化或文本内容为空")
            return False
        
        try:
            # 检查模型是否可用
            if LOCAL_EMBEDDING_AVAILABLE:
                self._ensure_model_loaded()
            
            if not self.local_embedder and not self.embeddings_client:
                logger.error("无法生成向量：embedding模型和API都不可用")
                logger.error("请检查：1. 模型是否成功加载 2. DeepSeek API是否配置正确")
                return False
            
            # 1. 处理文件名（也生成向量，用于搜索文件名）
            logger.debug(f"开始为文件名生成向量: {filename}")
            filename_embedding = self._generate_embedding(filename)
            if filename_embedding:
                try:
                    filename_point_id = str(uuid.uuid4())
                    self.qdrant_client.upsert(
                        collection_name=Config.QDRANT_COLLECTION_NAME,
                        points=[
                            PointStruct(
                                id=filename_point_id,
                                vector=filename_embedding,
                                payload={
                                    "pdf_file_id": pdf_file_id,
                                    "user_id": user_id,
                                    "type": "filename",
                                    "text": filename,
                                    "original_filename": filename
                                }
                            )
                        ]
                    )
                    logger.info(f"文件名向量已添加: {filename}")
                except Exception as upsert_error:
                    logger.warning(f"添加文件名向量失败: {str(upsert_error)}")
            
            # 2. 处理文本内容（分块处理）
            logger.debug(f"开始分块处理文本内容，原始长度: {len(text_content)} 字符")
            text_chunks = self._split_text(text_content)
            logger.debug(f"文本分块完成，共 {len(text_chunks)} 个块")
            points = []
            
            for idx, chunk in enumerate(text_chunks):
                chunk_embedding = self._generate_embedding(chunk)
                if chunk_embedding:
                    point_id = str(uuid.uuid4())
                    points.append(
                        PointStruct(
                            id=point_id,
                            vector=chunk_embedding,
                            payload={
                                "pdf_file_id": pdf_file_id,
                                "user_id": user_id,
                                "type": "content",
                                "chunk_index": idx,
                                "text": chunk,
                                "original_filename": filename
                            }
                        )
                    )
            
            if points:
                try:
                    # 分批插入，避免一次性插入太多数据导致超时
                    batch_size = 50  # 每批50个点
                    for i in range(0, len(points), batch_size):
                        batch = points[i:i + batch_size]
                        self.qdrant_client.upsert(
                            collection_name=Config.QDRANT_COLLECTION_NAME,
                            points=batch
                        )
                        logger.debug(f"已插入向量批次 {i//batch_size + 1}/{(len(points) + batch_size - 1)//batch_size}")
                    
                    logger.info(f"文档向量已添加: PDF ID={pdf_file_id}, 块数={len(points)}")
                    return True
                except Exception as upsert_error:
                    logger.error(f"插入文档向量失败: {str(upsert_error)}")
                    logger.error("可能原因：Qdrant服务响应慢或网络问题")
                    return False
            else:
                logger.warning(f"未能生成任何向量: PDF ID={pdf_file_id}")
                return False
                
        except Exception as e:
            logger.error(f"添加文档向量失败: {str(e)}")
            return False
    
    def search(self, query: str, user_id: int, limit: int = 10, score_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        语义搜索
        
        Args:
            query: 搜索查询文本
            user_id: 用户ID（只搜索该用户的文档）
            limit: 返回结果数量
            score_threshold: 相似度阈值（0-1）
            
        Returns:
            搜索结果列表
        """
        if not self.qdrant_client or not query:
            return []
        
        try:
            # 生成查询向量
            logger.info(f"开始生成查询向量: '{query}'")
            query_embedding = self._generate_embedding(query)
            if not query_embedding:
                logger.warning("无法生成查询向量，可能原因：模型未加载或网络问题")
                return []
            
            logger.info(f"查询向量生成成功，维度: {len(query_embedding)}")
            
            # 先检查集合中是否有数据
            try:
                collection_info = self.qdrant_client.get_collection(Config.QDRANT_COLLECTION_NAME)
                points_count = collection_info.points_count
                logger.info(f"Qdrant集合 '{Config.QDRANT_COLLECTION_NAME}' 中共有 {points_count} 个向量点")
                
                if points_count == 0:
                    logger.warning("Qdrant集合为空，没有可搜索的数据。请先上传PDF文件并生成向量。")
                    return []
            except Exception as info_error:
                logger.warning(f"无法获取集合信息: {str(info_error)}")
            
            # 搜索（只搜索该用户的文档）
            try:
                logger.info(f"开始搜索，用户ID: {user_id}, 阈值: {score_threshold}, 限制: {limit}")
                search_results = self.qdrant_client.search(
                    collection_name=Config.QDRANT_COLLECTION_NAME,
                    query_vector=query_embedding,
                    query_filter=Filter(
                        must=[
                            FieldCondition(
                                key="user_id",
                                match=MatchValue(value=user_id)
                            )
                        ]
                    ),
                    limit=limit * 2,  # 获取更多结果，然后过滤
                    score_threshold=0.0,  # 先不设阈值，获取所有结果
                    timeout=Config.QDRANT_TIMEOUT
                )
                logger.info(f"Qdrant返回 {len(search_results)} 个原始结果")
                
                # 手动过滤相似度阈值
                filtered_results = [r for r in search_results if r.score >= score_threshold]
                logger.info(f"经过阈值 {score_threshold} 过滤后，剩余 {len(filtered_results)} 个结果")
                
                if len(filtered_results) == 0 and len(search_results) > 0:
                    logger.warning(f"所有结果都被阈值 {score_threshold} 过滤掉了。最高相似度: {max(r.score for r in search_results):.4f}")
                    logger.warning("建议：降低相似度阈值或检查查询词是否与文档内容相关")
                
                search_results = filtered_results[:limit]  # 限制返回数量
                
            except Exception as search_error:
                logger.error(f"Qdrant搜索操作失败: {str(search_error)}")
                logger.error("可能原因：Qdrant服务响应慢、网络问题或集合不存在")
                return []
            
            # 格式化结果
            results = []
            seen_files = set()  # 避免重复文件
            
            for result in search_results:
                payload = result.payload
                pdf_file_id = payload.get("pdf_file_id")
                
                # 如果已经包含该文件，跳过（只返回每个文件的最佳匹配）
                if pdf_file_id in seen_files:
                    continue
                
                seen_files.add(pdf_file_id)
                results.append({
                    "pdf_file_id": pdf_file_id,
                    "filename": payload.get("original_filename", ""),
                    "text": payload.get("text", ""),
                    "type": payload.get("type", "content"),  # filename 或 content
                    "score": result.score,  # 相似度分数
                    "chunk_index": payload.get("chunk_index")
                })
            
            logger.info(f"搜索完成: 查询='{query}', 结果数={len(results)}")
            return results
            
        except Exception as e:
            logger.error(f"搜索失败: {str(e)}")
            return []
    
    def delete_document(self, pdf_file_id: int, user_id: int) -> bool:
        """
        删除文档的所有向量
        
        Args:
            pdf_file_id: PDF文件ID
            user_id: 用户ID
            
        Returns:
            是否成功
        """
        if not self.qdrant_client:
            return False
        
        try:
            # 先搜索所有相关的点
            # 注意：Qdrant的删除需要先找到所有点ID，这里使用scroll API
            from qdrant_client.models import ScrollRequest, Filter, FieldCondition, MatchValue
            
            scroll_result = self.qdrant_client.scroll(
                collection_name=Config.QDRANT_COLLECTION_NAME,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="pdf_file_id",
                            match=MatchValue(value=pdf_file_id)
                        ),
                        FieldCondition(
                            key="user_id",
                            match=MatchValue(value=user_id)
                        )
                    ]
                ),
                limit=1000  # 假设每个文档最多1000个点
            )
            
            # 提取所有点ID
            point_ids = [point.id for point in scroll_result[0]]
            
            if point_ids:
                # 删除所有点
                self.qdrant_client.delete(
                    collection_name=Config.QDRANT_COLLECTION_NAME,
                    points_selector=point_ids
                )
                logger.info(f"删除文档向量成功: PDF ID={pdf_file_id}, 点数={len(point_ids)}")
                return True
            else:
                logger.info(f"未找到要删除的向量: PDF ID={pdf_file_id}")
                return True
                
        except Exception as e:
            logger.error(f"删除文档向量失败: {str(e)}")
            return False

