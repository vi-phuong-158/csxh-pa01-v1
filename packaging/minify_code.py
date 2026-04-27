import os
import shutil
import ast
import re
from pathlib import Path

def minify_python(source_code):
    """Sử dụng AST để xoá TOÀN BỘ comment và docstring trong Python"""
    try:
        parsed = ast.parse(source_code)
        # ast.unparse() chỉ in ra code thuần, không chứa comment/docstring
        return ast.unparse(parsed)
    except Exception as e:
        print(f"Error minifying Python: {e}")
        return source_code

def minify_html(source_code):
    """Xoá comment HTML và Jinja2"""
    # Xoá comment Jinja {# ... #}
    source_code = re.sub(r'\{#.*?#\}', '', source_code, flags=re.DOTALL)
    # Xoá comment HTML <!-- ... --> (bỏ qua DOCTYPE)
    source_code = re.sub(r'<!--(?!>).*?-->', '', source_code, flags=re.DOTALL)
    return source_code

def minify_css(source_code):
    """Xoá comment CSS /* ... */"""
    return re.sub(r'/\*.*?\*/', '', source_code, flags=re.DOTALL)

def minify_js(source_code):
    """Xoá comment JS /* ... */ và // ... """
    source_code = re.sub(r'/\*.*?\*/', '', source_code, flags=re.DOTALL)
    source_code = re.sub(r'//.*', '', source_code)
    return source_code

def process_directory(src_dir, dest_dir):
    src_dir = Path(src_dir)
    dest_dir = Path(dest_dir)
    
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    
    shutil.copytree(src_dir, dest_dir, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.git'))
    
    print(f"Minifying {dest_dir.name}...")
    
    for filepath in dest_dir.rglob("*"):
        if not filepath.is_file():
            continue
            
        try:
            content = filepath.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue  # Bỏ qua file nhị phân (ảnh, font...)
            
        new_content = content
        
        if filepath.suffix == '.py':
            new_content = minify_python(content)
        elif filepath.suffix == '.html':
            new_content = minify_html(content)
        elif filepath.suffix == '.css':
            new_content = minify_css(content)
        elif filepath.suffix == '.js':
            new_content = minify_js(content)
            
        if new_content != content:
            filepath.write_text(new_content, encoding="utf-8")

if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    build_src_dir = base_dir / "build_src"
    
    if build_src_dir.exists():
        shutil.rmtree(build_src_dir)
    build_src_dir.mkdir()
    
    print("Starting clone and minify...")
    
    # 1. Process backend
    if (base_dir / "backend").exists():
        process_directory(base_dir / "backend", build_src_dir / "backend")
        
    # 2. Process frontend
    if (base_dir / "frontend").exists():
        process_directory(base_dir / "frontend", build_src_dir / "frontend")
        
    # 3. Process run_server.py
    run_server_src = base_dir / "run_server.py"
    if run_server_src.exists():
        content = run_server_src.read_text(encoding="utf-8")
        minified = minify_python(content)
        (build_src_dir / "run_server.py").write_text(minified, encoding="utf-8")
        
    # 4. Copy các file cần thiết khác
    for f in [".env.example", "requirements.txt"]:
        src = base_dir / f
        if src.exists():
            shutil.copy2(src, build_src_dir / f)

    print("Minification complete! Code is ready in build_src.")
