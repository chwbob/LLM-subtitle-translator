# package_config.py
import sys
from pathlib import Path

# 定义应用程序信息
APP_NAME = "SubtitleTranslator"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Your Name"
APP_DESCRIPTION = "AI-powered subtitle translator"

# 定义图标路径（如果有的话）
ICON_PATH = Path("assets/icon.ico")  # 替换为你的图标路径

# 定义需要包含的数据文件
ADDITIONAL_FILES = [
    # ('source_path', 'destination_directory')
    # 例如：('assets/logo.png', 'assets')
]

# 定义PyInstaller配置
def get_pyinstaller_config():
    return [
        'subtitle_translator.py',  # 主程序文件名
        '--name=%s' % APP_NAME,
        '--onefile',  # 打包成单个exe文件
        '--windowed',  # 使用GUI模式
        '--clean',  # 清理临时文件
        '--noconfirm',  # 覆盖输出目录
        '--log-level=INFO',
        # '--icon=%s' % ICON_PATH if ICON_PATH.exists() else '',  # 添加图标
        '--add-data=%s' % ';'.join(['%s;%s' % (src, dst) for src, dst in ADDITIONAL_FILES]),
        '--hidden-import=tkinter',
        '--hidden-import=asyncio',
        '--hidden-import=aiohttp',
        '--hidden-import=srt',
    ]