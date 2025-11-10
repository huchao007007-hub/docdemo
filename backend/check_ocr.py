"""
OCR环境检查脚本
用于检查OCR相关依赖是否正确安装
"""
import sys
import os

def check_python_packages():
    """检查Python包"""
    print("=" * 60)
    print("检查Python包...")
    print("=" * 60)
    
    packages = {
        'pytesseract': 'pytesseract',
        'pdf2image': 'pdf2image',
        'PIL': 'Pillow'
    }
    
    all_ok = True
    for name, package in packages.items():
        try:
            __import__(name)
            print(f"[OK] {package} 已安装")
        except ImportError:
            print(f"[FAIL] {package} 未安装")
            print(f"   安装命令: pip install {package}")
            all_ok = False
    
    return all_ok

def check_tesseract():
    """检查Tesseract OCR"""
    print("\n" + "=" * 60)
    print("检查Tesseract OCR...")
    print("=" * 60)
    
    try:
        import pytesseract
        try:
            version = pytesseract.get_tesseract_version()
            print(f"[OK] Tesseract已安装，版本: {version}")
        except Exception as e:
            print(f"[FAIL] Tesseract未找到: {str(e)}")
            print("   请确保Tesseract已安装并在PATH中")
            print("   下载: https://github.com/UB-Mannheim/tesseract/wiki")
            return False
        
        # 检查语言包
        try:
            langs = pytesseract.get_languages()
            print(f"[OK] 可用语言包: {', '.join(langs)}")
            if 'chi_sim' in langs:
                print("[OK] 中文语言包已安装")
            else:
                print("[WARN] 中文语言包未安装")
                print("   下载: https://github.com/tesseract-ocr/tessdata/blob/main/chi_sim.traineddata")
                print("   放到: Tesseract安装目录/tessdata/")
        except Exception as e:
            print(f"[WARN] 无法检查语言包: {str(e)}")
        
        return True
    except ImportError:
        print("[FAIL] pytesseract未安装")
        return False

def check_poppler():
    """检查poppler"""
    print("\n" + "=" * 60)
    print("检查Poppler (PDF转图片工具)...")
    print("=" * 60)
    
    import subprocess
    
    try:
        # 检查pdftoppm命令
        result = subprocess.run(
            ['pdftoppm', '-v'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 or 'pdftoppm' in result.stderr.lower():
            print("[OK] poppler已安装并在PATH中")
            print(f"   输出: {result.stderr[:100]}")
            return True
        else:
            print("[FAIL] poppler未正确安装")
            return False
    except FileNotFoundError:
        print("[FAIL] poppler未安装或不在PATH中")
        print("   Windows下载: https://github.com/oschwartz10612/poppler-windows/releases/")
        print("   或使用: choco install poppler")
        print("   安装后需要添加到PATH环境变量")
        return False
    except Exception as e:
        print(f"[WARN] 检查poppler时出错: {str(e)}")
        return False

def check_pdf2image():
    """检查pdf2image配置"""
    print("\n" + "=" * 60)
    print("检查pdf2image配置...")
    print("=" * 60)
    
    try:
        from pdf2image import convert_from_path
        print("[OK] pdf2image可以导入")
        
        # 尝试检查poppler路径配置
        try:
            from pdf2image import pdf2image
            poppler_path = getattr(pdf2image, 'poppler_path', None)
            if poppler_path:
                print(f"[OK] poppler路径已配置: {poppler_path}")
            else:
                print("[WARN] poppler路径未配置，将使用PATH中的poppler")
        except:
            pass
        
        return True
    except ImportError:
        print("[FAIL] pdf2image未安装")
        return False

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("OCR环境检查工具")
    print("=" * 60 + "\n")
    
    results = {
        'Python包': check_python_packages(),
        'Tesseract': check_tesseract(),
        'Poppler': check_poppler(),
        'pdf2image': check_pdf2image()
    }
    
    print("\n" + "=" * 60)
    print("检查结果汇总")
    print("=" * 60)
    
    all_ok = True
    for name, result in results.items():
        status = "[OK] 通过" if result else "[FAIL] 失败"
        print(f"{name}: {status}")
        if not result:
            all_ok = False
    
    print("\n" + "=" * 60)
    if all_ok:
        print("[OK] 所有检查通过，OCR功能应该可以正常使用！")
    else:
        print("[FAIL] 部分检查失败，请根据上述提示安装缺失的组件")
    print("=" * 60)

if __name__ == "__main__":
    main()

