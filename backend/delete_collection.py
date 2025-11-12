#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
删除旧的Qdrant集合
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
from config import Config

def delete_collection():
    """删除旧的Qdrant集合"""
    
    print("=" * 60)
    print("删除旧的Qdrant集合")
    print("=" * 60)
    
    print(f"\n配置信息:")
    print(f"  - Qdrant地址: {Config.QDRANT_HOST}:{Config.QDRANT_PORT}")
    print(f"  - 集合名称: {Config.QDRANT_COLLECTION_NAME}")
    
    # 连接Qdrant
    print(f"\n[1] 连接Qdrant...")
    try:
        client = QdrantClient(
            host=Config.QDRANT_HOST,
            port=Config.QDRANT_PORT,
            timeout=Config.QDRANT_TIMEOUT
        )
        print("  [OK] 连接成功")
    except Exception as e:
        print(f"  [X] 连接失败: {str(e)}")
        return False
    
    # 检查集合是否存在
    print(f"\n[2] 检查集合...")
    try:
        collection_info = client.get_collection(Config.QDRANT_COLLECTION_NAME)
        points_count = collection_info.points_count
        dimension = collection_info.config.params.vectors.size
        
        print(f"  - 集合存在")
        print(f"  - 当前维度: {dimension}")
        print(f"  - 向量点数量: {points_count}")
        print(f"  - 配置维度: {Config.EMBEDDING_DIMENSION}")
        
        if dimension != Config.EMBEDDING_DIMENSION:
            print(f"\n  [WARN] 维度不匹配！需要删除旧集合")
        else:
            print(f"\n  [INFO] 维度匹配，但需要重新生成向量")
        
    except Exception as e:
        print(f"  [INFO] 集合不存在或无法访问: {str(e)}")
        print("  将在生成向量时自动创建")
        return True
    
    # 删除集合
    print(f"\n[3] 删除集合...")
    try:
        client.delete_collection(Config.QDRANT_COLLECTION_NAME)
        print(f"  [OK] 集合已删除")
        return True
    except Exception as e:
        print(f"  [X] 删除失败: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        delete_collection()
        print("\n" + "=" * 60)
        print("下一步：运行 python regenerate_vectors.py 重新生成向量")
        print("=" * 60)
    except Exception as e:
        print(f"\n[X] 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

