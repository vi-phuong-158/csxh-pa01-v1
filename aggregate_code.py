import os

project_dir = r"d:\Code\csxh-pa01-v1"
output_file = os.path.join(project_dir, "PA01_Source_Code.md")

include_extensions = ['.py', '.css', '.md']
exclude_dirs = ['.git', '.venv', '__pycache__', 'tests', '.agents', '.Jules']
exclude_files = [
    'aggregate_code.py', 
    'PA01_Source_Code.md',
    'generate_1000_records.py',
    'generate_test_data.py',
    'verify_bulk_import.py',
    'verify_changes_phase1.py',
    'verify_changes_phase1_v2.py',
    'verify_phase2.py'
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
