#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
更新.env文件，确保EMBEDDING_DIMENSION=768
"""

import os
import sys

def update_env_file():
    """更新.env文件"""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    
    print("=" * 60)
    print("更新.env文件配置")
    print("=" * 60)
    
    # 读取现有配置
    env_vars = {}
    if os.path.exists(env_path):
        print(f"\n[INFO] 找到.env文件: {env_path}")
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
        print(f"  已读取 {len(env_vars)} 个配置项")
    else:
        print(f"\n[INFO] .env文件不存在，将创建新文件")
    
    # 更新配置
    print("\n[1] 更新配置...")
    
    # 必需的配置
    required_configs = {
        'DEEPSEEK_API_KEY': 'sk-e79c5ddba7324e58bbffa901ea368756',
        'DEEPSEEK_BASE_URL': 'https://api.deepseek.com/v1',
        'EMBEDDING_MODEL': 'shibing624/text2vec-base-chinese',
        'EMBEDDING_DIMENSION': '768',  # 关键：更新为768
        'QDRANT_HOST': '118.89.121.9',
        'QDRANT_PORT': '6333',
        'QDRANT_COLLECTION_NAME': 'pdf_summary_vectors',
    }
    
    updated = False
    for key, value in required_configs.items():
        if key not in env_vars or env_vars[key] != value:
            old_value = env_vars.get(key, '未设置')
            env_vars[key] = value
            print(f"  - {key}: {old_value} -> {value}")
            updated = True
        else:
            print(f"  - {key}: {value} (已正确)")
    
    # 保留其他配置（如DATABASE_URL等）
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key = line.split('=', 1)[0].strip()
                    if key not in required_configs:
                        # 保留非必需配置
                        if key not in env_vars:
                            env_vars[key] = line.split('=', 1)[1].strip()
    
    if not updated:
        print("\n[OK] 所有配置已正确，无需更新")
        return True
    
    # 写入文件
    print("\n[2] 写入.env文件...")
    try:
        with open(env_path, 'w', encoding='utf-8') as f:
            # 写入必需配置
            f.write("# DeepSeek API配置\n")
            f.write(f"DEEPSEEK_API_KEY={env_vars['DEEPSEEK_API_KEY']}\n")
            f.write(f"DEEPSEEK_BASE_URL={env_vars['DEEPSEEK_BASE_URL']}\n")
            f.write("\n")
            
            # 写入数据库配置（如果存在）
            if 'DATABASE_URL' in env_vars:
                f.write("# 数据库配置\n")
                f.write(f"DATABASE_URL={env_vars['DATABASE_URL']}\n")
                f.write("\n")
            else:
                f.write("# 数据库配置（需要修改）\n")
                f.write("# DATABASE_URL=mysql+pymysql://root:password@localhost:3306/pdf_summary?charset=utf8mb4\n")
                f.write("\n")
            
            # 写入Qdrant配置
            f.write("# Qdrant向量数据库配置\n")
            f.write(f"QDRANT_HOST={env_vars['QDRANT_HOST']}\n")
            f.write(f"QDRANT_PORT={env_vars['QDRANT_PORT']}\n")
            f.write(f"QDRANT_COLLECTION_NAME={env_vars['QDRANT_COLLECTION_NAME']}\n")
            f.write("\n")
            
            # 写入Embedding模型配置
            f.write("# Embedding模型配置\n")
            f.write(f"EMBEDDING_MODEL={env_vars['EMBEDDING_MODEL']}\n")
            f.write(f"EMBEDDING_DIMENSION={env_vars['EMBEDDING_DIMENSION']}\n")
            f.write("\n")
            
            # 写入其他配置
            other_keys = [k for k in env_vars.keys() if k not in required_configs and k != 'DATABASE_URL']
            if other_keys:
                f.write("# 其他配置\n")
                for key in other_keys:
                    f.write(f"{key}={env_vars[key]}\n")
        
        print(f"  [OK] .env文件已更新: {env_path}")
        print(f"\n[OK] 配置更新完成！")
        print(f"\n重要：EMBEDDING_DIMENSION 已设置为 768")
        print(f"      请重启后端服务以使配置生效")
        return True
        
    except Exception as e:
        print(f"  [X] 写入失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        update_env_file()
    except Exception as e:
        print(f"\n[X] 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

