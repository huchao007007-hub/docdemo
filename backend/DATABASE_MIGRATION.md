# 数据库迁移说明

## 重要提示

由于添加了用户认证功能，数据库结构发生了变化：

1. **新增了 `users` 表**
2. **`pdf_files` 表新增了 `user_id` 外键字段**

## 迁移方案

### 方案一：删除旧数据重新开始（推荐用于开发环境）

如果数据库中还没有重要数据，可以直接删除表重新创建：

```sql
-- 删除所有表（注意：这会删除所有数据）
DROP TABLE IF EXISTS summaries;
DROP TABLE IF EXISTS pdf_files;
DROP TABLE IF EXISTS users;

-- 然后重新启动后端服务，会自动创建新表
```

### 方案二：保留数据迁移（推荐用于生产环境）

如果需要保留现有数据，需要手动添加字段：

```sql
-- 1. 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. 创建一个默认管理员用户（密码：admin123，实际使用时请修改）
-- 注意：这是示例，实际密码需要手动加密
INSERT INTO users (username, password_hash) VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYQjZ5V5Q5O');

-- 3. 为pdf_files表添加user_id字段
ALTER TABLE pdf_files 
ADD COLUMN user_id INT NOT NULL DEFAULT 1 AFTER id,
ADD INDEX idx_user_id (user_id),
ADD CONSTRAINT fk_pdf_files_user FOREIGN KEY (user_id) REFERENCES users(id);

-- 4. 更新现有记录的user_id（将所有记录分配给默认用户）
UPDATE pdf_files SET user_id = 1 WHERE user_id IS NULL OR user_id = 0;

-- 5. 将user_id字段设置为NOT NULL（如果之前允许NULL）
-- ALTER TABLE pdf_files MODIFY COLUMN user_id INT NOT NULL;
```

**注意**：方案二中的默认用户密码是示例，实际使用时需要：

### 方法1：使用创建用户脚本（推荐）

```bash
cd backend
python create_user.py create admin admin123
```

### 方法2：使用Python生成密码哈希

```python
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
print(pwd_context.hash("your_password"))
```

然后将生成的哈希值插入数据库。

### 方法3：直接通过注册接口创建新用户（最简单）

访问登录页面，点击"注册"按钮，通过前端界面注册新用户。

## 自动迁移

如果使用SQLAlchemy的自动迁移功能，后端启动时会自动创建新表结构，但**不会自动添加user_id字段到现有表**。

## 验证

迁移完成后，检查：

```sql
-- 检查users表
SELECT * FROM users;

-- 检查pdf_files表结构
DESCRIBE pdf_files;

-- 检查外键约束
SHOW CREATE TABLE pdf_files;
```

## 注意事项

1. **备份数据**：在生产环境执行迁移前，务必备份数据库
2. **测试环境先验证**：先在测试环境验证迁移脚本
3. **用户创建**：如果没有用户，首次访问会提示注册

