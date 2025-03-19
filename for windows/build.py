# build_qt.py
import os
import subprocess
import shutil
from pathlib import Path

def clean_build_directories():
    """清理构建目录"""
    directories = ['build', 'dist']
    files = ['*.spec']

    for directory in directories:
        if os.path.exists(directory):
            print(f"正在删除 {directory} 目录...")
            shutil.rmtree(directory)

    for pattern in files:
        for file_path in Path('.').glob(pattern):
            print(f"正在删除 {file_path}...")
            file_path.unlink()

def create_spec_file():
    """创建spec文件"""
    # 检查图标是否存在
    icon_path = os.path.join('assets', 'icon.ico')
    icon_exists = os.path.exists(icon_path)

    icon_option = f"icon='{icon_path}'," if icon_exists else ""

    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['subtitle_translator_qt.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets')],
    hiddenimports=['PyQt6', 'asyncio', 'aiohttp', 'srt', 'nest_asyncio'],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SubtitleTranslator_Qt',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    {icon_option}
)
'''
    with open('subtitle_translator_qt.spec', 'w') as f:
        f.write(spec_content)

def build_executable():
    """构建可执行文件"""
    try:
        # 清理旧的构建文件
        print("清理旧的构建文件...")
        clean_build_directories()

        # 确保assets目录存在
        assets_dir = Path('assets')
        if not assets_dir.exists():
            print("创建assets目录...")
            assets_dir.mkdir()
            print("注意: 请将icon.ico文件放入assets目录中")

        # 创建spec文件
        print("创建spec文件...")
        create_spec_file()

        # 使用spec文件构建
        print("开始构建...")
        subprocess.run(['pyinstaller', 'subtitle_translator_qt.spec'], check=True)

        print("\n构建成功完成！")
        print(f"可执行文件位于: {os.path.join('dist', 'SubtitleTranslator_Qt.exe')}")

    except subprocess.CalledProcessError as e:
        print(f"\n构建失败: {str(e)}")
    except Exception as e:
        print(f"\n发生错误: {str(e)}")

if __name__ == '__main__':
    # 打印当前工作目录
    print(f"当前工作目录: {os.getcwd()}")
    build_executable()