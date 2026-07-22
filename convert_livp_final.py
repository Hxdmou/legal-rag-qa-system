import os
import sys
import zipfile
from PIL import Image
import pillow_heif

def convert_livp_to_png(livp_path, output_path=None):
    try:
        with zipfile.ZipFile(livp_path, 'r') as zip_ref:
            namelist = zip_ref.namelist()
            
            heic_files = [f for f in namelist if f.lower().endswith('.heic')]
            
            if not heic_files:
                jpeg_files = [f for f in namelist if f.lower().endswith('.jpg') or f.lower().endswith('.jpeg')]
                if jpeg_files:
                    with zip_ref.open(jpeg_files[0]) as img_data:
                        img = Image.open(img_data)
                        if output_path is None:
                            base_name = os.path.splitext(os.path.basename(livp_path))[0]
                            output_path = os.path.join(os.path.dirname(livp_path), f"{base_name}.png")
                        img.save(output_path, 'PNG')
                        print(f"转换成功: {livp_path} -> {output_path}")
                        return True
                else:
                    print(f"警告: {livp_path} 中未找到HEIC或JPEG文件")
                    return False
            
            heic_file = heic_files[0]
            with zip_ref.open(heic_file) as heic_data:
                heif_file = pillow_heif.read_heif(heic_data)
                img = Image.frombytes(
                    heif_file.mode,
                    heif_file.size,
                    heif_file.data,
                    "raw",
                    heif_file.mode,
                    heif_file.stride,
                )
                
                if output_path is None:
                    base_name = os.path.splitext(os.path.basename(livp_path))[0]
                    output_path = os.path.join(os.path.dirname(livp_path), f"{base_name}.png")
                
                img.save(output_path, 'PNG')
                print(f"转换成功: {livp_path} -> {output_path}")
                return True
    
    except zipfile.BadZipFile:
        print(f"警告: {livp_path} 不是有效的ZIP文件")
        return False
    
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