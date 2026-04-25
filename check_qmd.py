import subprocess
import os

# 检查 qmd 是否可用
try:
    result = subprocess.run(['which', 'qmd'], capture_output=True, text=True, timeout=5)
    print('=== qmd availability ===')
    print(f'Return code: {result.returncode}')
    print(f'Stdout: {result.stdout}')
    print(f'Stderr: {result.stderr}')
    qmd_available = result.returncode == 0
except Exception as e:
    print(f'qmd check error: {e}')
    qmd_available = False

print(f'\nqmd available: {qmd_available}')

# 检查 memory 目录
memory_dir = '/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/memory/'
print(f'\n=== Memory directory check ===')
print(f'Path: {memory_dir}')
print(f'Exists: {os.path.exists(memory_dir)}')

if os.path.exists(memory_dir):
    try:
        files = os.listdir(memory_dir)
        print(f'Files count: {len(files)}')
        
        # 检查 .qmd 和 .vec 文件
        qmd_files = [f for f in files if f.endswith('.qmd')]
        vec_files = [f for f in files if f.endswith('.vec') or '.vec' in f]
        
        print(f'\n.qmd files: {qmd_files}')
        print(f'.vec related files: {vec_files}')
        
        # 列出所有文件
        print(f'\nAll files:')
        for f in sorted(files):
            fpath = os.path.join(memory_dir, f)
            fsize = os.path.getsize(fpath) if os.path.isfile(fpath) else 'DIR'
            print(f'  {f} ({fsize})')
    except Exception as e:
        print(f'Error listing directory: {e}')
else:
    print('Memory directory does not exist')
