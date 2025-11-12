#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查向量生成状态
诊断工具：检查PDF文件、向量数据、模型状态
"""

import sys
import os
import io

# 设置Windows控制台编码为UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(__file__))

from database import get_db
from models import PDFFile
from services.vector_service import VectorService
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_vectors_status():
    """检查向量生成状态"""
    
    print("=" * 60)
    print("向量生成状态诊断")
    print("=" * 60)
    
    # 1. 检查向量服务
    print("\n[1] 检查向量服务状态...")
    try:
        vector_service = VectorService()
        
        if not vector_service.qdrant_client:
            print("  [X] Qdrant客户端未初始化")
            return False
        else:
            print("  [OK] Qdrant客户端已初始化")
        
        # 导入LOCAL_EMBEDDING_AVAILABLE
        try:
            from sentence_transformers import SentenceTransformer
            LOCAL_EMBEDDING_AVAILABLE = True
        except ImportError:
            LOCAL_EMBEDDING_AVAILABLE = False
        
        # 检查模型
        if LOCAL_EMBEDDING_AVAILABLE:
            vector_service._ensure_model_loaded()
            if vector_service.local_embedder:
                print(f"  [OK] Embedding模型已加载: {Config.EMBEDDING_MODEL}")
            else:
                print(f"  [X] Embedding模型未加载")
                print(f"    请检查模型是否下载成功，或配置HF_ENDPOINT镜像源")
                return False
        else:
            print("  ✗ sentence-transformers未安装")
            return False
            
    except Exception as e:
        print(f"  ✗ 向量服务初始化失败: {str(e)}")
        return False
    
    # 2. 检查Qdrant集合
    print("\n[2] 检查Qdrant集合...")
    try:
        collection_info = vector_service.qdrant_client.get_collection(Config.QDRANT_COLLECTION_NAME)
        points_count = collection_info.points_count
        print(f"  [OK] 集合 '{Config.QDRANT_COLLECTION_NAME}' 存在")
        print(f"  - 向量点数量: {points_count}")
        print(f"  - 向量维度: {collection_info.config.params.vectors.size}")
        
        if points_count == 0:
            print("  [WARN] 集合为空，没有向量数据")
        else:
            print("  [OK] 集合中有向量数据")
    except Exception as e:
        print(f"  [X] 无法获取集合信息: {str(e)}")
        print(f"    集合可能不存在，会在首次上传时自动创建")
    
    # 3. 检查数据库中的PDF文件
    print("\n[3] 检查数据库中的PDF文件...")
    db = next(get_db())
    try:
        all_files = db.query(PDFFile).all()
        files_with_text = db.query(PDFFile).filter(
            PDFFile.text_content.isnot(None),
            PDFFile.text_content != ""
        ).all()
        
        print(f"  - 总文件数: {len(all_files)}")
        print(f"  - 有文本内容的文件: {len(files_with_text)}")
        
        if len(files_with_text) == 0:
            print("  [WARN] 没有找到有文本内容的PDF文件")
            print("    可能原因：")
            print("    1. 还没有上传PDF文件")
            print("    2. 上传的PDF都是扫描版，无法提取文本")
        else:
            print("\n  文件列表：")
            for i, file in enumerate(files_with_text[:10], 1):  # 只显示前10个
                text_len = len(file.text_content) if file.text_content else 0
                print(f"    {i}. {file.original_filename} (ID: {file.id}, 文本长度: {text_len} 字符)")
            
            if len(files_with_text) > 10:
                print(f"    ... 还有 {len(files_with_text) - 10} 个文件")
        
    except Exception as e:
        print(f"  [X] 查询数据库失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    # 4. 检查向量维度匹配
    print("\n[4] 检查向量维度配置...")
    try:
        collection_info = vector_service.qdrant_client.get_collection(Config.QDRANT_COLLECTION_NAME)
        qdrant_dimension = collection_info.config.params.vectors.size
        config_dimension = Config.EMBEDDING_DIMENSION
        
        print(f"  - 配置的维度: {config_dimension}")
        print(f"  - Qdrant集合维度: {qdrant_dimension}")
        
        if qdrant_dimension != config_dimension:
            print(f"  [WARN] 维度不匹配！")
            print(f"    需要删除旧集合并重新生成向量")
            print(f"    执行: python regenerate_vectors.py")
        else:
            print(f"  [OK] 维度匹配")
    except Exception as e:
        print(f"  [WARN] 无法检查维度（集合可能不存在）: {str(e)}")
    
    # 5. 测试向量生成
    print("\n[5] 测试向量生成...")
    try:
        test_text = "测试文本"
        embedding = vector_service._generate_embedding(test_text)
        if embedding:
            print(f"  [OK] 向量生成成功")
            print(f"  - 测试文本: '{test_text}'")
            print(f"  - 生成维度: {len(embedding)}")
            print(f"  - 配置维度: {Config.EMBEDDING_DIMENSION}")
            
            if len(embedding) != Config.EMBEDDING_DIMENSION:
                print(f"  [WARN] 生成的向量维度与配置不匹配！")
                print(f"    需要更新 EMBEDDING_DIMENSION 配置")
        else:
            print(f"  [X] 向量生成失败")
    except Exception as e:
        print(f"  ✗ 向量生成测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # 6. 总结和建议
    print("\n" + "=" * 60)
    print("诊断总结")
    print("=" * 60)
    
    try:
        collection_info = vector_service.qdrant_client.get_collection(Config.QDRANT_COLLECTION_NAME)
        points_count = collection_info.points_count
        
        if points_count == 0:
            print("\n[WARN] 问题：Qdrant集合为空")
            print("\n解决方案：")
            print("1. 如果有已上传的PDF文件，运行重新生成向量脚本：")
            print("   python regenerate_vectors.py")
            print("\n2. 或者重新上传PDF文件（会自动生成向量）")
            print("\n3. 确保上传的PDF有文本内容（不是纯扫描版）")
        else:
            print(f"\n[OK] Qdrant集合中有 {points_count} 个向量点")
            print("  如果搜索不到结果，可能原因：")
            print("  1. 相似度阈值太高（当前前端使用0.3）")
            print("  2. 查询词与文档内容不相关")
            print("  3. 用户ID过滤问题")
    except:
        pass
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    # 导入LOCAL_EMBEDDING_AVAILABLE
    try:
        from sentence_transformers import SentenceTransformer
        LOCAL_EMBEDDING_AVAILABLE = True
    except ImportError:
        LOCAL_EMBEDDING_AVAILABLE = False
    
    check_vectors_status()

