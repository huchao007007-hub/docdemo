#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复向量维度问题
1. 删除旧的Qdrant集合（如果维度不匹配）
2. 更新配置
3. 重新生成所有向量
"""

import sys
import os
import io

# 设置Windows控制台编码为UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(__file__))

from qdrant_client import QdrantClient
from database import get_db
from models import PDFFile
from services.vector_service import VectorService
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_vectors():
    """修复向量维度问题"""
    
    print("=" * 60)
    print("向量维度修复工具")
    print("=" * 60)
    
    # 1. 检查配置
    print("\n[1] 检查配置...")
    print(f"  - Embedding模型: {Config.EMBEDDING_MODEL}")
    print(f"  - 配置维度: {Config.EMBEDDING_DIMENSION}")
    print(f"  - Qdrant地址: {Config.QDRANT_HOST}:{Config.QDRANT_PORT}")
    print(f"  - 集合名称: {Config.QDRANT_COLLECTION_NAME}")
    
    # 2. 检查Qdrant集合
    print("\n[2] 检查Qdrant集合...")
    qdrant_client = QdrantClient(
        host=Config.QDRANT_HOST,
        port=Config.QDRANT_PORT,
        timeout=Config.QDRANT_TIMEOUT
    )
    
    try:
        collection_info = qdrant_client.get_collection(Config.QDRANT_COLLECTION_NAME)
        qdrant_dimension = collection_info.config.params.vectors.size
        points_count = collection_info.points_count
        
        print(f"  - 集合存在")
        print(f"  - 当前维度: {qdrant_dimension}")
        print(f"  - 向量点数量: {points_count}")
        print(f"  - 配置维度: {Config.EMBEDDING_DIMENSION}")
        
        if qdrant_dimension != Config.EMBEDDING_DIMENSION:
            print(f"\n  [WARN] 维度不匹配！")
            print(f"    需要删除旧集合并重新创建")
            
            # 询问是否删除
            response = input("\n  是否删除旧集合并重新创建？(y/n): ").strip().lower()
            if response == 'y':
                print("\n  正在删除旧集合...")
                qdrant_client.delete_collection(Config.QDRANT_COLLECTION_NAME)
                print("  [OK] 旧集合已删除")
            else:
                print("  已取消操作")
                return False
        else:
            print(f"  [OK] 维度匹配")
            
            if points_count == 0:
                print(f"  [WARN] 集合为空，需要生成向量")
            else:
                response = input(f"\n  集合中已有 {points_count} 个向量点，是否重新生成？(y/n): ").strip().lower()
                if response != 'y':
                    print("  已取消操作")
                    return False
                # 删除集合以重新创建
                print("\n  正在删除旧集合...")
                qdrant_client.delete_collection(Config.QDRANT_COLLECTION_NAME)
                print("  [OK] 旧集合已删除")
                
    except Exception as e:
        print(f"  [INFO] 集合不存在或无法访问: {str(e)}")
        print("  将在生成向量时自动创建")
    
    # 3. 检查数据库中的PDF文件
    print("\n[3] 检查数据库中的PDF文件...")
    db = next(get_db())
    try:
        files_with_text = db.query(PDFFile).filter(
            PDFFile.text_content.isnot(None),
            PDFFile.text_content != ""
        ).all()
        
        print(f"  - 有文本内容的文件: {len(files_with_text)}")
        
        if len(files_with_text) == 0:
            print("  [WARN] 没有找到需要生成向量的PDF文件")
            print("  请先上传PDF文件")
            return False
        
        print("\n  文件列表：")
        for i, file in enumerate(files_with_text, 1):
            text_len = len(file.text_content) if file.text_content else 0
            print(f"    {i}. {file.original_filename} (ID: {file.id}, 文本长度: {text_len} 字符)")
        
    except Exception as e:
        print(f"  [X] 查询数据库失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()
    
    # 4. 初始化向量服务
    print("\n[4] 初始化向量服务...")
    try:
        vector_service = VectorService()
        
        if not vector_service.qdrant_client:
            print("  [X] Qdrant客户端未初始化")
            return False
        
        # 确保模型已加载
        try:
            from sentence_transformers import SentenceTransformer
            LOCAL_EMBEDDING_AVAILABLE = True
        except ImportError:
            LOCAL_EMBEDDING_AVAILABLE = False
        
        if LOCAL_EMBEDDING_AVAILABLE:
            vector_service._ensure_model_loaded()
            if vector_service.local_embedder:
                print(f"  [OK] Embedding模型已加载: {Config.EMBEDDING_MODEL}")
            else:
                print(f"  [X] Embedding模型未加载")
                return False
        else:
            print(f"  [X] sentence-transformers未安装")
            return False
            
    except Exception as e:
        print(f"  [X] 向量服务初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
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
                print(f"  [X] 生成的向量维度与配置不匹配！")
                print(f"    请检查 .env 文件中的 EMBEDDING_DIMENSION 配置")
                return False
        else:
            print(f"  [X] 向量生成失败")
            return False
    except Exception as e:
        print(f"  [X] 向量生成测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # 6. 重新生成向量
    print("\n[6] 开始重新生成向量...")
    print("=" * 60)
    
    db = next(get_db())
    try:
        success_count = 0
        fail_count = 0
        
        for i, pdf_file in enumerate(files_with_text, 1):
            try:
                print(f"\n[{i}/{len(files_with_text)}] 处理文件: {pdf_file.original_filename} (ID: {pdf_file.id})")
                
                # 删除旧向量（如果存在）
                try:
                    vector_service.delete_document(pdf_file.id, pdf_file.user_id)
                    print("  - 已删除旧向量")
                except Exception as e:
                    print(f"  - 删除旧向量失败（可能不存在）: {str(e)}")
                
                # 生成新向量
                if vector_service.add_document(
                    pdf_file_id=pdf_file.id,
                    user_id=pdf_file.user_id,
                    filename=pdf_file.original_filename,
                    text_content=pdf_file.text_content
                ):
                    success_count += 1
                    print(f"  [OK] 向量生成成功")
                else:
                    fail_count += 1
                    print(f"  [X] 向量生成失败")
                    
            except Exception as e:
                fail_count += 1
                print(f"  [X] 处理失败: {str(e)}")
                import traceback
                traceback.print_exc()
        
        print("\n" + "=" * 60)
        print("向量生成完成")
        print("=" * 60)
        print(f"  总文件数: {len(files_with_text)}")
        print(f"  成功: {success_count}")
        print(f"  失败: {fail_count}")
        print("=" * 60)
        
        # 验证结果
        try:
            collection_info = qdrant_client.get_collection(Config.QDRANT_COLLECTION_NAME)
            print(f"\n验证结果:")
            print(f"  - 集合维度: {collection_info.config.params.vectors.size}")
            print(f"  - 向量点数量: {collection_info.points_count}")
            
            if collection_info.points_count > 0:
                print(f"\n[OK] 向量生成成功！现在可以正常搜索了。")
            else:
                print(f"\n[WARN] 集合中仍然没有向量点，请检查错误日志")
        except Exception as e:
            print(f"\n[WARN] 无法验证结果: {str(e)}")
        
        return fail_count == 0
        
    except Exception as e:
        print(f"\n[X] 重新生成向量失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    try:
        fix_vectors()
    except KeyboardInterrupt:
        print("\n\n操作已取消")
    except Exception as e:
        print(f"\n[X] 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

