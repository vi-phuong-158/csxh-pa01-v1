import os

project_dir = r"d:\Code\csxh-pa01-v1"
output_file = os.path.join(project_dir, "PA01_Source_Code.md")

include_extensions = ['.py', '.css', '.md', '.sql', '.bat', '.ps1', '.vbs']
exclude_dirs = [
    '.git', '.venv', '__pycache__', '.agents', '.agent', '.Jules', '_build_temp', 
    'dist_portable', 'dist_v2', 'dist_v3', 'uploads', 'backups'
]
exclude_files = [
    'aggregate_code.py', 
    'PA01_Source_Code.md',
    'Mo_ta_chi_tiet_PA01.md', # Exclude the description file itself from code dump
    'security_profile.db',
    'baocao_loi.xlsx',
    'PA01_Core_Source.zip'
]

with open(output_file, 'w', encoding='utf-8') as out:
    out.write("# Toàn bộ mã nguồn dự án PA01\n\n")
    
    for root, dirs, files in os.walk(project_dir):
        # modify dirs in-place to prune exclude_dirs
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            file_ext = os.path.splitext(file)[1]
            if file_ext in include_extensions and file not in exclude_files:
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    rel_path = os.path.relpath(file_path, project_dir)
                    # use relative path with forward slashes for better readability
                    rel_path_fmt = rel_path.replace(os.sep, '/')
                    lang = file_ext[1:] if file_ext else ''
                    
                    out.write(f"## {rel_path_fmt}\n")
                    if file_ext == '.md':
                        out.write(f"{content}\n\n")
                    else:
                        out.write(f"```{lang}\n")
                        out.write(content + "\n")
                        out.write("```\n\n")
                except Exception as e:
                    print(f"Could not read {file_path}: {e}")

print(f"Thành công! Toàn bộ file mã nguồn chính đã được gom vào {output_file}")
