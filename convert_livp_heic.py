import os
import sys
import zipfile
from PIL import Image

def convert_livp_to_png(livp_path, output_path=None):
    try:
        with zipfile.ZipFile(livp_path, 'r') as zip_ref:
            heic_files = [f for f in zip_ref.namelist() if f.lower().endswith('.heic')]
            
            if not heic_files:
                print(f"警告: {livp_path} 中未找到HEIC文件")
                return False
            
            heic_file = heic_files[0]
            with zip_ref.open(heic_file) as heic_data:
                img = Image.open(heic_data)
                
                if output_path is None:
                    base_name = os.path.splitext(os.path.basename(livp_path))[0]
                    output_path = os.path.join(os.path.dirname(livp_path), f"{base_name}.png")
                
                img.save(output_path, 'PNG')
                print(f"转换成功: {livp_path} -> {output_path}")
                return True
    
    except zipfile.BadZipFile:
        print(f"警告: {livp_path} 不是有效的ZIP文件，尝试直接查找PNG数据")
        with open(livp_path, 'rb') as f:
            data = f.read()
        
        start_marker = b'\x89PNG\r\n\x1a\n'
        end_marker = b'IEND\xaeB`\x82'
        
        start_idx = data.find(start_marker)
        if start_idx == -1:
            print(f"错误: {livp_path} 中未找到PNG数据")
            return False
        
        end_idx = data.find(end_marker, start_idx)
        if end_idx == -1:
            print(f"错误: {livp_path} 中PNG数据不完整")
            return False
        
        from io import BytesIO
        png_data = data[start_idx:end_idx + 8]
        img = Image.open(BytesIO(png_data))
        
        if output_path is None:
            base_name = os.path.splitext(os.path.basename(livp_path))[0]
            output_path = os.path.join(os.path.dirname(livp_path), f"{base_name}.png")
        
        img.save(output_path, 'PNG')
        print(f"转换成功: {livp_path} -> {output_path}")
        return True
    
    except Exception as e:
        print(f"转换失败 {livp_path}: {str(e)}")
        return False

def convert_directory(directory):
    livp_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.livp'):
                livp_files.append(os.path.join(root, file))
    
    if not livp_files:
        print(f"在目录 {directory} 中未找到.livp文件")
        return
    
    print(f"找到 {len(livp_files)} 个.livp文件")
    
    success_count = 0
    for livp_file in livp_files:
        if convert_livp_to_png(livp_file):
            success_count += 1
    
    print(f"\n转换完成: {success_count}/{len(livp_files)} 成功")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = os.path.expanduser("~/Desktop")
    
    convert_directory(directory)