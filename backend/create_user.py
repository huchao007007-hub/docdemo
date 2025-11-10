"""
创建用户脚本
用于在数据库中创建初始用户或生成密码哈希
"""
import sys
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User
from utils.auth import get_password_hash, verify_password
from services.auth_service import AuthService

def create_user(username: str, password: str, email: str = None):
    """创建用户"""
    db = SessionLocal()
    try:
        # 检查用户是否已存在
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            print(f"❌ 用户 '{username}' 已存在")
            return False
        
        # 创建新用户
        auth_service = AuthService()
        user = auth_service.register_user(db, username, password, email)
        
        if user:
            print(f"✅ 用户 '{username}' 创建成功！")
            print(f"   用户ID: {user.id}")
            print(f"   用户名: {user.username}")
            if user.email:
                print(f"   邮箱: {user.email}")
            return True
        else:
            print(f"❌ 用户创建失败")
            return False
    
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return False
    finally:
        db.close()

def generate_password_hash(password: str):
    """生成密码哈希"""
    hash_value = get_password_hash(password)
    print(f"密码: {password}")
    print(f"哈希值: {hash_value}")
    print(f"\nSQL插入语句（用于手动插入用户）:")
    print(f"INSERT INTO users (username, password_hash) VALUES ('username', '{hash_value}');")
    return hash_value

def verify_password_hash(password: str, hash_value: str):
    """验证密码哈希"""
    is_valid = verify_password(password, hash_value)
    if is_valid:
        print(f"✅ 密码验证成功")
    else:
        print(f"❌ 密码验证失败")
    return is_valid

def list_users():
    """列出所有用户"""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        if not users:
            print("📭 数据库中没有用户")
            return
        
        print(f"📋 用户列表（共 {len(users)} 个）:")
        print("-" * 60)
        for user in users:
            print(f"ID: {user.id}")
            print(f"用户名: {user.username}")
            print(f"邮箱: {user.email or '(无)'}")
            print(f"激活: {'是' if user.is_active else '否'}")
            print(f"创建时间: {user.created_at}")
            print("-" * 60)
    
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
    finally:
        db.close()

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("=" * 60)
        print("用户管理工具")
        print("=" * 60)
        print("\n用法:")
        print("  python create_user.py create <用户名> <密码> [邮箱]")
        print("    - 创建新用户")
        print("  python create_user.py hash <密码>")
        print("    - 生成密码哈希值")
        print("  python create_user.py verify <密码> <哈希值>")
        print("    - 验证密码哈希")
        print("  python create_user.py list")
        print("    - 列出所有用户")
        print("\n示例:")
        print("  python create_user.py create admin admin123")
        print("  python create_user.py hash admin123")
        print("  python create_user.py list")
        return
    
    command = sys.argv[1].lower()
    
    if command == "create":
        if len(sys.argv) < 4:
            print("❌ 参数不足")
            print("用法: python create_user.py create <用户名> <密码> [邮箱]")
            return
        username = sys.argv[2]
        password = sys.argv[3]
        email = sys.argv[4] if len(sys.argv) > 4 else None
        create_user(username, password, email)
    
    elif command == "hash":
        if len(sys.argv) < 3:
            print("❌ 参数不足")
            print("用法: python create_user.py hash <密码>")
            return
        password = sys.argv[2]
        generate_password_hash(password)
    
    elif command == "verify":
        if len(sys.argv) < 4:
            print("❌ 参数不足")
            print("用法: python create_user.py verify <密码> <哈希值>")
            return
        password = sys.argv[2]
        hash_value = sys.argv[3]
        verify_password_hash(password, hash_value)
    
    elif command == "list":
        list_users()
    
    else:
        print(f"❌ 未知命令: {command}")

if __name__ == "__main__":
    main()

