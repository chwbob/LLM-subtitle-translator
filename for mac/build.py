#!/usr/bin/env python3
# build.py - macOS 应用构建脚本(使用py2app)
import os
import sys
import shutil
from pathlib import Path
import subprocess


def clean_build_directories():
    """清理构建目录"""
    directories = ['build', 'dist']
    files = ['setup.py']

    for directory in directories:
        if os.path.exists(directory):
            print(f"正在删除 {directory} 目录...")
            shutil.rmtree(directory)

    for pattern in files:
        for file_path in Path('.').glob(pattern):
            print(f"正在删除 {file_path}...")
            file_path.unlink()


def create_qt_conf():
    """创建qt.conf文件以禁用问题服务"""
    print("创建 qt.conf 文件...")
    config_content = """[Paths]
Plugins = plugins
Imports = imports
Qml2Imports = qml

[Qt]
GeoServices = false
Location = false
Multimedia = false
WebEngine = false
WebView = false
"""
    with open('qt.conf', 'w') as f:
        f.write(config_content)
    print("已创建 qt.conf 配置文件")


def create_early_init_py():
    """创建包含早期初始化代码的Python模块"""
    print("创建早期初始化模块...")
    init_code = """# early_init.py - 在应用启动时最早执行的代码
import os

def disable_qt_services():
    """
    """
    # 禁用位置服务和其他可能导致崩溃的服务
    os.environ["QT_MAC_WANTS_LAYER"] = "1"  # 解决某些 macOS 渲染问题
    os.environ["QT_ENABLE_GEOSERVICES"] = "0"  # 禁用地理服务
    os.environ["QT_ENABLE_LOCATION"] = "0"  # 禁用位置服务
    os.environ["QT_BEARER_POLL_TIMEOUT"] = "-1"  # 禁用网络检查
    os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt.qpa.*=false"  # 减少日志
    os.environ["QT_MULTIMEDIA_PREFERRED_PLUGINS"] = "nosystems"  # 禁用多媒体
    os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"  # 优化性能
    os.environ["QT_OPENGL"] = "software"  # 使用软件渲染
    os.environ["QT_PLUGIN_PERMISSION"] = "0"  # 禁用权限请求
    os.environ["QT_LOCATION_DISABLED"] = "1"  # 明确禁用位置
    os.environ["QT_MAC_DISABLE_FOREGROUND_APPLICATION_TRANSFORM"] = "1"  # 防止macOS特定转换

# 在模块导入时立即执行
disable_qt_services()
"""
    with open('early_init.py', 'w') as f:
        f.write(init_code)
    print("已创建早期初始化模块")


def modify_source_code():
    """修改源代码以尽早禁用Qt服务"""
    print("修改源代码以确保尽早禁用Qt服务...")
    if os.path.exists('subtitle_translator.py'):
        shutil.copy('subtitle_translator.py', 'subtitle_translator.py.bak')
        with open('subtitle_translator.py', 'r', encoding='utf-8') as f:
            content = f.read()

        # 在导入部分的开始添加early_init导入
        import_start = content.find('import sys')
        if import_start >= 0:
            early_import = 'import early_init  # 最早执行，禁用Qt服务\n'
            content = content[:import_start] + early_import + content[import_start:]

            # 写入修改后的文件
            with open('subtitle_translator.py', 'w', encoding='utf-8') as f:
                f.write(content)
            print("已修改源代码，添加early_init导入")
        else:
            print("警告: 未找到适合添加导入的位置")
    else:
        print("警告: 未找到subtitle_translator.py文件")


def create_setup_py():
    """创建py2app的setup.py文件"""
    print("创建py2app的setup.py文件...")

    # 检查图标是否存在
    icon_path = os.path.join('assets', 'icon.icns')
    icon_exists = os.path.exists(icon_path)
    icon_option = f"'iconfile': '{icon_path}'," if icon_exists else ""

    setup_content = f'''
from setuptools import setup

APP = ['subtitle_translator.py']
DATA_FILES = [
    ('assets', ['assets/icon.ico', 'assets/AAA.jpg', 'assets/icon.icns']), 
    ('', ['qt.conf', 'early_init.py'])
]
OPTIONS = {{
    'argv_emulation': False,
    'packages': ['PyQt6', 'asyncio', 'aiohttp', 'srt', 'nest_asyncio'],
    'excludes': ['PyQt5', 'tkinter', 'matplotlib'],
    'includes': ['early_init'],
    'arch': 'universal2',
    {icon_option}
    'plist': {{
        'CFBundleName': 'SubtitleTranslator',
        'CFBundleDisplayName': 'Subtitle Translator',
        'CFBundleGetInfoString': 'AI-powered subtitle translator',
        'CFBundleVersion': '1.1.0',
        'CFBundleShortVersionString': '1.1.0',
        'NSHighResolutionCapable': True,
        'NSPrincipalClass': 'NSApplication',
        # 明确声明不使用各种系统服务
        'NSLocationUsageDescription': 'This app does not use location services',
        'NSLocationWhenInUseUsageDescription': 'This app does not use location services',
        'NSMicrophoneUsageDescription': 'This app does not use microphone access',
        'NSCameraUsageDescription': 'This app does not use camera access',
        'NSBluetoothAlwaysUsageDescription': 'This app does not use Bluetooth',
        'NSBluetoothPeripheralUsageDescription': 'This app does not use Bluetooth',
    }},
    # PyQt设置
    'qt_plugins': ['imageformats'],
    # 排除不需要的Qt插件
    'excludes_plugins': [
        'position', 'geoservices', 'webview', 'sensors', 'location',
        'multimedia', 'audio', 'designer'
    ],
}}

setup(
    name='SubtitleTranslator',
    app=APP,
    data_files=DATA_FILES,
    options={{'py2app': OPTIONS}},
    setup_requires=['py2app'],
)
'''
    with open('setup.py', 'w') as f:
        f.write(setup_content)
    print("已创建setup.py文件")


def build_executable():
    """使用py2app构建macOS应用"""
    try:
        # 清理旧的构建文件
        print("清理旧的构建文件...")
        clean_build_directories()

        # 确保assets目录存在
        assets_dir = Path('assets')
        if not assets_dir.exists():
            print("创建assets目录...")
            assets_dir.mkdir()

        # 创建早期初始化模块
        create_early_init_py()

        # 修改源代码
        modify_source_code()

        # 创建Qt配置文件
        create_qt_conf()

        # 创建setup.py
        create_setup_py()

        # 使用py2app构建
        print("开始使用py2app构建macOS应用...")
        os.environ["QT_MAC_WANTS_LAYER"] = "1"
        os.environ["QT_ENABLE_GEOSERVICES"] = "0"
        os.environ["QT_ENABLE_LOCATION"] = "0"

        # 执行构建命令
        build_cmd = ["python", "setup.py", "py2app"]
        print(f"执行命令: {' '.join(build_cmd)}")
        result = subprocess.run(build_cmd, check=False)

        if result.returncode != 0:
            print(f"py2app构建失败，退出码: {result.returncode}")
            return

        # 检查构建结果
        app_path = os.path.join("dist", "SubtitleTranslator.app")
        if os.path.exists(app_path):
            print("\n构建成功完成！")
            print(f"应用位于: {app_path}")

            # 对应用进行简单签名以减少macOS安全提示
            print("对应用进行签名...")
            subprocess.run(["codesign", "--force", "--deep", "--sign", "-", app_path])
            print("签名完成")

            # 创建ZIP存档
            print("创建ZIP存档...")
            os.chdir("dist")
            subprocess.run(["zip", "-r", "SubtitleTranslator-macOS-universal.zip", "SubtitleTranslator.app"])
            os.chdir("..")
            print(f"ZIP存档已创建: dist/SubtitleTranslator-macOS-universal.zip")
        else:
            print("构建过程完成，但找不到应用Bundle。请检查构建日志")

    except Exception as e:
        print(f"\n构建失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    print(f"当前工作目录: {os.getcwd()}")
    build_executable()