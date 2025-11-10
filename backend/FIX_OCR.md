# OCR问题修复指南

## 问题诊断

根据检查脚本的结果，你的问题是：
- ✅ Python包已安装（pytesseract, pdf2image, Pillow）
- ❌ Tesseract未在PATH中
- ❌ Poppler未在PATH中

## 解决方案

### 方案1：添加到PATH环境变量（推荐）

#### Windows添加PATH步骤：

1. **找到Tesseract安装路径**
   - 通常在：`C:\Program Files\Tesseract-OCR`
   - 或：`C:\Program Files (x86)\Tesseract-OCR`

2. **找到Poppler安装路径**
   - 如果已下载解压，通常在：`C:\poppler\Library\bin`
   - 或你解压到的其他位置

3. **添加到PATH**
   - 右键"此电脑" → "属性" → "高级系统设置" → "环境变量"
   - 在"系统变量"中找到"Path"，点击"编辑"
   - 添加两个路径：
     - `C:\Program Files\Tesseract-OCR`（Tesseract）
     - `C:\poppler\Library\bin`（Poppler的bin目录）
   - 点击"确定"保存

4. **重启终端和后端服务**

### 方案2：在.env文件中配置路径（无需修改PATH）

如果不想修改系统PATH，可以在`.env`文件中配置：

```env
# OCR配置（如果不在PATH中）
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
POPPLER_PATH=C:\poppler\Library\bin
```

**注意**：
- `TESSERACT_CMD` 是tesseract.exe的完整路径
- `POPPLER_PATH` 是poppler的bin目录路径（不是exe文件路径）

### 方案3：使用Chocolatey安装（自动配置PATH）

```powershell
# 以管理员身份运行PowerShell
choco install tesseract poppler
```

## 验证安装

运行检查脚本：

```bash
cd backend
.\venv\Scripts\Activate.ps1
python check_ocr.py
```

应该看到所有检查都通过。

## 常见问题

### Q: 如何找到Tesseract安装路径？

**A:** 运行以下命令查找：
```powershell
where.exe tesseract
```

如果找不到，说明未安装或不在PATH中。

### Q: 如何找到Poppler安装路径？

**A:** 如果你下载了解压版，检查解压目录。通常结构是：
```
poppler/
  Library/
    bin/
      pdftoppm.exe
      ...
```

### Q: 配置后还是不行？

**A:** 
1. 确保路径正确（使用完整路径）
2. 重启后端服务
3. 检查路径中是否有空格（需要用引号或转义）
4. 运行 `python check_ocr.py` 再次检查

## 快速测试

配置完成后，上传一个扫描版PDF，查看日志应该会显示：
- "poppler检查: pdftoppm可用"
- "Tesseract版本: x.x.x"
- "正在将PDF转换为图片..."
- "开始OCR识别第 1/X 页..."

