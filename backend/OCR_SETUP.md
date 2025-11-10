# OCR识别功能设置说明

## 功能说明

系统已集成OCR识别功能，可以识别扫描版PDF（图片型PDF）中的文本。

## 安装步骤

### Windows系统

1. **安装Tesseract OCR**

   - 下载安装包：https://github.com/UB-Mannheim/tesseract/wiki
   - 或使用 Chocolatey: `choco install tesseract`
   - 或使用 scoop: `scoop install tesseract`

2. **安装中文语言包**

   - 下载中文简体语言包：https://github.com/tesseract-ocr/tessdata/blob/main/chi_sim.traineddata
   - 将文件放到Tesseract安装目录的 `tessdata` 文件夹中
   - 默认路径：`C:\Program Files\Tesseract-OCR\tessdata\`

3. **配置环境变量（如果自动配置失败）**

   - 添加 `TESSDATA_PREFIX` 环境变量，值为 `C:\Program Files\Tesseract-OCR\tessdata`
   - 或将Tesseract添加到PATH：`C:\Program Files\Tesseract-OCR`

4. **安装Python依赖**

   ```bash
   cd backend
   .\venv\Scripts\Activate.ps1
   pip install pytesseract pdf2image Pillow
   ```

5. **安装poppler（PDF转图片工具）**

   - 下载：https://github.com/oschwartz10612/poppler-windows/releases/
   - 解压到某个目录（如 `C:\poppler`）
   - 添加到PATH环境变量

### Linux系统

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim poppler-utils

# CentOS/RHEL
sudo yum install tesseract tesseract-langpack-chi_sim poppler-utils

# 安装Python依赖
pip install pytesseract pdf2image Pillow
```

### Mac系统

```bash
# 使用Homebrew
brew install tesseract tesseract-lang poppler

# 安装Python依赖
pip install pytesseract pdf2image Pillow
```

## 验证安装

运行以下命令验证：

```bash
# 检查Tesseract是否安装
tesseract --version

# 检查中文语言包
tesseract --list-langs
# 应该看到 chi_sim

# 测试Python导入
python -c "import pytesseract; print('OCR可用')"
```

## 使用说明

1. **自动OCR**：上传PDF时，如果无法提取文本，系统会自动尝试OCR识别
2. **OCR识别速度**：OCR识别比普通文本提取慢，大文件可能需要较长时间
3. **识别质量**：OCR识别质量取决于PDF图片的清晰度

## 注意事项

- OCR识别需要较长时间，特别是多页PDF
- 如果OCR库未安装，系统会正常上传PDF，但无法提取文本
- OCR识别需要额外的系统资源（CPU和内存）

## 故障排除

### 错误：`pytesseract.pytesseract.TesseractNotFoundError`

**解决方案**：
1. 确认Tesseract已安装
2. 如果Tesseract不在PATH中，需要设置环境变量或配置路径

### 错误：`pdf2image.exceptions.PDFInfoNotInstalledError`

**解决方案**：
1. Windows：安装poppler并添加到PATH
2. Linux：安装 `poppler-utils`
3. Mac：安装 `poppler`

### OCR识别结果为空

**可能原因**：
1. PDF图片质量太差
2. 图片是照片而非扫描件
3. 语言包未正确安装

