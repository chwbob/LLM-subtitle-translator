import sys
import os
import re
import json
import asyncio
import aiohttp
import srt
import nest_asyncio
import shutil
import time
import traceback
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, QLineEdit,
                             QFileDialog, QTextEdit, QWidget, QVBoxLayout, QHBoxLayout,
                             QTabWidget, QFrame, QCheckBox, QMessageBox, QComboBox,
                             QScrollArea, QGridLayout, QSpacerItem, QSizePolicy,
                             QGroupBox, QFormLayout, QSpinBox, QDoubleSpinBox,
                             QTableWidget, QHeaderView, QTableWidgetItem, QProgressDialog,
                             QDialog, QDialogButtonBox, QMenu, QProgressBar)
from PyQt6.QtCore import Qt, QObject, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont, QPixmap, QCursor, QTextCursor

# 应用 nest_asyncio 来解决事件循环问题
nest_asyncio.apply()

# 颜色常量定义
# 主题颜色
COLOR_PRIMARY = "#007AFF"  # 主色调蓝色
COLOR_PRIMARY_HOVER = "#0062CC"  # 主色调悬停
COLOR_SUCCESS = "#4CD964"  # 成功绿色
COLOR_WARNING = "#FDBC2C"  # 警告黄色
COLOR_DANGER = "#FF5F57"  # 危险红色
COLOR_DARK = "#262626"  # 暗色
COLOR_LIGHT = "#F5F5F5"  # 亮色
COLOR_WHITE = "#FFFFFF"  # 白色
COLOR_TEXT = "#333333"  # 文本颜色
COLOR_TEXT_LIGHT = "#666666"  # 浅色文本
COLOR_BORDER = "#CCCCCC"  # 边框颜色
COLOR_BACKGROUND = "#F5F5F5"  # 背景色

# 语言支持
# 支持的语言
SUPPORTED_LANGUAGES = {
    "zh": "简体中文",
    "en": "English"
}

# 翻译文本
TRANSLATIONS = {
    "zh": {
        # 窗口标题和通用文本
        "app_title": "大模型字幕翻译小助手",
        "version": "版本",
        "save": "保存",
        "cancel": "取消",
        "confirm": "确认",
        "ok": "确定",
        "error": "错误",
        "warning": "警告",
        "success": "成功",
        "info": "信息",
        
        # 主界面元素
        "source_file": "字幕源文件",
        "output_dir": "输出目录",
        "browse_file": "打开文件",
        "browse_dir": "选择目录",
        "default_output_dir": "默认与输入文件同目录",
        
        # 标签页
        "api_settings": "API 设置", 
        "translation_settings": "翻译设置",
        "system_settings": "系统设置",
        "terminology_settings": "术语管理",
        
        # API设置
        "api_host": "API地址",
        "api_key": "API密钥",
        "model": "模型",
        "show": "显示",
        "hide": "隐藏",
        
        # 翻译设置
        "source_lang": "原文语言",
        "target_lang": "目标语言",
        "temperature": "温度",
        "batch_size": "批处理大小",
        "request_delay": "请求延迟(秒)",
        "show_original": "显示原文",
        "clean_punctuation": "清理标点",
        "multi_phase": "多阶段翻译",
        "enable_recovery": "启用恢复功能",
        "enable_batching": "启用批处理",
        
        # 系统设置
        "interface_language": "界面语言",
        
        # 按钮
        "start_translation": "开始翻译",
        "stop_translation": "停止翻译",
        "save_config": "保存配置",
        "about": "关于",
        "donation": "赞助",
        "show_terminology": "术语管理",
        
        # 术语管理
        "term": "术语",
        "translation": "翻译",
        "add_term": "添加术语",
        "remove_term": "删除术语",
        "import_terms": "导入术语",
        "export_terms": "导出术语",
        "save_terms": "保存术语",
        
        # 消息
        "config_saved": "配置已成功保存",
        "config_save_failed": "无法保存配置: {0}",
        "terms_saved": "术语列表已保存",
        "terms_save_failed": "术语列表保存失败，请检查文件权限",
        "stopping_translation": "正在停止翻译...",
        "translation_stopped": "翻译已停止",
        "translation_completed": "翻译完成！",
        "translation_failed": "翻译失败: {0}",
        "translation_in_progress": "翻译进行中...",
        "select_subtitle_file": "选择字幕文件",
        "select_output_dir": "选择输出目录",
        "no_subtitle_found": "没有找到有效的字幕内容进行翻译",
        "stopped_by_user": "翻译已被用户中断",
        
        # 关于和捐赠对话框
        "about_title": "关于大模型字幕翻译小助手",
        "about_content": "这是一个使用大型语言模型进行字幕翻译的工具。",
        "developer": "开发者",
        "donation_title": "赞助支持",
        "donation_text": "如果您觉得这个工具有用，可以考虑赞助支持开发者。",
        "donation_alipay": "支付宝",
        "donation_wechat": "微信支付",
        "hide": "隐藏",
        "show": "显示"
    },
    "en": {
        # Window title and common text
        "app_title": "AI Subtitle Translator",
        "version": "Version",
        "save": "Save",
        "cancel": "Cancel",
        "confirm": "Confirm",
        "ok": "OK",
        "error": "Error",
        "warning": "Warning",
        "success": "Success",
        "info": "Information",
        
        # Main interface elements
        "source_file": "Subtitle Source File",
        "output_dir": "Output Directory",
        "browse_file": "Open File",
        "browse_dir": "Select Directory",
        "default_output_dir": "Same as input file by default",
        
        # Tabs
        "api_settings": "API Settings", 
        "translation_settings": "Translation Settings",
        "system_settings": "System Settings",
        "terminology_settings": "Terminology Management",
        
        # API settings
        "api_host": "API Host",
        "api_key": "API Key",
        "model": "Model",
        "show": "Show",
        "hide": "Hide",
        
        # Translation settings
        "source_lang": "Source Language",
        "target_lang": "Target Language",
        "temperature": "Temperature",
        "batch_size": "Batch Size",
        "request_delay": "Request Delay (sec)",
        "show_original": "Show Original",
        "clean_punctuation": "Clean Punctuation",
        "multi_phase": "Multi-phase Translation",
        "enable_recovery": "Enable Recovery",
        "enable_batching": "Enable Batching",
        
        # System settings
        "interface_language": "Interface Language",
        
        # Buttons
        "start_translation": "Start Translation",
        "stop_translation": "Stop Translation",
        "save_config": "Save Config",
        "about": "About",
        "donation": "Donation",
        "show_terminology": "Terminology Manager",
        
        # Terminology management
        "term": "Term",
        "translation": "Translation",
        "add_term": "Add Term",
        "remove_term": "Remove Term",
        "import_terms": "Import Terms",
        "export_terms": "Export Terms",
        "save_terms": "Save Terms",
        
        # Messages
        "config_saved": "Configuration saved successfully",
        "config_save_failed": "Failed to save config: {0}",
        "terms_saved": "Terminology list saved",
        "terms_save_failed": "Failed to save terminology list, please check file permissions",
        "stopping_translation": "Stopping translation...",
        "translation_stopped": "Translation stopped",
        "translation_completed": "Translation completed!",
        "translation_failed": "Translation failed: {0}",
        "translation_in_progress": "Translation in progress...",
        "select_subtitle_file": "Select subtitle file",
        "select_output_dir": "Select output directory",
        "no_subtitle_found": "No valid subtitle content found for translation",
        "stopped_by_user": "Translation interrupted by user",
        
        # About and donation dialogs
        "about_title": "About AI Subtitle Translator",
        "about_content": "This is a tool for subtitle translation using large language models.",
        "developer": "Developer",
        "donation_title": "Support Development",
        "donation_text": "If you find this tool useful, please consider supporting the developer.",
        "donation_alipay": "Alipay",
        "donation_wechat": "WeChat Pay",
        "hide": "Hide",
        "show": "Show"
    }
}

def exception_hook(exctype, value, traceback):
    """全局异常处理器"""
    import traceback as tb
    error_msg = ''.join(tb.format_exception(exctype, value, traceback))
    print(f"未捕获的异常: {error_msg}")

    # 将错误写入日志文件
    with open('error_log.txt', 'a', encoding='utf-8') as f:
        f.write(f"\n[{datetime.now()}] 应用崩溃:\n")
        f.write(error_msg)
        f.write('\n' + '-' * 50 + '\n')

    # 显示错误对话框
    QMessageBox.critical(None, "应用程序错误",
                         f"应用程序遇到了未预期的错误，需要关闭。\n\n"
                         f"错误详情已保存到 error_log.txt\n\n"
                         f"错误: {value}")


def resource_path(relative_path):
    """获取资源的绝对路径，适用于开发环境和PyInstaller打包后的环境"""
    try:
        # PyInstaller创建临时文件夹，将路径存储在_MEIPASS中
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


@dataclass
class TranslationConfig:
    """翻译配置类"""
    source_lang: str  # 源语言
    target_lang: str  # 目标语言
    api_key: str  # API密钥
    api_host: str  # API主机地址
    model: str  # 模型名称
    temperature: float = 0.5  # 温度系数
    max_tokens: int = None  # 最大生成令牌数
    batch_size: int = 40  # 批量处理字幕数量
    concurrency: int = 5  # 并发数量
    delay: float = 1.0  # 每次请求后的延迟时间（默认改为1.0秒）
    preserve_format: bool = True  # 保留原始格式
    netflix_style: bool = True  # Netflix风格优化字幕分段（默认启用）
    terminology_consistency: bool = True  # 保持术语一致性（默认启用）
    multi_phase: bool = False  # 是否使用多阶段翻译流程
    recovery_enabled: bool = False  # 是否启用恢复功能
    recovery_file: str = ""  # 恢复文件路径
    enable_batching: bool = False  # 是否启用批量翻译
    request_delay: float = 1.0  # API请求之间的延迟（秒）
    clean_punctuation: bool = False  # 是否清理标点符号
    show_original: bool = True  # 是否显示原文
    custom_terminology: dict = None  # 用户自定义术语字典
    
    def __getitem__(self, key):
        """允许像字典一样访问配置"""
        return getattr(self, key)
        
    def get(self, key, default=None):
        """获取配置值，如果不存在则返回默认值"""
        return getattr(self, key, default)


class SubtitleProcessor:
    @staticmethod
    def remove_hearing_impaired(text: str) -> str:
        """删除听障字幕（方括号内的内容）"""
        if not text or not text.strip():
            return ""
            
        original_text = text
        
        # 处理带有破折号前缀的听障字幕，如 "- [light steps]"
        dash_pattern = r'^\s*-\s*\[.*?\]'
        if re.match(dash_pattern, text):
            # 检查是否整行都是类似格式 (可能有多行，每行都是破折号+方括号格式)
            lines = text.split('\n')
            all_lines_are_dash_hi = all(re.match(r'^\s*-\s*\[.*?\]', line.strip()) for line in lines if line.strip())
            if all_lines_are_dash_hi:
                return ""  # 如果整个字幕都是破折号+听障内容，直接返回空
        
        # 清理带有破折号前缀的听障标记
        cleaned_text = re.sub(r'\s*-\s*\[.*?\]', '', text)
        
        # 清理所有方括号内的内容，这包括所有听障字幕标记
        cleaned_text = re.sub(r'\[.*?\]', '', cleaned_text)
        
        # 也处理常见的听障标记格式，如 (音乐) (鼓掌)
        cleaned_text = re.sub(r'\(.*?\)', '', cleaned_text)
        
        # 处理其他常见格式，如 *笑声* 或 #音乐#
        cleaned_text = re.sub(r'[*#].*?[*#]', '', cleaned_text)
        
        # 处理带有破折号前缀的听障词汇，如 "- Music" or "- 音乐"
        cleaned_text = re.sub(r'^\s*-\s*(音乐|音效|笑声|掌声|叹息|喘息|脚步声|门响|电话铃|引擎声|Music|Sound|Laughter|Applause|Sighs|Breathing|Footsteps|Door|Phone|Engine)$', '', cleaned_text, flags=re.IGNORECASE|re.MULTILINE)
        
        # 处理常见的听障词汇，如果它们单独存在于一行
        common_patterns = [
            r'^(?:音乐|音效|笑声|掌声|叹息|喘息|脚步声|门响|电话铃|引擎声)$',
            r'^(?:Music|Sound|Laughter|Applause|Sighs|Breathing|Footsteps|Door|Phone|Engine)$'
        ]
        for pattern in common_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
        
        # 清理前后空白并返回
        cleaned_text = cleaned_text.strip()
        
        # 移除可能留下的孤立破折号 (如果一行只剩下破折号)
        cleaned_text = re.sub(r'^\s*-\s*$', '', cleaned_text, flags=re.MULTILINE)
        
        # 处理只剩下多个破折号的情况
        if re.match(r'^\s*(-\s*)+$', cleaned_text):
            return ""
        
        # 如果清理后文本为空，直接返回空字符串而不是原始文本
        # 这意味着整个字幕都是听障内容，应该被完全移除
        if not cleaned_text:
            return ""
            
        return cleaned_text

    @staticmethod
    def clean_punctuation(text: str) -> str:
        """将标点符号替换为空格"""
        # 定义所有需要替换的标点符号
        punctuation_pattern = r'[，。！？：；,.!?:;，。！？：；""《》〈〉：！；，。、？\-\[\]【】()]'
        cleaned_text = re.sub(punctuation_pattern, ' ', text)
        # 将多个空格合并为一个空格
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        return cleaned_text.strip()

    @staticmethod
    def split_into_sentences(text: str) -> List[str]:
        """将文本分割成句子"""
        # 使用标点符号作为分隔符
        sentences = re.split(r'(?<=[.!?。！？])\s*', text)
        return [s.strip() for s in sentences if s.strip()]
        
    @staticmethod
    async def optimize_subtitle_segmentation(subtitles: List[dict], config: TranslationConfig) -> List[dict]:
        """使用AI优化字幕分段，达到Netflix级别的字幕质量
        
        1. 分析完整字幕内容和时间轴
        2. 重新分割字幕，确保每行长短适中，在完整停顿处断句
        3. 确保专有名词不被分开
        4. 保持时间轴对齐
        """
        if not subtitles or not config.netflix_style:
            return subtitles  # 如果未启用或无字幕，直接返回原始字幕
            
        try:
            # 为了限制API请求量，每次处理最多100条字幕
            MAX_SUBS_PER_REQUEST = 100
            optimized_subtitles = []
            
            # 分批处理
            for i in range(0, len(subtitles), MAX_SUBS_PER_REQUEST):
                batch = subtitles[i:i+MAX_SUBS_PER_REQUEST]
                
                # 准备请求数据
                formatted_subs = []
                for sub in batch:
                    formatted_subs.append(
                        f"[{sub['index']}] {sub['time_info']}\n{sub['content']}"
                    )
                
                all_subs_text = "\n\n".join(formatted_subs)
                
                # 构建系统提示词
                system_prompt = f"""You are a professional subtitle editor specializing in Netflix-quality subtitle segmentation.
Your task is to optimize subtitle segmentation based on these guidelines:
1. Each subtitle line should be of moderate length (max ~42 chars for Western languages)
2. Break at natural pause points (end of clauses, punctuation)
3. Keep proper nouns and phrases together - never split names, places, or technical terms
4. Maintain existing timecodes exactly as they are
5. Return the EXACT SAME content just with improved line breaks 
6. IMPORTANT: Never merge or split subtitles - keep exactly one output subtitle for each input

For each subtitle, analyze its content and improve its segmentation by adding appropriate line breaks.
Return the subtitles in the same exact format and order, with the same numbering.
"""

                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Please optimize the segmentation of these subtitles:\n\n{all_subs_text}"}
                ]
                
                # 发送请求
                async with aiohttp.ClientSession() as session:
                    headers = {
                        "Authorization": f"Bearer {config.api_key}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "model": config.model,
                        "messages": messages,
                        "temperature": 0.3  # 低温度以确保结果稳定
                    }
                    
                    api_endpoint = f"{config.api_host}/v1/chat/completions" 
                    print(f"优化字幕分段时使用API主机: {config.api_host}")
                    print(f"优化字幕分段API端点: {api_endpoint}")
                    
                    async with session.post(
                            api_endpoint,
                            headers=headers,
                            json=payload,
                            timeout=aiohttp.ClientTimeout(total=120)  # 两分钟超时
                    ) as response:
                        if response.status != 200:
                            # 如果API请求失败，返回原始字幕批次
                            return subtitles
                            
                        result = await response.json()
                        if "choices" in result and result["choices"]:
                            response_text = result["choices"][0]["message"]["content"]
                            
                            # 解析优化后的字幕
                            optimized_batch = SubtitleProcessor._parse_optimized_subtitles(response_text, batch)
                            optimized_subtitles.extend(optimized_batch)
                        else:
                            # 如果API响应没有结果，添加原始批次
                            optimized_subtitles.extend(batch)
                
            # 验证优化后的字幕数量是否与原始字幕数量匹配
            if len(optimized_subtitles) != len(subtitles):
                # 数量不匹配时使用原始字幕
                return subtitles
                
            return optimized_subtitles
        except Exception as e:
            # 出现任何错误，返回原始字幕
            print(f"字幕分段优化出错: {str(e)}")
            return subtitles
    
    @staticmethod
    async def multi_phase_translate(subtitles: List[dict], config: TranslationConfig, signals=None) -> tuple:
        """多阶段翻译: 先批量翻译，再提取术语、优化格式和时间轴
        
        1. 阶段一: 初步翻译和术语提取
        2. 阶段二: 术语统一化和翻译反思  
        3. 阶段三: 最终翻译、分段优化和时间轴调整
        
        Args:
            subtitles: 字幕列表
            config: 翻译配置
            signals: 信号对象，用于发送进度信息
            
        Returns:
            (翻译结果列表, 术语字典)
        """
        if not subtitles:
            if signals:
                signals.progress.emit("没有找到有效的字幕")
            return [], {}
        
        # 过滤空内容的字幕
        cleaned_subtitles = [sub for sub in subtitles if sub["content"].strip()]
        if not cleaned_subtitles:
            if signals:
                signals.progress.emit("没有找到有效的字幕内容进行翻译")
            return [], {}
        
        if signals:
            signals.progress.emit(f"开始多阶段翻译流程，共有 {len(cleaned_subtitles)} 条字幕")
            signals.progress.emit("阶段1/3: 初步翻译和术语提取...")
        
        # 阶段1: 初步翻译和术语提取
        terminology_dict = {}
        first_pass_translations = []
        
        # 批量处理初步翻译
        INITIAL_BATCH_SIZE = config.batch_size
        
        # 移除听障字幕内容
        hearing_impaired_pattern = r'\[.*?\]|\(.*?\)'  # 匹配方括号或圆括号中的内容
        removed_hi_count = 0
        
        for i in range(0, len(cleaned_subtitles), INITIAL_BATCH_SIZE):
            batch = cleaned_subtitles[i:min(i + INITIAL_BATCH_SIZE, len(cleaned_subtitles))]
            
            if signals:
                signals.progress.emit(f"处理批次 {i//INITIAL_BATCH_SIZE + 1}/{(len(cleaned_subtitles)+INITIAL_BATCH_SIZE-1)//INITIAL_BATCH_SIZE}")
            
            # 提取批次字幕内容，并移除听障字幕
            batch_texts = []
            for sub in batch:
                # 先移除听障字幕内容再进行翻译
                original_content = sub['content']
                cleaned_content = SubtitleProcessor.remove_hearing_impaired(original_content)
                
                # 统计移除的听障字幕数量
                if cleaned_content != original_content:
                    removed_hi_count += 1
                
                batch_texts.append(cleaned_content)
            
            # 构建批量翻译请求
            system_prompt = f"""你是一位专业的{config.source_lang}到{config.target_lang}字幕翻译专家。
请将提供的字幕批量翻译。
请遵循以下规则:
1. 保持翻译的准确性和流畅度
2. 保持一致的翻译风格
3. 在翻译过程中注意提取专业术语
4. 提供简洁有效的译文，不过度解释或增加内容
"""

            user_prompt = f"""请翻译以下字幕，并从中提取专业术语:

"""
            for idx, text in enumerate(batch_texts):
                user_prompt += f"[{idx+1}] {text}\n"
                
            user_prompt += f"""
请以如下格式返回结果:
1. 首先列出所有翻译结果，使用[编号]标记
2. 然后提供你发现的术语表

返回格式:
[1] 翻译1
[2] 翻译2
...

术语表:
术语1 | 翻译1
术语2 | 翻译2
...
"""
            
            try:
                # 发送请求进行初步翻译
                async with aiohttp.ClientSession() as session:
                    headers = {
                        "Authorization": f"Bearer {config.api_key}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "model": config.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.3
                    }
                    
                    api_endpoint = f"{config.api_host}/v1/chat/completions"
                    
                    if signals:
                        signals.progress.emit(f"发送初步翻译请求...")
                    
                    async with session.post(
                        api_endpoint,
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=180)
                    ) as response:
                        if response.status != 200:
                            error_message = f"初步翻译API请求失败，状态码: {response.status}，错误: {await response.text()}"
                            if signals:
                                signals.error.emit(error_message)
                            continue
                            
                        result = await response.json()
                        response_text = result["choices"][0]["message"]["content"]
                        
                        # 提取翻译结果和术语
                        translations_match = re.search(r'((\[\d+\].*\n)+)', response_text, re.DOTALL)
                        if translations_match:
                            translations_text = translations_match.group(1)
                            pattern = r'\[(\d+)\]\s*(.*?)(?=\[\d+\]|\n\n|$)'
                            matches = re.finditer(pattern, translations_text, re.DOTALL)
                            
                            batch_translations = [""] * len(batch)
                            for match in matches:
                                idx = int(match.group(1)) - 1
                                if 0 <= idx < len(batch):
                                    batch_translations[idx] = match.group(2).strip()
                            
                            first_pass_translations.extend(batch_translations)
                        else:
                            # 如果无法提取到翻译，则添加空字符串
                            first_pass_translations.extend([""] * len(batch))
                        
                        # 提取术语
                        terminology_match = re.search(r'术语表[：:]\s*(.*?)$', response_text, re.DOTALL)
                        if terminology_match:
                            terms_text = terminology_match.group(1)
                            term_pattern = r'(.*?)\s*[\|丨]\s*(.*?)(?=\n|$)'
                            for term_match in re.finditer(term_pattern, terms_text):
                                source_term = term_match.group(1).strip()
                                target_term = term_match.group(2).strip()
                                if source_term and target_term:
                                    terminology_dict[source_term] = target_term
            
            except Exception as e:
                error_message = f"阶段1处理批次 {i//INITIAL_BATCH_SIZE + 1} 失败: {str(e)}"
                if signals:
                    signals.error.emit(error_message)
                continue
        
        if signals:
            signals.progress.emit(f"阶段1完成，共处理 {len(first_pass_translations)} 条字幕，提取 {len(terminology_dict)} 个术语")
            signals.progress.emit(f"移除了 {removed_hi_count} 条字幕中的听障内容")
        
        # 检查是否有足够的翻译结果
        if len(first_pass_translations) < len(cleaned_subtitles) * 0.5:
            if signals:
                signals.error.emit(f"初步翻译不完整，仅获得 {len(first_pass_translations)}/{len(cleaned_subtitles)} 条翻译")
            return [], {}
        
        # 阶段2: 术语统一化和翻译反思
        if signals:
            signals.progress.emit("阶段2/3: 术语统一化和翻译反思...")
        
        # 整理术语表，合并重复项和近似术语
        normalized_terminology = {}
        if terminology_dict:
            # 添加用户自定义术语
            if config.custom_terminology:
                for source, target in config.custom_terminology.items():
                    terminology_dict[source] = target
                if signals:
                    signals.progress.emit(f"合并了 {len(config.custom_terminology)} 个用户自定义术语")
            
            # 将术语按长度降序排序（优先处理长术语）
            sorted_terms = sorted(terminology_dict.items(), key=lambda x: len(x[0]), reverse=True)
            
            # 统一术语翻译
            system_prompt = f"""你是一位{config.source_lang}到{config.target_lang}的专业术语专家。
请审核和改进以下从字幕中提取的术语表，确保术语翻译的准确性和一致性。
你需要:
1. 合并重复或相似的术语
2. 纠正不准确的翻译
3. 标准化术语的翻译方式
4. 删除不是真正术语的条目
"""

            terms_list = "\n".join([f"{source} | {target}" for source, target in sorted_terms])
            user_prompt = f"""请审核以下术语表:

{terms_list}

请返回改进后的术语表，格式为:
术语1 | 翻译1
术语2 | 翻译2
...
"""
            
            try:
                # 发送请求优化术语表
                async with aiohttp.ClientSession() as session:
                    headers = {
                        "Authorization": f"Bearer {config.api_key}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "model": config.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.2
                    }
                    
                    api_endpoint = f"{config.api_host}/v1/chat/completions"
                    
                    if signals:
                        signals.progress.emit(f"术语标准化API请求: {api_endpoint}")
                    
                    async with session.post(
                        api_endpoint,
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=60)
                    ) as response:
                        if response.status != 200:
                            if signals:
                                signals.error.emit(f"术语标准化API请求失败，状态码: {response.status}")
                            # 使用原始术语表作为备份
                            normalized_terminology = terminology_dict.copy()
                        else:
                            result = await response.json()
                            response_text = result["choices"][0]["message"]["content"]
                            
                            # 提取标准化的术语表
                            term_pattern = r'(.*?)\s*[\|丨]\s*(.*?)(?=\n|$)'
                            for term_match in re.finditer(term_pattern, response_text):
                                source_term = term_match.group(1).strip()
                                target_term = term_match.group(2).strip()
                                if source_term and target_term:
                                    normalized_terminology[source_term] = target_term
                            
                            if signals:
                                signals.progress.emit(f"术语标准化完成，共 {len(normalized_terminology)} 个术语")
            
            except Exception as e:
                error_message = f"术语标准化失败: {str(e)}"
                if signals:
                    signals.error.emit(error_message)
                # 使用原始术语表作为备份
                normalized_terminology = terminology_dict.copy()
        
        # 如果没有提取到术语，则创建一个空字典
        if not normalized_terminology:
            normalized_terminology = {}
        
        # 确保用户自定义术语的优先级最高
        if config.custom_terminology:
            for source, target in config.custom_terminology.items():
                normalized_terminology[source] = target
        
        # 阶段3: 最终翻译、分段优化和时间轴调整
        if signals:
            signals.progress.emit("阶段3/3: 最终翻译、分段优化和时间轴调整...")
        
        final_translations = []
        
        # 准备术语表提示词
        terminology_prompt = ""
        if normalized_terminology:
            terminology_prompt = "术语表参考（确保一致使用）:\n"
            for idx, (source, target) in enumerate(sorted(normalized_terminology.items(), key=lambda x: len(x[0]), reverse=True)[:30]):  # 限制数量
                terminology_prompt += f"{idx+1}. {source}: {target}\n"
        
        # 批量进行最终翻译
        FINAL_BATCH_SIZE = config.batch_size // 2  # 第三阶段减小批次大小，确保更精确的翻译
        
        for i in range(0, len(cleaned_subtitles), FINAL_BATCH_SIZE):
            batch = cleaned_subtitles[i:min(i + FINAL_BATCH_SIZE, len(cleaned_subtitles))]
            first_pass_batch = first_pass_translations[i:min(i + FINAL_BATCH_SIZE, len(first_pass_translations))]
            
            if signals:
                signals.progress.emit(f"最终翻译批次 {i//FINAL_BATCH_SIZE + 1}/{(len(cleaned_subtitles)+FINAL_BATCH_SIZE-1)//FINAL_BATCH_SIZE}")
            
            # 构建最终翻译请求
            system_prompt = f"""你是一位专业的{config.source_lang}到{config.target_lang}字幕翻译专家。
请对初步翻译的字幕进行优化和调整。

请遵循以下规则:
1. 保持翻译的准确性和流畅度
2. 确保每条字幕语义完整，长度适中（每行不超过42个字符）
3. 使用术语表中的标准翻译
4. 考虑时间轴信息，为每条字幕进行时间轴优化
5. 优化时间轴时，请确保每个句子显示时长与原字幕中一致，尽量与原字幕时间轴匹配，尤其是未合并也未拆分的句子时间轴应保持不变
6. 合并过短的字幕，拆分过长的字幕
7. 调整断句时，要将原文和译文联合考虑，使最终的原文和译文行数相同
8. 以结构化数据格式返回结果，包含原文、时间轴和翻译
9. 保留完整的原文内容，不要修改原文
10. 确保原文和翻译都包含在最终输出中
"""

            user_prompt = f"""请根据以下字幕的初步翻译和时间轴信息进行最终优化和调整。确保字幕语义完整、长度适中，且与原字幕时间轴匹配：

"""
            for idx, (sub, first_trans) in enumerate(zip(batch, first_pass_batch)):
                # 将timedelta转换为秒数
                start_seconds = sub['start'].total_seconds() if hasattr(sub['start'], 'total_seconds') else float(sub['start'])
                end_seconds = sub['end'].total_seconds() if hasattr(sub['end'], 'total_seconds') else float(sub['end'])
                duration = end_seconds - start_seconds
                
                time_info = f"{format_timecode(start_seconds)} --> {format_timecode(end_seconds)} (时长: {duration:,.2f}秒)"
                user_prompt += f"[{idx+1}] 原文: {sub['content']}\n时间轴: {time_info}\n初步翻译: [{idx+1}] {first_trans}\n\n"
            
            user_prompt += f"""
{terminology_prompt}

请以结构化格式返回结果，每个字幕包含四部分信息：编号、时间轴、原文和翻译。
格式如下：

#1#
TIME: 0:00:00.000 --> 0:00:00.000
ORIG: 原始文本1
TRANS: 翻译文本1

#2#
TIME: 0:00:00.000 --> 0:00:00.000
ORIG: 原始文本2
TRANS: 翻译文本2

... 依此类推 ...

严格按照这个格式，这样我们可以准确提取出每条字幕的完整信息。不要添加任何其他内容或解释。
"""
            
            try:
                
                
                # 发送最终翻译请求
                async with aiohttp.ClientSession() as session:
                    headers = {
                        "Authorization": f"Bearer {config.api_key}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "model": config.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.3  # 低温度以确保结果稳定
                    }
                    
                    api_endpoint = f"{config.api_host}/v1/chat/completions"
                    
                    async with session.post(
                        api_endpoint,
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=180)
                    ) as response:
                        if response.status != 200:
                            if signals:
                                signals.progress.emit(f"最终翻译API请求失败，状态码: {response.status}")
                            
                            # 使用初步翻译作为备份
                            final_translations.extend(first_pass_batch[:len(batch)])
                            continue
                            
                        result = await response.json()
                        response_text = result["choices"][0]["message"]["content"]
                        
                        
                        
                        # 使用正则表达式提取结构化信息
                        batch_translations = []
                        original_texts = []
                        time_infos = []
                        pattern = r'#(\d+)#\s*\nTIME:\s*(.*?)\s*\nORIG:\s*(.*?)\s*\nTRANS:\s*(.*?)(?=\n#\d+#|\Z)'
                        matches = list(re.finditer(pattern, response_text, re.DOTALL))
                        
                        if signals:
                            signals.progress.emit(f"从响应中找到 {len(matches)} 个结构化翻译块")
                        
                        # 创建与batch大小相同的空列表
                        batch_translations = [""] * len(batch)
                        batch_originals = [""] * len(batch)
                        batch_time_infos = [""] * len(batch)
                        
                        # 填充提取到的翻译
                        for match in matches:
                            idx = int(match.group(1)) - 1
                            if 0 <= idx < len(batch):
                                time_info = match.group(2).strip()
                                original = match.group(3).strip()
                                translation = match.group(4).strip()
                                batch_translations[idx] = translation
                                batch_originals[idx] = original
                                batch_time_infos[idx] = time_info
                                if signals:
                                    signals.progress.emit(f"提取到翻译 #{idx+1}: {translation[:20]}..." if len(translation) > 20 else f"提取到翻译 #{idx+1}: {translation}")
                            else:
                                if signals:
                                    signals.progress.emit(f"警告：找到索引为 {idx+1} 的翻译，但超出批次范围 {len(batch)}")
                        
                        # 检查空翻译
                        empty_count = sum(1 for t in batch_translations if not t)
                        if empty_count > 0 and signals:
                            signals.progress.emit(f"警告：有 {empty_count}/{len(batch_translations)} 条翻译为空")
                        
                        # 记录处理后的翻译到日志
                        
                        
                        # 将翻译结果添加到最终列表，包含原文、翻译和时间轴信息
                        for i, (trans, orig, time_info) in enumerate(zip(batch_translations, batch_originals, batch_time_infos)):
                            # 如果有空字段，使用原始数据填充
                            if not trans:
                                trans = first_pass_batch[i] if i < len(first_pass_batch) else ""
                            if not orig:
                                orig = batch[i]["content"] if i < len(batch) else ""
                            
                            # 组合为完整的信息条目
                            final_translations.append({
                                "translation": trans,
                                "original": orig,
                                "time_info": time_info
                            })
            
            except Exception as e:
                error_message = f"阶段3处理批次 {i//FINAL_BATCH_SIZE + 1} 失败: {str(e)}\n{traceback.format_exc()}"
                if signals:
                    signals.error.emit(error_message)
                # 使用初步翻译作为备份
                final_translations.extend(first_pass_batch[:len(batch)])
        
        # 确保翻译结果数量与字幕数量一致
        if len(final_translations) < len(cleaned_subtitles):
            if signals:
                signals.progress.emit(f"警告: 翻译结果数量 ({len(final_translations)}) 少于字幕数量 ({len(cleaned_subtitles)})")
            # 填充缺失的翻译
            for i in range(len(final_translations), len(cleaned_subtitles)):
                final_translations.append({
                    "translation": "",
                    "original": cleaned_subtitles[i]["content"],
                    "time_info": ""
                })
        elif len(final_translations) > len(cleaned_subtitles):
            if signals:
                signals.progress.emit(f"警告: 翻译结果数量 ({len(final_translations)}) 多于字幕数量 ({len(cleaned_subtitles)})")
            # 截断多余的翻译
            final_translations = final_translations[:len(cleaned_subtitles)]
        
        if signals:
            signals.progress.emit(f"多阶段翻译完成，共翻译 {len(final_translations)} 条字幕，提取 {len(normalized_terminology)} 个术语")
        
        return final_translations, normalized_terminology

    @staticmethod
    def _parse_optimized_subtitles(response_text: str, original_subs: List[dict]) -> List[dict]:
        """解析AI优化后的字幕分段结果"""
        # 初始化结果列表
        optimized_subs = []
        # 使用与原始字幕相同的索引创建映射
        original_indices = {sub['index']: sub for sub in original_subs}
        
        # 分割响应文本为单独的字幕块
        subtitle_blocks = re.split(r'\n\s*\n', response_text)
        
        for block in subtitle_blocks:
            if not block.strip():
                continue
                
            # 尝试提取索引
            index_match = re.match(r'\[(\d+)\]', block)
            if not index_match:
                continue
                
            try:
                index = int(index_match.group(1))
                if index not in original_indices:
                    continue
                    
                # 获取原始字幕信息
                original_sub = original_indices[index]
                
                # 提取内容（排除时间信息行）
                content_lines = []
                lines = block.strip().split('\n')
                
                # 跳过索引和时间信息行
                content_start = False
                for line in lines:
                    if '-->' in line or re.match(r'\[\d+\]', line):
                        continue
                    content_start = True
                    if content_start and line.strip():
                        content_lines.append(line.strip())
                
                # 组合内容
                content = '\n'.join(content_lines)
                
                # 创建新的字幕条目，保留原始时间信息
                optimized_sub = original_sub.copy()
                optimized_sub['content'] = content
                
                optimized_subs.append(optimized_sub)
            except Exception:
                continue
        
        # 如果解析结果不完整，使用原始字幕填充缺失部分
        if len(optimized_subs) < len(original_subs):
            processed_indices = {sub['index'] for sub in optimized_subs}
            for sub in original_subs:
                if sub['index'] not in processed_indices:
                    optimized_subs.append(sub)
                    
        # 按原始索引排序
        optimized_subs.sort(key=lambda x: x['index'])
        
        return optimized_subs

    @staticmethod
    def merge_similar_consecutive_subtitles(subtitles: List[dict], max_time_diff: float = 1.0) -> List[dict]:
        """合并内容完全相同且时间间隔小于指定值的连续字幕
        
        Args:
            subtitles: 字幕列表
            max_time_diff: 最大时间间隔（秒），默认为1.0秒
            
        Returns:
            合并后的字幕列表
        """
        if not subtitles or len(subtitles) < 2:
            return subtitles
            
        merged_subtitles = []
        i = 0
        
        while i < len(subtitles):
            current = subtitles[i]
            merged_sub = {
                "index": current["index"],
                "time_info": current["time_info"],
                "content": current["content"],
                "start": current["start"],
                "end": current["end"]
            }
            
            # 查看是否可以合并连续字幕
            next_index = i + 1
            while next_index < len(subtitles):
                next_sub = subtitles[next_index]
                
                # 计算时间差（下一个字幕的开始时间减去当前字幕的结束时间）
                # 转换为datetime.timedelta对象
                time_diff = (next_sub["start"] - merged_sub["end"]).total_seconds()
                
                # 检查内容是否相同且时间间隔小于阈值
                if (next_sub["content"].strip() == merged_sub["content"].strip() and
                    time_diff <= max_time_diff):
                    # 更新合并后字幕的结束时间
                    merged_sub["end"] = next_sub["end"]
                    merged_sub["time_info"] = f"{merged_sub['start']} --> {merged_sub['end']}"
                    next_index += 1
                else:
                    break
            
            # 添加合并后的字幕到结果列表
            merged_subtitles.append(merged_sub)
            
            # 跳过已合并的字幕
            i = next_index
        
        # 重新编号字幕
        for idx, sub in enumerate(merged_subtitles):
            sub["index"] = idx + 1
            
        return merged_subtitles

    @staticmethod
    def should_merge_subtitles(subs: List[dict]) -> bool:
        """判断一组字幕是否应该被合并
        
        检查字幕是否过短（单字/短词）且时间间隔很小
        
        Args:
            subs: 连续的字幕列表
            
        Returns:
            布尔值，表示是否应该合并
        """
        # 如果只有一个字幕，不需要合并
        if len(subs) <= 1:
            return False
            
        # 检查字幕是否都很短（例如，单字或短词）
        short_subtitle_threshold = 3  # 字符数少于此阈值的字幕被视为短字幕
        is_short = all(len(sub["content"].strip()) <= short_subtitle_threshold for sub in subs)
        
        if not is_short:
            return False
            
        # 检查时间间隔是否都很小
        max_time_interval = 0.5  # 秒
        for i in range(len(subs) - 1):
            time_diff = (subs[i+1]["start"] - subs[i]["end"]).total_seconds()
            if time_diff > max_time_interval:
                return False
                
        # 检查总时长是否在合理范围内（防止合并过多导致字幕过长）
        total_duration = (subs[-1]["end"] - subs[0]["start"]).total_seconds()
        if total_duration > 5.0:  # 不合并总时长超过5秒的字幕组
            return False
            
        return True

    @staticmethod
    def smart_merge_subtitles(subtitles: List[dict], max_word_per_sub: int = 25) -> List[dict]:
        """智能合并字幕，处理单字或短语分散在多个字幕中的情况
        
        此方法首先识别应该合并的短字幕组，然后将它们合并成一个
        语义完整的字幕，同时保留时间轴信息。
        
        Args:
            subtitles: 字幕列表
            max_word_per_sub: 每个字幕的最大词数，默认为25
            
        Returns:
            合并后的字幕列表
        """
        if not subtitles or len(subtitles) < 2:
            return subtitles
            
        result = []
        i = 0
        
        while i < len(subtitles):
            # 查找可能需要合并的连续字幕组
            j = i
            current_group = [subtitles[i]]
            
            while j + 1 < len(subtitles):
                next_sub = subtitles[j + 1]
                current_sub = current_group[-1]
                
                # 检查两个字幕之间的时间间隔
                time_diff = (next_sub["start"] - current_sub["end"]).total_seconds()
                
                # 如果时间间隔足够小，添加到当前组
                if time_diff <= 0.5:  # 使用较小的阈值以避免过度合并
                    current_group.append(next_sub)
                    j += 1
                else:
                    break
                    
            # 如果当前组只有一个字幕，或者不应该合并，则直接添加到结果
            if len(current_group) == 1 or not SubtitleProcessor.should_merge_subtitles(current_group):
                result.append(subtitles[i])
                i += 1
                continue
                
            # 合并当前组中的字幕
            merged_content = "".join(sub["content"].strip() for sub in current_group)
            
            # 检查合并后的内容是否过长
            if len(merged_content) > max_word_per_sub * 2:  # 每个字符平均算2个字节
                # 如果过长，只合并部分字幕
                mid_point = len(current_group) // 2
                first_half = current_group[:mid_point]
                second_half = current_group[mid_point:]
                
                # 递归处理两部分
                result.extend(SubtitleProcessor.smart_merge_subtitles(first_half, max_word_per_sub))
                result.extend(SubtitleProcessor.smart_merge_subtitles(second_half, max_word_per_sub))
            else:
                # 创建合并后的字幕
                merged_sub = {
                    "index": current_group[0]["index"],
                    "start": current_group[0]["start"],
                    "end": current_group[-1]["end"],
                    "content": merged_content,
                    "time_info": f"{current_group[0]['start']} --> {current_group[-1]['end']}"
                }
                result.append(merged_sub)
                
            # 跳过已处理的字幕
            i = j + 1
        
        # 重新编号字幕
        for idx, sub in enumerate(result):
            sub["index"] = idx + 1
            
        return result

    @staticmethod
    def balance_subtitle_length(subtitles: List[dict], min_chars: int = 10, max_chars: int = 42) -> List[dict]:
        """平衡字幕长度，拆分过长字幕，合并过短字幕
        
        按照Netflix标准，调整字幕长度，确保每行不超过max_chars个字符
        同时尽量保持语义完整性
        
        Args:
            subtitles: 字幕列表
            min_chars: 最小字符数，默认10
            max_chars: 最大字符数，默认42（Netflix标准）
            
        Returns:
            平衡后的字幕列表
        """
        if not subtitles:
            return []
            
        result = []
        
        for sub in subtitles:
            content = sub["content"].strip()
            
            # 如果字幕长度在合理范围内，直接添加
            if len(content) <= max_chars:
                result.append(sub.copy())
                continue
                
            # 需要拆分的过长字幕
            sentences = re.split(r'([。！？.!?]+)', content)
            # 重组句子（保留标点）
            sentences = [''.join(sentences[i:i+2]) for i in range(0, len(sentences), 2) if i < len(sentences)]
            
            if not sentences:  # 防止没有句子的情况
                sentences = [content]
                
            # 如果只有一个句子但超过最大长度，尝试按逗号拆分
            if len(sentences) == 1 and len(sentences[0]) > max_chars:
                comma_parts = re.split(r'([，,、]+)', sentences[0])
                # 重组（保留逗号）
                comma_parts = [''.join(comma_parts[i:i+2]) for i in range(0, len(comma_parts), 2) if i < len(comma_parts)]
                if comma_parts:
                    sentences = comma_parts
                    
            # 如果仍然只有一个部分但超过最大长度，按字符数强制拆分
            if len(sentences) == 1 and len(sentences[0]) > max_chars:
                parts = []
                current = sentences[0]
                while len(current) > max_chars:
                    # 尝试在空格处拆分
                    space_idx = current[:max_chars].rfind(' ')
                    if space_idx > 0:
                        parts.append(current[:space_idx].strip())
                        current = current[space_idx:].strip()
                    else:
                        # 无法在空格处拆分，按max_chars拆分
                        parts.append(current[:max_chars])
                        current = current[max_chars:]
                if current:
                    parts.append(current)
                sentences = parts
            
            # 重新组合句子，确保每个字幕长度不超过最大值
            current_content = ""
            start_time = sub["start"]
            
            for i, sentence in enumerate(sentences):
                # 检查sentence是否为空字符串
                if not sentence:
                    continue
                    
                if len(current_content) + len(sentence) <= max_chars:
                    if current_content:
                        # 使用安全的方式检查第一个字符是否为字母
                        current_content += " " if sentence and sentence[0].isalpha() else ""  # 仅对字母添加空格分隔
                    current_content += sentence
                else:
                    if current_content:  # 保存累积的内容
                        # 计算结束时间：按比例分配
                        # 避免除以零错误
                        if len(content) > 0:
                            progress = len(''.join(sentences[:i])) / len(content)
                        else:
                            progress = 0.5  # 默认中点
                            
                        duration = (sub["end"] - sub["start"]).total_seconds()
                        end_time = sub["start"] + timedelta(seconds=duration * progress)
                        
                        new_sub = sub.copy()
                        new_sub["content"] = current_content
                        new_sub["start"] = start_time
                        new_sub["end"] = end_time
                        new_sub["time_info"] = f"{start_time} --> {end_time}"
                        result.append(new_sub)
                        
                        # 为下一部分设置开始时间
                        start_time = end_time
                    
                    # 开始新的累积
                    current_content = sentence
            
            # 添加最后一部分
            if current_content:
                new_sub = sub.copy()
                new_sub["content"] = current_content
                new_sub["start"] = start_time
                new_sub["end"] = sub["end"]
                new_sub["time_info"] = f"{start_time} --> {sub['end']}"
                result.append(new_sub)
    
        # 重新编号字幕
        for idx, sub in enumerate(result):
            sub["index"] = idx + 1
        
        return result

    @staticmethod
    def serialize_for_json(obj):
        """将对象转换为可JSON序列化的格式"""
        if isinstance(obj, timedelta):
            return str(obj)
        elif isinstance(obj, dict):
            return {k: SubtitleProcessor.serialize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [SubtitleProcessor.serialize_for_json(item) for item in obj]
        else:
            return obj


class WorkerSignals(QObject):
    """工作线程的信号类"""
    progress = pyqtSignal(str)  # 进度信息
    error = pyqtSignal(str)     # 错误信息 
    finished = pyqtSignal()     # 完成信号


class TranslationWorker(QThread):
    """翻译线程，用于异步执行字幕翻译"""
    
    def __init__(self, config, parent=None):
        """初始化翻译线程"""
        super().__init__(parent)
        self.config = config
        self.should_stop = False  # 添加停止标志
        self.subtitles = []
        self.translations = []
        self.failed_indices = []
        self.custom_terminology = {}
        self.worker_signals = WorkerSignals()
        self.input_file = ""
        self.output_file = ""
        
    def stop_translation(self):
        """停止翻译过程"""
        self.should_stop = True
        self.worker_signals.progress.emit("正在停止翻译...")
        
        # 保存当前进度
        if hasattr(self, 'output_file') and self.output_file:
            try:
                cache_dir = os.path.dirname(self.output_file)
                cache_file = os.path.join(cache_dir, f".temp_translations_{int(time.time())}.json")
                
                # 保存当前翻译进度到缓存文件
                cache_data = {
                    "translations": self.translations,
                    "failed_indices": self.failed_indices,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "total": len(self.subtitles),
                    "completed": len(self.translations)
                }
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
                self.worker_signals.progress.emit(f"已保存翻译进度到临时文件: {cache_file}")
                
                # 尝试将临时文件复制到最终输出文件
                if os.path.exists(cache_file):
                    self.write_subtitles_from_cache(self.output_file, cache_file)
                    self.worker_signals.progress.emit(f"已将当前进度保存到最终文件: {self.output_file}")
            except Exception as e:
                self.worker_signals.error.emit(f"保存进度时出错: {str(e)}")
        
        # 确保线程停止
        self.terminate()
        self.worker_signals.finished.emit()
        
    async def run_async(self):
        """异步运行翻译过程"""
        try:
            # 读取配置
            source_lang = self.config.source_lang
            target_lang = self.config.target_lang
            
            # 确保custom_terminology被添加到配置中
            if hasattr(self, 'custom_terminology') and self.custom_terminology:
                self.config.custom_terminology = self.custom_terminology
                self.worker_signals.progress.emit(f"使用自定义术语表（{len(self.custom_terminology)}项）")
                
            # 显示配置信息
            self.worker_signals.progress.emit(f"翻译语言：{source_lang} → {target_lang}")
            self.worker_signals.progress.emit(f"使用模型：{self.config.model}")
            
            # 检查字幕是否为空
            if not self.subtitles:
                self.worker_signals.error.emit("没有可翻译的字幕内容")
                return
                
            # 创建缓存目录和缓存文件名
            if self.output_file:
                cache_dir = os.path.dirname(self.output_file)
                os.makedirs(cache_dir, exist_ok=True)
                cache_file = os.path.join(cache_dir, f".temp_translations_{int(time.time())}.json")
            else:
                self.worker_signals.error.emit("输出文件路径未指定")
                return
                
            # 检查是否已请求停止
            if self.should_stop:
                return
                
            # 初始化翻译状态
            self.translations = []
            self.failed_indices = []
            
            # 检查字幕列表
            if not self.subtitles:
                self.worker_signals.error.emit("没有找到有效的字幕内容进行翻译")
                return
                
            # 创建临时缓存文件
            cache_file = self.output_file + ".temp"
            
            # 显示配置信息
            self.worker_signals.progress.emit(f"使用模型: {self.config.model}")
            self.worker_signals.progress.emit(f"批次大小: {self.config.batch_size}")
            self.worker_signals.progress.emit(f"双语字幕: {'是' if self.config.show_original else '否'}")
            self.worker_signals.progress.emit(f"清理标点: {'是' if self.config.clean_punctuation else '否'}")
            self.worker_signals.progress.emit(f"多阶段翻译: {'是' if self.config.multi_phase else '否'}")
            
            # 创建缓存文件
            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'translations': [],
                        'failed_indices': [],
                        'total': len(self.subtitles)
                    }, f, ensure_ascii=False)
            except Exception as e:
                error_msg = f"创建缓存文件失败: {str(e)}"
                print(error_msg)  # 输出到控制台
                self.worker_signals.error.emit(error_msg)
                return
                
            # 根据配置选择翻译方式
            if self.config.multi_phase:
                # 多阶段翻译
                try:
                    translations, terminology_dict = await SubtitleProcessor.multi_phase_translate(
                        self.subtitles, self.config, self.worker_signals
                    )
                    if self.should_stop:
                        return
                    self.translations = translations
                except Exception as e:
                    error_msg = f"多阶段翻译失败: {str(e)}"
                    print(error_msg)  # 输出到控制台
                    if 'traceback' in globals():
                        error_msg += f"\n{traceback.format_exc()}"
                    self.worker_signals.error.emit(error_msg)
                    return
            else:
                # 单阶段翻译
                total_batches = (len(self.subtitles) + self.config.batch_size - 1) // self.config.batch_size
                current_batch = 0
                
                for i in range(0, len(self.subtitles), self.config.batch_size):
                    if self.should_stop:
                        self.worker_signals.progress.emit("检测到停止请求，正在终止翻译...")
                        return
                        
                    batch = self.subtitles[i:i + self.config.batch_size]
                    current_batch += 1
                    
                    # 更新进度
                    self.worker_signals.progress.emit(f"正在翻译第 {current_batch}/{total_batches} 批...")
                    
                    # 构建翻译请求
                    messages = self.construct_batch_translation_request(
                        [sub['content'] for sub in batch],
                        [sub['index'] for sub in batch],
                        self.config.source_lang,
                        self.config.target_lang,
                        self.config.netflix_style,
                        self.config.terminology_consistency
                    )
                    
                    try:
                        # 发送翻译请求
                        async with aiohttp.ClientSession() as session:
                            headers = {
                                "Authorization": f"Bearer {self.config.api_key}",
                                "Content-Type": "application/json"
                            }
                            payload = {
                                "model": self.config.model,
                                "messages": messages,
                                "temperature": self.config.temperature
                            }
                            
                            async with session.post(
                                    f"{self.config.api_host}/v1/chat/completions",
                                    headers=headers,
                                    json=payload,
                                    timeout=aiohttp.ClientTimeout(total=180)
                            ) as response:
                                if response.status != 200:
                                    self.worker_signals.error.emit(f"API请求失败，状态码: {response.status}")
                                    self.failed_indices.extend([sub['index'] for sub in batch])
                                    continue
                                    
                                result = await response.json()
                                if "choices" in result and result["choices"]:
                                    batch_translations = self.process_batch_translation_response(
                                        result["choices"][0]["message"]["content"],
                                        len(batch)
                                    )
                                    self.translations.extend(batch_translations)
                                    
                                    # 更新缓存
                                    try:
                                        with open(cache_file, 'r', encoding='utf-8') as f:
                                            cache_data = json.load(f)
                                        cache_data['translations'] = self.translations
                                        cache_data['failed_indices'] = self.failed_indices
                                        with open(cache_file, 'w', encoding='utf-8') as f:
                                            json.dump(cache_data, f, ensure_ascii=False)
                                    except Exception as e:
                                        self.worker_signals.error.emit(f"更新缓存文件失败: {str(e)}")
                                        
                    except Exception as e:
                        self.worker_signals.error.emit(f"翻译批次 {current_batch} 失败: {str(e)}")
                        self.failed_indices.extend([sub['index'] for sub in batch])
                        continue
                        
                    # 等待一段时间，避免API请求过快
                    if not self.should_stop:
                        await asyncio.sleep(self.config.delay)
                    else:
                        return
            
            # 重试失败的翻译
            if self.failed_indices and not self.should_stop:
                self.worker_signals.progress.emit(f"开始重试 {len(self.failed_indices)} 条失败的翻译...")
                await self.retry_failed_translations_with_cache(None, self.failed_indices, cache_file)
                
            # 保存最终结果
            if not self.should_stop:
                self.write_subtitles_from_cache(self.output_file, cache_file)
                
                # 清理临时文件
                try:
                    os.remove(cache_file)
                except:
                    pass
                    
                self.worker_signals.progress.emit("翻译完成！")
                
        except Exception as e:
            error_msg = f"翻译过程出错: {str(e)}"
            print(error_msg)  # 输出到控制台
            if 'traceback' in globals():
                error_msg += f"\n{traceback.format_exc()}"
            self.worker_signals.error.emit(error_msg)
            
        finally:
            self.worker_signals.finished.emit()
        
    def run(self):
        """运行翻译处理的主方法"""
        try:
            # 创建翻译处理对象
            translator = SubtitleProcessor()
            
            # 设置信号连接
            signals = WorkerSignals()
            signals.progress.connect(self.worker_signals.progress.emit)
            signals.error.connect(self.worker_signals.error.emit)
            
            # 如果设置了自定义术语，确保添加到配置中
            if hasattr(self, 'custom_terminology') and self.custom_terminology:
                self.config.custom_terminology = self.custom_terminology
                signals.progress.emit(f"使用自定义术语表（{len(self.custom_terminology)}项）")
            
            # 检查是否需要使用多阶段翻译
            if self.config.multi_phase:
                signals.progress.emit("使用多阶段翻译流程...")
                asyncio.run(self.process_with_multi_phase(translator, signals))
            else:
                signals.progress.emit("使用标准翻译流程...")
                asyncio.run(self.process_with_standard(translator, signals))
                
            # 发送完成信号
            self.worker_signals.finished.emit()
            
        except Exception as e:
            # 捕获并报告所有异常
            error_msg = f"翻译过程中发生错误: {str(e)}\n{traceback.format_exc()}"
            self.worker_signals.error.emit(error_msg)
            
            # 写入错误日志
            try:
                with open("error_log.txt", "a", encoding="utf-8") as f:
                    f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {error_msg}\n")
            except:
                pass
                
            # 发送完成信号
            self.worker_signals.finished.emit()
        
    def create_api_client(self):
        """创建API客户端"""
        try:
            api_key = self.config.get("api_key", "")
            api_host = self.config.get("api_host", "")
            model = self.config.get("model", "")
            
            # 更详细的检查和错误信息
            if not api_key:
                self.worker_signals.error.emit("错误: API密钥未设置")
                return None
                
            if not model:
                self.worker_signals.error.emit("错误: 模型名称未设置")
                return None
                
            if not api_host:
                self.worker_signals.error.emit("错误: API主机地址未设置")
                return None
                
            # 添加更多调试信息
            self.worker_signals.progress.emit(f"API配置: 主机={api_host}, 模型={model}")
            self.worker_signals.progress.emit(f"API密钥前5个字符: {api_key[:5]}...")
            
            # 验证API主机地址格式
            if not (api_host.startswith("http://") or api_host.startswith("https://")):
                self.worker_signals.progress.emit(f"警告: API主机地址不以http://或https://开头，尝试添加https://")
                api_host = f"https://{api_host}"
            
            # 移除API主机地址末尾的斜杠
            if api_host.endswith("/"):
                api_host = api_host[:-1]
                
            # 更新修正后的主机地址
            self.worker_signals.progress.emit(f"使用最终API主机地址: {api_host}")
            
            return APIClient(api_key, api_host, model)
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            self.worker_signals.error.emit(f"创建API客户端失败: {str(e)}\n{error_detail}")
            return None
            
    def translation_finished(self):
        """翻译完成处理"""
        self.worker_signals.finished.emit()
        
    def get_context_before(self, index, count=2):
        """获取当前字幕之前的上下文"""
        context = []
        for i in range(max(0, index - count), index):
            if i < len(self.subtitles):
                context.append(self.subtitles[i]["content"])
        return context
        
    def get_context_after(self, index, count=2):
        """获取当前字幕之后的上下文"""
        context = []
        for i in range(index + 1, min(len(self.subtitles), index + count + 1)):
            context.append(self.subtitles[i]["content"])
        return context
        
    def construct_translation_request(self, text, context_before, context_after, 
                                     source_lang, target_lang, netflix_style, terminology_consistency):
        """构建翻译请求"""
        system_prompt = f"""你是一个专业的{source_lang}到{target_lang}字幕翻译专家。请直接提供翻译结果，不要重复原文，不要添加任何前缀、解释或注释。
请尊重以下翻译规则:
1. 只翻译我提供的字幕文本，保持语义准确
2. 翻译要自然流畅，符合目标语言习惯，不要生硬直译
3. 保持术语一致性
4. 严格保留我提供的编号格式 [数字]
5. 只返回翻译后的文本，不要包含原文
6. 不要添加任何解释或注释
7. 不要添加"翻译："、"最终翻译："等前缀
"""

        # 提供上下文信息
        context_text = ""
        if context_before:
            context_text += f"上文字幕:\n{chr(10).join(context_before)}\n\n"
        if context_after:
            context_text += f"下文字幕:\n{chr(10).join(context_after)}\n\n"

        user_prompt = f"""请将以下字幕从{source_lang}翻译为{target_lang}:

需要翻译的字幕: "{text}"

{context_text}
请直接提供翻译结果，不要输出原文，不要添加"翻译："等前缀，不要有任何解释或注释，只输出翻译后的文本。"""
        
        return {
            "system_message": system_prompt,
            "user_message": user_prompt
        }
        
    def construct_batch_translation_request(self, texts, indices, source_lang, target_lang, 
                                          netflix_style, terminology_consistency):
        """构建批量翻译请求"""
        system_prompt = f"""你是一个专业的{source_lang}到{target_lang}字幕翻译专家。
请遵循以下翻译规则:
1. 只翻译提供的字幕文本，保持语义准确
2. 翻译要自然流畅，符合目标语言习惯，不要生硬直译
3. 保持术语一致性
4. 严格保留提供的编号格式 [数字]
5. 直接翻译，不要输出原文
6. 不要添加任何解释、注释或前缀
7. 不要出现"翻译："、"最终翻译"等文字
8. 不要输出"根据您提供的规则"、"以下是翻译结果"等任何引导性文字
9. 每个编号只对应一个翻译内容，不要混淆或重复编号
10. 严格按照原始编号顺序翻译，不要跳过或重复编号
11. 只输出翻译结果，不要有任何多余的文字
12. 不要输出"根据时间轴和字幕长度要求"等任何解释性文字
13. 只需直接输出格式为[编号] 翻译内容的结果，不需要任何其他内容
14. 禁止在翻译内容前添加任何形式的说明或解释
15. 即使是第一条翻译，也不要添加任何说明

输出格式示例（正确的）:
[1] 这是第一条翻译
[2] 这是第二条翻译

错误的输出示例:
根据您提供的规则，以下是翻译结果：
[1] 这是第一条翻译
[2] 这是第二条翻译
"""
        
        # 构建用户提示词
        formatted_texts = []
        for idx, text in zip(indices, texts):
            formatted_texts.append(f"[{idx+1}] {text}")
        
        batch_text = "\n".join(formatted_texts)
        
        user_prompt = f"""请将以下{source_lang}字幕批量翻译为{target_lang}:

{batch_text}

请注意:
1. 直接翻译，不要输出原文
2. 严格保持[数字]格式
3. 不要添加任何解释或注释
4. 不要输出"翻译："、"最终翻译"等任何前缀
5. 不要输出"根据您提供的规则"等任何引导性文字
6. 只输出翻译结果，不要有任何其他内容

直接以下列格式返回结果:
[1] 翻译内容1
[2] 翻译内容2
...
"""
        
        return {
            "system_message": system_prompt,
            "user_message": user_prompt
        }
        
    def process_translation_response(self, response):
        """处理单条翻译响应，清理格式并提取翻译内容"""
        if not response:
            return ""

        # 首先检查是否是常见的说明性文本模式
        if self.is_common_error_response(response):
            self.worker_signals.progress.emit("检测到说明性文本模式，尝试提取有效翻译内容")
            
            # 尝试查找可能的分隔点，如空行、数字标记等
            lines = response.split('\n')
            
            # 如果有多行，查找第一个符合条件的行
            for line_idx, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                    
                # 检查这一行是否包含过多中文字符（说明性内容）
                chinese_count = self.count_chinese_chars(line)
                # 检查这一行是否是正常的翻译内容（15字以内或者包含标记）
                if chinese_count <= 25 or re.match(r'^\[\d+\]|\d+[\.\:、]', line):
                    # 从这一行开始截取
                    response = '\n'.join(lines[line_idx:])
                    self.worker_signals.progress.emit(f"从第{line_idx+1}行开始截取有效内容")
                    break
    
        # 清理常见前缀
        cleaned = self.clean_llm_response(response)
        
        # 再次检查结果是否合理
        if cleaned:
            # 按行检查每一行是否合理
            lines = cleaned.split('\n')
            valid_lines = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # 检查这一行是否包含过多中文字符
                chinese_count = self.count_chinese_chars(line)
                
                # 如果单行超过15个中文字符，可能是说明内容
                if chinese_count > 25 and not re.match(r'^\[\d+\]|\d+[\.\:、]', line):
                    self.worker_signals.progress.emit(f"检测到过长行: {line[:25]}... ({chinese_count}字)")
                    # 尝试提取有效内容
                    valid_content = self.extract_valid_translation(line)
                    if valid_content:
                        valid_lines.append(valid_content)
                else:
                    valid_lines.append(line)
            
            # 重新组合有效行
            if valid_lines:
                cleaned = '\n'.join(valid_lines)
            elif len(lines) > 0:
                # 如果没有有效行，但有原始行，使用首行
                cleaned = lines[0]
                
                # 如果首行仍然过长，截断它
                chinese_count = self.count_chinese_chars(cleaned)
                if chinese_count > 25:
                    cleaned = self.truncate_chinese_text(cleaned, 25)
        
        return cleaned.strip()

    def extract_valid_translation(self, text):
        """从长文本中提取有效的翻译内容"""
        if not text:
            return ""
        
        # 方法1: 尝试通过冒号或引号分隔
        for pattern in [r'[:：](.+)$', r'["""」』』](.*?)["""」』』]']:
            match = re.search(pattern, text)
            if match:
                extracted = match.group(1).strip()
                chinese_count = self.count_chinese_chars(extracted)
                if 1 <= chinese_count <= 25:
                    return extracted
        
        # 方法2: 尝试查找第一个句号或逗号，取其后内容
        for sep in ['。', '，', '.', ',']:
            parts = text.split(sep, 1)
            if len(parts) > 1:
                second_part = parts[1].strip()
                chinese_count = self.count_chinese_chars(second_part)
                if 1 <= chinese_count <= 25:
                    return second_part
        
        # 方法3: 如果仍然没找到，尝试截断
        return self.truncate_chinese_text(text, 25)

    def truncate_chinese_text(self, text, max_chars):
        """智能截断中文文本到指定字符数"""
        if not text:
            return ""
        
        # 统计中文字符
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        if len(chinese_chars) <= max_chars:
            return text
        
        # 找到第N个中文字符的位置
        count = 0
        cut_pos = 0
        for i, char in enumerate(text):
            if '\u4e00' <= char <= '\u9fff':
                count += 1
            if count == max_chars:
                cut_pos = i + 1
                break
        
        if cut_pos > 0:
            # 尝试找到合适的断句点
            for i in range(cut_pos, max(0, cut_pos-5), -1):
                if i < len(text) and text[i] in ['。', '，', '.', ',', '!', '?', '；', ';']:
                    return text[:i+1]
        
        # 如果没找到合适的断句点，直接截断并添加省略号
        return text[:cut_pos] + "..."
    
    def process_batch_translation_response(self, response, expected_count):
        """处理批量翻译响应，分离多条翻译结果"""
        if not response:
            return []
        
        # 首先检查响应是否包含说明性文本
        if self.is_common_error_response(response):
            self.worker_signals.progress.emit("检测到批量响应中包含说明性文本模式")
            
        # 第一步：强制跳过第一个编号前的所有内容
        # 查找第一个编号标记，包括[1]、1.、Translation 1:等格式
        first_marker_patterns = [
            r'(^|\n)\s*\[\s*1\s*\]',  # [1] 格式
            r'(^|\n)\s*1[\.。:：、]',  # 1. 格式
            r'(^|\n)\s*Translation\s+1\s*:',  # Translation 1: 格式
            r'(^|\n)\s*翻译\s*1\s*[\.。:：、]'  # 翻译1: 格式
        ]
            
        # 尝试每种模式来查找第一个编号标记
        start_pos = -1
        for pattern in first_marker_patterns:
            match = re.search(pattern, response)
            if match:
                # 找到匹配项，记录位置
                start_pos = match.start()
                if match.group(1):  # 如果捕获到换行符
                    start_pos += 1  # 调整位置跳过换行符
                break
                
        # 如果找到了第一个编号标记
        if start_pos >= 0:
            if start_pos > 0:
                self.worker_signals.progress.emit(f"删除第一个编号标记[1]前的所有内容（{start_pos}个字符）")
                # 从第一个编号标记开始截取
                response = response[start_pos:]
        else:
            # 没有找到编号标记，尝试查找任何数字编号
            any_number_match = re.search(r'(^|\n)\s*\d+\s*[\.\]\):：、]', response)
            if any_number_match:
                start_pos = any_number_match.start()
                if any_number_match.group(1):  # 如果捕获到换行符
                    start_pos += 1  # 调整位置跳过换行符
                if start_pos > 0:
                    self.worker_signals.progress.emit(f"删除第一个数字编号前的所有内容（{start_pos}个字符）")
                    response = response[start_pos:]
    
        # 尝试通过编号分隔翻译结果
        translations = []
        
        # 定义多种可能的分隔模式，按优先级排序
        patterns = [
            r'\[\s*(\d+)\s*\]\s*(.*?)(?=\[\s*\d+\s*\]|\Z)',  # [1] 翻译内容
            r'^\s*(\d+)[\.。:：、]\s*(.*?)(?=^\s*\d+[\.。:：、]|\Z)',  # 1. 翻译内容
            r'(^|\n)\s*Translation\s+(\d+)\s*:\s*(.*?)(?=(^|\n)\s*Translation\s+\d+\s*:|\Z)',  # Translation 1: 翻译内容
            r'(^|\n)\s*翻译\s*(\d+)\s*[\.。:：、]\s*(.*?)(?=(^|\n)\s*翻译\s*\d+\s*[\.。:：、]|\Z)'  # 翻译1: 翻译内容
        ]
        
        # 尝试每种模式
        for pattern in patterns:
            matches = list(re.finditer(pattern, response, re.MULTILINE | re.DOTALL))
            if matches:
                for match in matches:
                    if pattern.startswith(r'^\s*(\d+)'):
                        # 对于第二种模式，组索引不同
                        index = int(match.group(1))
                        content = match.group(2).strip()
                    elif pattern.startswith(r'(^|\n)\s*Translation'):
                        # 对于第三种模式
                        index = int(match.group(2))
                        content = match.group(3).strip()
                    elif pattern.startswith(r'(^|\n)\s*翻译'):
                        # 对于第四种模式
                        index = int(match.group(2))
                        content = match.group(3).strip()
                    else:
                        # 对于第一种模式
                        index = int(match.group(1))
                        content = match.group(2).strip()
                    
                    # 确保索引有效
                    while len(translations) < index:
                        translations.append("")
                    
                    # 进一步清理翻译内容
                    cleaned_content = self.clean_translation_content(content)
                    
                    # 检查是否合规
                    chinese_count = self.count_chinese_chars(cleaned_content)
                    
                    # 特别处理第一条翻译，因为它最容易包含说明性文本
                    if index == 1 and chinese_count > 25 and not '\n' in cleaned_content:
                        self.worker_signals.progress.emit(f"第一条翻译疑似包含说明性文本 ({chinese_count}字)")
                        # 应用更严格的过滤规则
                        if re.search(r'根据|翻译|调整|优化|确保|保持|字幕|提供|以下是|这是|按照|参考', cleaned_content[:25]):
                            self.worker_signals.progress.emit("检测到常见说明性文本特征，尝试提取有效内容")
                            cleaned_content = self.extract_valid_translation(cleaned_content)
                            # 如果还是过长，尝试使用更简洁的内容
                            if self.count_chinese_chars(cleaned_content) > 25:
                                original_match = re.search(r'原文[""]?(.*?)[""]?$', content)
                                if original_match:
                                    cleaned_content = original_match.group(1).strip()
                                    self.worker_signals.progress.emit(f"使用简洁提取内容: {cleaned_content}")
                    # 检查其他翻译
                    elif chinese_count > 25 and not '\n' in cleaned_content:
                        self.worker_signals.progress.emit(f"翻译 {index} 疑似包含非翻译内容 ({chinese_count}字)")
                        # 提取有效内容
                        cleaned_content = self.extract_valid_translation(cleaned_content)
                    
                    # 额外检查，确保不是说明
                    if self.is_explanation_text(cleaned_content):
                        self.worker_signals.progress.emit(f"翻译 {index} 仍然包含说明性文本，尝试深度清理")
                        # 应用深度清理
                        cleaned_content = self.deep_clean_explanation(cleaned_content)
                    
                    # 更新翻译列表
                    if index > 0 and index <= len(translations):
                        translations[index-1] = cleaned_content
                    elif index == len(translations) + 1:
                        translations.append(cleaned_content)
                
                # 如果找到了匹配项，跳出循环
                if translations:
                    break
    
        # 如果没有找到匹配项，尝试按行分割
        if not translations:
            self.worker_signals.progress.emit("未找到编号标记，尝试按行分割翻译")
            lines = response.split('\n')
            valid_lines = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # 检查行是否包含过多中文字符
                chinese_count = self.count_chinese_chars(line)
                
                # 不考虑非常长的行作为翻译内容
                if chinese_count > 30:
                    self.worker_signals.progress.emit(f"跳过过长行: {line[:20]}... ({chinese_count}字)")
                    continue
                    
                # 跳过可能的说明性文本
                if self.is_explanation_text(line):
                    self.worker_signals.progress.emit(f"跳过说明性行: {line[:20]}...")
                    continue
                    
                # 清理行内容
                cleaned_line = self.clean_translation_content(line)
                if cleaned_line:
                    valid_lines.append(cleaned_line)
            
            # 使用有效行作为翻译
            translations = valid_lines
        
        # 确保返回足够数量的翻译结果
        while len(translations) < expected_count:
            translations.append("")
        
        # 如果返回了过多结果，截断到预期数量
        if len(translations) > expected_count:
            translations = translations[:expected_count]
        
        # 最后对每个翻译再次应用clean_llm_response清理
        for i in range(len(translations)):
            if translations[i]:
                translations[i] = self.clean_llm_response(translations[i])
            
            # 最终检查：确保没有常见的说明性文本特征
            if i == 0 and len(translations[i]) > 30:
                # 对第一条翻译进行特别严格的检查
                if re.search(r'(根据|按照|如下|以下|这是).{0,10}(翻译|优化|调整)', translations[i]):
                    self.worker_signals.progress.emit(f"最终检查：第一条翻译仍含说明性文本，尝试截断")
                    # 尝试找到冒号后的内容
                    colon_match = re.search(r'[:：].{0,5}(.{1,25})', translations[i])
                    if colon_match:
                        translations[i] = colon_match.group(1).strip()
                    else:
                        # 或者简单截断为15个字符
                        translations[i] = self.truncate_chinese_text(translations[i], 25)
    
        return translations

    def clean_translation_content(self, content):
        """清理单条翻译内容"""
        if not content:
            return ""
        
        # 移除常见的前缀
        content = re.sub(r'^(翻译|译文|Translation)\s*[:：]', '', content).strip()
        
        # 移除引号
        content = re.sub(r'^["""「『』」""\'\'\']+|["""「『』」""\'\'\']+$', '', content).strip()
        
        # 移除可能的注释
        content = re.sub(r'\(.*?\)|\[.*?\]', '', content).strip()
        
        return content

    def clean_llm_response(self, response):
        """清理LLM响应，移除前缀和格式化噪音"""
        if not response:
            return ""
        
        # 优先检查并移除"根据时间轴和字幕长度要求"这类特定解释性文本
        time_pattern = r'^[\s\n]*根据时间轴和字幕长度要求[^，。\n]*[，。]?'
        response = re.sub(time_pattern, '', response, flags=re.DOTALL)
        
        # 移除常见的前缀，扩展匹配模式以涵盖更多情况
        prefixes = [
            r'^[\s\n]*最终翻译[\s\n]*',
            r'^[\s\n]*翻译结果[:：][\s\n]*',
            r'^[\s\n]*最终译文[:：][\s\n]*',
            r'^[\s\n]*译文[:：][\s\n]*',
            r'^[\s\n]*Translation:[\s\n]*',
            r'^[\s\n]*最终字幕[\s\n]*',
            r'^[\s\n]*Translated subtitle:[\s\n]*',
            r'^[\s\n]*优化后的翻译[:：][\s\n]*',
            r'^[\s\n]*修正后的翻译[:：][\s\n]*',
            r'^[\s\n]*字幕翻译[:：][\s\n]*',
            r'^[\s\n]*Final translation:[\s\n]*',
            r'^[\s\n]*以下是(最终)?(的)?翻译(结果)?[:：]?[\s\n]*',
            r'^[\s\n]*以下是(最终)?(的)?译文[:：]?[\s\n]*',
            r'^[\s\n]*这是(最终)?(的)?翻译(结果)?[:：]?[\s\n]*',
            r'^[\s\n]*这是(最终)?(的)?译文[:：]?[\s\n]*',
            r'^[\s\n]*下面是(最终)?(的)?翻译(结果)?[:：]?[\s\n]*',
            r'^[\s\n]*Here is the translation:[\s\n]*',
            r'^[\s\n]*Here is the subtitle:[\s\n]*',
            r'^[\s\n]*The optimized translation:[\s\n]*',
            r'^[\s\n]*根据(您|你)(提供的)?(规则|要求).*?(我|以下是)?.*?翻译(结果)?[:：]?[\s\n]*',
            r'^[\s\n]*(根据|按照|遵循).*?(要求|规则|标准).{0,50}(翻译|优化|调整)(结果)?[:：]?[\s\n]*',
            r'^[\s\n]*(我已|我已经|我对|我将).{0,30}(翻译|优化|调整).{0,50}[:：]?[\s\n]*',
            r'^[\s\n]*(以下|如下|下面)(是|为).{0,20}(翻译|结果|译文)([:：])?[\s\n]*',
            r'^[\s\n]*(确保|保持).{0,30}(语义|字幕|翻译).{0,50}[:：]?[\s\n]*',
        ]
        
        # 应用所有前缀模式
        for prefix in prefixes:
            response = re.sub(prefix, '', response, flags=re.IGNORECASE | re.DOTALL)
        
        # 移除可能的注释或说明
        response = re.sub(r'\(注:.*?\)', '', response)
        response = re.sub(r'\[注:.*?\]', '', response)
        
        # 移除以"根据..."开头的整句
        response = re.sub(r'^[\s\n]*根据[^。\n]+。', '', response)
        
        # 清理多余的空白字符
        response = re.sub(r'\s+', ' ', response).strip()
        
        return response.strip()

    def count_chinese_chars(self, text):
        """计算文本中的中文字符数量"""
        if not text:
            return 0
        # 使用Unicode范围匹配中文字符
        chinese_char_count = len(re.findall(r'[\u4e00-\u9fff]', text))
        return chinese_char_count
        
    async def retry_failed_translations(self, api_client):
        """重试失败的翻译"""
        if not self.failed_indices:
            return
            
        self.worker_signals.progress.emit(f"重试 {len(self.failed_indices)} 条失败的翻译...")
        
        for idx in self.failed_indices[:]:
            if self.should_stop:
                self.worker_signals.progress.emit("翻译重试已手动停止")
                break
                
            self.worker_signals.progress.emit(f"重试字幕 {idx + 1}/{len(self.subtitles)}...")
            
            # 获取上下文
            context_before = self.get_context_before(idx, 2)
            context_after = self.get_context_after(idx, 2)
            
            # 获取原始文本
            text = self.subtitles[idx]["content"]
            
            # 应用自定义术语表替换
            original_text = text
            for term, translation in self.custom_terminology.items():
                pattern = r'\b' + re.escape(term) + r'\b'
                text = re.sub(pattern, f"[{term}|{translation}]", text, flags=re.IGNORECASE)
            
            if original_text != text:
                self.worker_signals.progress.emit(f"重试时应用了自定义术语表到字幕 {idx + 1}")
            
            # 构建请求
            prompt = self.construct_translation_request(
                text,
                context_before,
                context_after,
                self.config.get("source_language", "英语"),
                self.config.get("target_language", "中文"),
                True,  # netflix_style always enabled
                True   # terminology_consistency always enabled
            )
            
            # 重试3次
            success = False
            for attempt in range(3):
                try:
                    response = await api_client.chat(prompt)
                    translation = self.process_translation_response(response)
                    
                    # 保存翻译结果
                    self.translations[idx] = translation
                    self.failed_indices.remove(idx)
                    
                    success = True
                    break
                    
                except Exception as e:
                    if attempt < 2:
                        self.worker_signals.progress.emit(f"重试出错，再次尝试 ({attempt+1}/3): {str(e)}")
                        await asyncio.sleep(2)
                    else:
                        self.worker_signals.progress.emit(f"重试失败 ({attempt+1}/3): {str(e)}")
                        
            if success:
                self.worker_signals.progress.emit(f"字幕 {idx + 1} 重试成功")
            else:
                self.worker_signals.progress.emit(f"字幕 {idx + 1} 重试失败，将在最终结果中跳过")
                
            # 延迟
            if self.config.get("request_delay", 1.0) > 0:
                delay = self.config.get("request_delay", 1.0)
                await asyncio.sleep(delay)
                
        self.worker_signals.progress.emit(f"重试完成，还有 {len(self.failed_indices)} 条翻译失败")
        
    def write_subtitles(self, output_file):
        """写入翻译后的字幕文件 - 这是为了向后兼容，实际使用write_subtitles_from_cache"""
        self.worker_signals.progress.emit("错误：应使用write_subtitles_from_cache方法")
        return False
        
    async def backup_translation_state(self, backup_path):
        """备份当前翻译状态 - 这是为了向后兼容，实际由缓存系统处理"""
        self.worker_signals.progress.emit("错误：备份由缓存系统自动处理")
        return False

    async def test_api_connection(self):
        """测试API连接是否正常"""
        self.worker_signals.progress.emit("测试API连接...")
        
        try:
            api_client = self.create_api_client()
            if not api_client:
                self.worker_signals.error.emit("无法创建API客户端")
                return False
                
            # 使用一个简单的测试消息
            test_message = "Hello, please respond with 'API connection successful'"
            response = await api_client.chat(test_message)
            
            self.worker_signals.progress.emit(f"API测试响应: {response}")
            
            if "success" in response.lower() or "成功" in response:
                self.worker_signals.progress.emit("API连接测试成功!")
                return True
            else:
                self.worker_signals.progress.emit("API连接测试返回了意外响应，但连接似乎正常")
                return True
                
        except Exception as e:
            self.worker_signals.error.emit(f"API连接测试失败: {str(e)}")
            return False
            
    async def translate_subtitles(self, subtitles, output_file, backup_path=None):
        """翻译字幕并保存结果"""
        try:
            # 初始化翻译状态
            self.subtitles = subtitles
            self.translations = [""] * len(subtitles)
            self.failed_indices = []
            
            # 创建临时缓存文件路径
            cache_dir = os.path.dirname(output_file)
            cache_file = os.path.join(cache_dir, f".temp_translations_{int(time.time())}.json")
            self.worker_signals.progress.emit(f"将使用缓存文件: {cache_file}")
            
            # 显示当前配置信息
            self.worker_signals.progress.emit(f"批处理大小: {self.config.batch_size}")
            self.worker_signals.progress.emit(f"双语字幕: {'启用' if self.config.get('show_original', False) else '禁用'}")
            self.worker_signals.progress.emit(f"清理标点: {'启用' if self.config.get('clean_punctuation', False) else '禁用'}")
            self.worker_signals.progress.emit(f"多阶段翻译: {'启用' if self.config.get('multi_phase', False) else '禁用'}")
            
            # 初始化缓存数据结构
            cache_data = {
                "translations": [""] * len(subtitles),
                "failed_indices": [],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 保存初始缓存文件
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            # 创建API客户端
            api_client = self.create_api_client()
            if not api_client:
                self.worker_signals.error.emit("无法创建API客户端")
                return False
                
            # 测试API连接
            if not await self.test_api_connection():
                self.worker_signals.error.emit("API连接测试失败，请检查API密钥和网络连接")
                return False
            
            # 检查是否使用多阶段翻译
            if self.config.get("multi_phase", False):
                self.worker_signals.progress.emit("使用多阶段翻译流程...")
                translations, terminology_dict = await SubtitleProcessor.multi_phase_translate(
                    subtitles, 
                    self.config, 
                    self.worker_signals
                )
                
                # 检查是否有空翻译
                empty_translations = sum(1 for t in translations if (isinstance(t, dict) and not t.get("translation", "").strip()) or (isinstance(t, str) and not t.strip()))
                if empty_translations > 0:
                    self.worker_signals.progress.emit(f"警告: 发现 {empty_translations} 条空翻译，尝试修复...")
                    
                # 更新翻译结果
                self.translations = translations
                
                # 更新缓存文件
                try:
                    # 读取当前缓存
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    
                    # 更新翻译结果，使用serialize_for_json防止序列化错误
                    cache_data["translations"] = SubtitleProcessor.serialize_for_json(translations)
                    
                    # 保存更新后的缓存
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump(cache_data, f, ensure_ascii=False, indent=2)
                    
                    self.worker_signals.progress.emit("已将多阶段翻译结果保存到缓存文件")
                except Exception as e:
                    self.worker_signals.error.emit(f"更新缓存文件失败: {str(e)}")
                
                # 检查是否需要重试失败的翻译
                if self.failed_indices and not self.should_stop:
                    self.worker_signals.progress.emit("开始重试失败的翻译...")
                    await self.retry_failed_translations_with_cache(api_client, self.failed_indices, cache_file)
                
                # 写入最终结果
                self.write_subtitles_from_cache(output_file, cache_file)
                
                return True
            else:
                # 单阶段翻译
                batch_size = self.config.get("batch_size", 40)
                total_batches = (len(subtitles) + batch_size - 1) // batch_size
                current_batch = 0
                
                # 处理每个批次
                for i in range(0, len(subtitles), batch_size):
                    if self.should_stop:
                        self.worker_signals.progress.emit("检测到停止请求，正在终止翻译...")
                        break
                        
                    current_batch += 1
                    batch_indices = list(range(i, min(i + batch_size, len(subtitles))))
                    batch_subs = [subtitles[idx] for idx in batch_indices]
                    
                    # 进度更新
                    progress_msg = f"正在翻译第 {current_batch}/{total_batches} 批, "
                    progress_msg += f"字幕 {batch_indices[0] + 1}-{batch_indices[-1] + 1}/{len(subtitles)}"
                    self.worker_signals.progress.emit(progress_msg)
                    
                    # 尝试翻译最多3次
                    batch_translations = []  # 当前批次的翻译结果
                    batch_failed = []  # 当前批次失败的索引
                    for attempt in range(3):
                        try:
                            batch_translations = []  # 当前批次的翻译结果
                            batch_failed = []  # 当前批次失败的索引
                            
                            if batch_size == 1:
                                # 单个字幕翻译
                                sub = batch_subs[0]
                                idx = batch_indices[0]
                                
                                # 构建上下文
                                context_before = self.get_context_before(idx, 2)
                                context_after = self.get_context_after(idx, 2)
                                
                                # 获取该字幕文本
                                text = sub['content']  # 正确访问字典属性
                                
                                # 应用自定义术语表替换
                                original_text = text
                                for term, translation in self.custom_terminology.items():
                                    pattern = r'\b' + re.escape(term) + r'\b'
                                    text = re.sub(pattern, f"[{term}|{translation}]", text, flags=re.IGNORECASE)
                                
                                if original_text != text:
                                    self.worker_signals.progress.emit(f"应用了自定义术语表到字幕 {idx + 1}")
                                
                                # 创建翻译请求
                                prompt = self.construct_translation_request(
                                    text, 
                                    context_before, 
                                    context_after,
                                    self.config.get("source_language", "英语"),
                                    self.config.get("target_language", "中文"),
                                    True,  # netflix_style always enabled
                                    True   # terminology_consistency always enabled
                                )
                                
                                # 发送请求
                                response = await api_client.chat(prompt)
                                
                                # 处理响应
                                translation = self.process_translation_response(response)
                                batch_translations.append(translation)
                                
                            else:
                                # 批量翻译
                                batch_texts = []
                                for sub_idx, sub in enumerate(batch_subs):
                                    # 应用自定义术语表替换
                                    text = sub['content']  # 正确访问字典属性
                                    original_text = text
                                    for term, translation in self.custom_terminology.items():
                                        pattern = r'\b' + re.escape(term) + r'\b'
                                        text = re.sub(pattern, f"[{term}|{translation}]", text, flags=re.IGNORECASE)
                                    
                                    if original_text != text:
                                        self.worker_signals.progress.emit(f"应用了自定义术语表到字幕 {batch_indices[sub_idx] + 1}")
                                    
                                    batch_texts.append(text)
                                    
                                # 创建批量翻译请求
                                prompt = self.construct_batch_translation_request(
                                    batch_texts,
                                    batch_indices,
                                    self.config.get("source_language", "英语"),
                                    self.config.get("target_language", "中文"),
                                    True,  # netflix_style always enabled
                                    True   # terminology_consistency always enabled
                                )
                                
                                # 发送请求
                                response = await api_client.chat(prompt)
                                
                                # 处理批量响应
                                batch_translations = self.process_batch_translation_response(response, len(batch_indices))
                            
                            # 翻译成功，跳出重试循环
                            break
                            
                        except Exception as e:
                            if attempt < 2:  # 如果还有重试机会
                                self.worker_signals.progress.emit(f"翻译出错，正在重试 ({attempt+1}/3): {str(e)}")
                                await asyncio.sleep(2)  # 等待2秒后重试
                            else:
                                self.worker_signals.progress.emit(f"翻译失败 ({attempt+1}/3): {str(e)}")
                                batch_failed = batch_indices  # 标记整个批次失败
                    
                    # 更新缓存文件
                    try:
                        # 读取当前缓存
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            cache_data = json.load(f)
                        
                        # 更新翻译结果
                        translations = cache_data["translations"]
                        for idx, trans_idx in enumerate(batch_indices):
                            if idx < len(batch_translations):
                                translations[trans_idx] = batch_translations[idx]
                            else:
                                cache_data["failed_indices"].append(trans_idx)
                        
                        # 添加失败的索引
                        for idx in batch_failed:
                            if idx not in cache_data["failed_indices"]:
                                cache_data["failed_indices"].append(idx)
                        
                        # 保存更新后的缓存
                        with open(cache_file, 'w', encoding='utf-8') as f:
                            json.dump(cache_data, f, ensure_ascii=False, indent=2)
                            
                        self.worker_signals.progress.emit(f"已更新翻译缓存文件")
                    except Exception as e:
                        self.worker_signals.error.emit(f"更新缓存文件失败: {str(e)}")
                    
                    # 检查延迟
                    if self.config.get("request_delay", 1.0) > 0:
                        delay = self.config.get("request_delay", 1.0)
                        self.worker_signals.progress.emit(f"等待 {delay} 秒后继续...")
                        await asyncio.sleep(delay)
                        
                    # 每完成5批次或最后一批次，备份当前状态
                    if backup_path and (current_batch % 5 == 0 or current_batch == total_batches):
                        try:
                            shutil.copy2(cache_file, backup_path)
                            self.worker_signals.progress.emit(f"已创建备份: {backup_path}")
                        except Exception as e:
                            self.worker_signals.progress.emit(f"创建备份时出错: {str(e)}")
            
                # 重试失败的翻译
                if not self.should_stop:
                    # 读取当前缓存
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    
                    # 获取失败的索引
                    failed_indices = cache_data["failed_indices"]
                    
                    if failed_indices:
                        await self.retry_failed_translations_with_cache(api_client, failed_indices, cache_file)
                    
                    # 写入最终结果
                    self.write_subtitles_from_cache(output_file, cache_file)
                    
                    # 清理缓存文件
                    try:
                        if os.path.exists(cache_file):
                            os.remove(cache_file)
                            self.worker_signals.progress.emit("已清理临时缓存文件")
                    except Exception as e:
                        self.worker_signals.progress.emit(f"清理缓存文件失败: {str(e)}")
                
                return True
                
        except Exception as e:
            import traceback
            self.worker_signals.error.emit(f"翻译过程异常: {str(e)}\n{traceback.format_exc()}")
            return False

    async def retry_failed_translations_with_cache(self, translator, failed_indices, cache_file):
        """重试失败的翻译并更新缓存"""
        if not failed_indices:
            return

        # 读取缓存文件
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
        except Exception as e:
            self.worker_signals.error.emit(f"读取缓存文件失败: {str(e)}")
            return

        # 获取失败的字幕
        failed_subtitles = []
        for idx in failed_indices:
            for sub in self.subtitles:
                if sub['index'] == idx:
                    failed_subtitles.append(sub)
                    break

        if not failed_subtitles:
            return

        # 设置重试次数
        max_retries = 3
        current_retry = 0
        remaining_indices = failed_indices.copy()

        while remaining_indices and current_retry < max_retries and not self.should_stop:
            current_retry += 1
            self.worker_signals.progress.emit(f"第 {current_retry} 次重试，剩余 {len(remaining_indices)} 条未翻译字幕")

            # 按批次重试
            batch_size = min(10, len(remaining_indices))  # 重试时使用较小的批次
            retry_failed = []

            for i in range(0, len(remaining_indices), batch_size):
                if self.should_stop:
                    return

                batch_indices = remaining_indices[i:i + batch_size]
                batch_subs = [sub for sub in failed_subtitles if sub['index'] in batch_indices]

                try:
                    # 构建翻译请求
                    messages = self.construct_batch_translation_request(
                        [sub['content'] for sub in batch_subs],
                        [sub['index'] for sub in batch_subs],
                        self.config.source_lang,
                        self.config.target_lang,
                        self.config.netflix_style,
                        self.config.terminology_consistency
                    )

                    # 发送翻译请求
                    async with aiohttp.ClientSession() as session:
                        headers = {
                            "Authorization": f"Bearer {self.config.api_key}",
                            "Content-Type": "application/json"
                        }
                        payload = {
                            "model": self.config.model,
                            "messages": messages,
                            "temperature": self.config.temperature
                        }

                        async with session.post(
                                f"{self.config.api_host}/v1/chat/completions",
                                headers=headers,
                                json=payload,
                                timeout=aiohttp.ClientTimeout(total=180)
                        ) as response:
                            if response.status != 200:
                                self.worker_signals.error.emit(f"重试请求失败，状态码: {response.status}")
                                retry_failed.extend(batch_indices)
                                continue

                            result = await response.json()
                            if "choices" in result and result["choices"]:
                                batch_translations = self.process_batch_translation_response(
                                    result["choices"][0]["message"]["content"],
                                    len(batch_subs)
                                )

                                # 更新翻译结果
                                for idx, trans in zip(batch_indices, batch_translations):
                                    if trans.strip():  # 只更新非空翻译
                                        # 查找原始索引位置
                                        original_idx = next(i for i, sub in enumerate(self.subtitles) if sub['index'] == idx)
                                        if original_idx < len(self.translations):
                                            self.translations[original_idx] = trans
                                    else:
                                        retry_failed.append(idx)

                                # 更新缓存
                                try:
                                    cache_data['translations'] = self.translations
                                    cache_data['failed_indices'] = retry_failed
                                    with open(cache_file, 'w', encoding='utf-8') as f:
                                        json.dump(cache_data, f, ensure_ascii=False)
                                except Exception as e:
                                    self.worker_signals.error.emit(f"更新缓存文件失败: {str(e)}")

                except Exception as e:
                    self.worker_signals.error.emit(f"重试批次失败: {str(e)}")
                    retry_failed.extend(batch_indices)
                    continue

                # 等待一段时间再进行下一次请求
                if not self.should_stop:
                    await asyncio.sleep(self.config.delay)
                else:
                    return

            # 更新剩余需要重试的索引
            remaining_indices = retry_failed

            if not remaining_indices:
                self.worker_signals.progress.emit("所有失败的翻译已重试成功！")
                break
            elif current_retry < max_retries:
                # 增加重试间隔，避免频繁请求
                await asyncio.sleep(self.config.delay * 2)

        if remaining_indices:
            self.worker_signals.error.emit(f"仍有 {len(remaining_indices)} 条字幕翻译失败，请检查日志并手动处理")
            self.failed_indices = remaining_indices
    
    def write_subtitles_from_cache(self, output_file, cache_file):
        """从缓存文件中读取并写入最终字幕文件"""
        try:
            # 检查文件是否存在
            if not os.path.exists(cache_file):
                self.worker_signals.error.emit(f"缓存文件不存在: {cache_file}")
                return False
                
            # 读取缓存文件
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                
            # 检查缓存数据结构
            if 'translations' not in cache_data:
                self.worker_signals.error.emit("缓存文件格式错误，缺少translations字段")
                return False
                
            # 获取翻译结果
            translations = cache_data['translations']
            
            # 如果没有翻译结果，尝试使用内存中的翻译
            if not translations and hasattr(self, 'translations'):
                self.worker_signals.progress.emit("缓存中没有翻译结果，使用内存中的翻译")
                translations = self.translations
                
            # 如果仍没有翻译结果，报错退出
            if not translations:
                self.worker_signals.error.emit("没有找到任何可用的翻译结果")
                return False
                
            # 读取原始字幕
            if hasattr(self, 'subtitles') and self.subtitles:
                subtitles = self.subtitles
            elif 'subtitles' in cache_data:
                subtitles = cache_data['subtitles']
            else:
                self.worker_signals.error.emit("找不到原始字幕数据")
                return False
                
            # 确保翻译数量与字幕数量匹配
            if len(translations) < len(subtitles):
                self.worker_signals.error.emit(f"警告：翻译数量({len(translations)})少于字幕数量({len(subtitles)})")
                # 补齐翻译
                translations.extend([""] * (len(subtitles) - len(translations)))
                
            # 创建输出目录
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # 预处理字幕翻译，应用字符数量过滤规则
            translated_subs = []
            empty_translation_count = 0
            identical_count = 0
            filtered_by_length_count = 0
            
            for i, sub in enumerate(subtitles):
                if i >= len(translations):
                    break
                    
                # 获取原文和翻译
                original_content = sub['content']
                
                # 处理新的字典格式，兼容旧格式
                if isinstance(translations[i], dict):
                    translation = translations[i].get("translation", "")
                    # 如果有原文，优先使用LLM返回的原文
                    if translations[i].get("original"):
                        original_content = translations[i].get("original")
                else:
                    translation = translations[i]
                
                # 应用字符数量检测
                if translation:
                    # 检查中文字符数
                    chinese_count = self.count_chinese_chars(translation)
                    
                    # 如果第一行超过15个汉字且没有换行，可能是非翻译内容
                    if chinese_count > 25 and not "\n" in translation:
                        self.worker_signals.progress.emit(f"字幕 {i+1} 疑似包含非翻译内容 ({chinese_count}字)")
                        
                        # 尝试分行处理
                        lines = translation.split('\n')
                        valid_translation = None
                        
                        for line in lines:
                            line = line.strip()
                            line_chinese_count = self.count_chinese_chars(line)
                            if 1 <= line_chinese_count <= 25:
                                valid_translation = line
                                break
                        
                        if valid_translation:
                            self.worker_signals.progress.emit(f"从字幕 {i+1} 中提取有效翻译: {valid_translation}")
                            translation = valid_translation
                        else:
                            # 如果没找到合适的行但长度仍超过15字，尝试截断
                            count = 0
                            cut_pos = 0
                            for j, char in enumerate(translation):
                                if '\u4e00' <= char <= '\u9fff':
                                    count += 1
                                if count == 25:
                                    cut_pos = j + 1
                                    break
                            
                            if cut_pos > 0:
                                translation = translation[:cut_pos] + "..."
                                self.worker_signals.progress.emit(f"截断过长翻译: {translation}")
                        
                        filtered_by_length_count += 1
                
                # 检查翻译结果有效性
                is_untranslated = False
                if not translation:
                    empty_translation_count += 1
                    translation = f"[未翻译] {original_content}"
                    is_untranslated = True
                elif translation.lower() == original_content.lower():
                    identical_count += 1
                    translation = f"[未翻译] {original_content}"
                    is_untranslated = True
                elif re.search(r'\[\s*未翻译\s*\]', translation):
                    # 已经被标记为未翻译，保持原样
                    is_untranslated = True
                elif self.is_common_error_response(translation):
                    # 检测到常见错误响应
                    self.worker_signals.progress.emit(f"字幕 {i+1} 检测到错误响应模式")
                    translation = f"[未翻译] {original_content}"
                    identical_count += 1
                    is_untranslated = True
                
                # 检查未翻译字幕：如果是未翻译且没有原文，则跳过此字幕
                if is_untranslated and not original_content.strip():
                    self.worker_signals.progress.emit(f"字幕 {i+1} 未翻译且无原文，已跳过")
                    continue
                
                # 决定内容格式
                if hasattr(self, 'config'):
                    # 获取配置选项
                    show_original = getattr(self.config, 'show_original', False)
                    clean_punct = getattr(self.config, 'clean_punctuation', False)
                    
                    # 先处理清理标点的问题
                    cleaned_translation = translation
                    cleaned_original = original_content
                    
                    if clean_punct:
                        # 如果启用了清理标点，在完成翻译后用空格替换标点符号
                        cleaned_translation = SubtitleProcessor.clean_punctuation(translation)
                        cleaned_original = SubtitleProcessor.clean_punctuation(original_content)
                        self.worker_signals.progress.emit(f"字幕 {i+1} 应用标点符号清理")
                    
                    # 再处理是否双语的问题
                    if show_original:
                        # 双语字幕模式
                        content = f"{cleaned_translation}\n{cleaned_original}"
                        self.worker_signals.progress.emit(f"字幕 {i+1} 使用双语模式")
                    else:
                        # 单语字幕模式
                        content = cleaned_translation
                else:
                    # 默认双语且不清理标点
                    content = f"{translation}\n{original_content}"
                
                # 创建字幕对象
                new_sub = srt.Subtitle(
                    index=sub['index'],
                    start=sub['start'],
                    end=sub['end'],
                    content=content
                )
                translated_subs.append(new_sub)
            
            # 在最终处理阶段过滤掉未翻译且无原文的字幕
            filtered_subs = []
            skipped_count = 0
            
            for sub in translated_subs:
                content = sub.content
                # 检查是否是未翻译的内容
                if "未翻译" in content:
                    # 对于双语字幕，需要检查每一行
                    lines = content.split('\n')
                    has_content = False
                    
                    for line in lines:
                        # 如果某一行不包含"[未翻译]"且有内容，则保留该字幕
                        if "未翻译" not in line and line.strip():
                            has_content = True
                            break
                        
                        # 如果包含"[未翻译]"，检查是否在未翻译标记后有内容
                        if "未翻译" in line:
                            remaining = line.replace("未翻译", "").strip()
                            if remaining:
                                has_content = True
                                break
                    
                    if not has_content:
                        self.worker_signals.progress.emit(f"字幕 {sub.index} 完全未翻译且无内容，已跳过")
                        skipped_count += 1
                        continue
                
                # 保留有内容的字幕
                filtered_subs.append(sub)
            
            # 更新序号
            for i, sub in enumerate(filtered_subs, 1):
                sub.index = i
            
            # 写入字幕文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(srt.compose(filtered_subs))
            
            # 打印统计信息
            self.worker_signals.progress.emit(f"字幕写入完成: {output_file}")
            self.worker_signals.progress.emit(f"字幕统计: 总计 {len(filtered_subs)} 条，空翻译 {empty_translation_count} 条，相同内容 {identical_count} 条，长度过滤 {filtered_by_length_count} 条，跳过 {skipped_count} 条")
            if hasattr(self, 'config'):
                self.worker_signals.progress.emit(f"配置: 双语字幕: {'启用' if getattr(self.config, 'show_original', False) else '禁用'}, 清理标点: {'启用' if getattr(self.config, 'clean_punctuation', False) else '禁用'}")
            
            return True
        
        except Exception as e:
            self.worker_signals.error.emit(f"写入字幕文件时出错: {str(e)}")
            traceback_info = traceback.format_exc()
            self.worker_signals.error.emit(traceback_info)
            return False

    def is_common_error_response(self, text):
        """检测常见的错误响应模式"""
        if not text:
            return False
            
        # 检查开头是否为常见的错误响应模式
        common_error_patterns = [
            r'^[\s\n]*(根据要求|根据您的要求|遵循规则|遵循您的规则|按照规则)[，,\s\n]',
            r'^[\s\n]*(我已|已经|现已)[对将把].*?(进行了|完成了|做了)[优校调修][整改善化]',
            r'^[\s\n]*这(是|里是)[修优校调]正[后的]*译文',
            r'^[\s\n]*Translation:',
            r'^[\s\n]*以下是[优修校][化正对]后的[字翻译]幕',
        ]
        
        for pattern in common_error_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False

    def add_custom_terminology(self, terminology_dict):
        """添加用户自定义术语字典
        
        Args:
            terminology_dict: 包含术语和翻译的字典，格式为 {原文术语: 翻译术语}
        """
        if not terminology_dict:
            return
            
        if not hasattr(self, 'custom_terminology'):
            self.custom_terminology = {}
            
        # 合并术语字典
        self.custom_terminology.update(terminology_dict)
        
        # 确保配置中也包含自定义术语
        if hasattr(self.config, 'custom_terminology'):
            self.config.custom_terminology = self.custom_terminology
        else:
            # 如果配置中没有custom_terminology属性，可能是旧版本的配置类
            setattr(self.config, 'custom_terminology', self.custom_terminology)
            
        self.worker_signals.progress.emit(f"已添加 {len(terminology_dict)} 项用户自定义术语")
        
    def clear_custom_terminology(self):
        """清除所有用户自定义术语"""
        if hasattr(self, 'custom_terminology'):
            self.custom_terminology = {}
            
        if hasattr(self.config, 'custom_terminology'):
            self.config.custom_terminology = {}
            
        self.worker_signals.progress.emit("已清除所有用户自定义术语")

    async def process_with_multi_phase(self, translator, signals):
        """使用多阶段翻译流程处理字幕"""
        if not self.subtitles:
            signals.error.emit("没有可供翻译的字幕")
            return
            
        signals.progress.emit(f"开始多阶段翻译，共 {len(self.subtitles)} 条字幕...")
        
        try:
            # 测试API连接
            api_connection_successful = await self.test_api_connection()
            if not api_connection_successful:
                signals.error.emit("API连接测试失败，请检查API密钥和主机地址")
                return
                
            # 创建API客户端
            api_client = self.create_api_client()
            if not api_client:
                signals.error.emit("无法创建API客户端")
                return
                
            signals.progress.emit("API连接测试成功，开始多阶段翻译流程...")
            
            # 使用多阶段翻译处理
            translations, terminology_dict = await SubtitleProcessor.multi_phase_translate(
                self.subtitles, self.config, signals
            )
            
            if self.should_stop:
                signals.error.emit("翻译过程被用户中断")
                return
                
            # 处理空翻译等问题
            empty_translations = 0
            for i, t in enumerate(translations):
                if isinstance(t, dict):
                    if not t.get("translation", "").strip():
                        empty_translations += 1
                        # 使用原文作为备用
                        translations[i]["translation"] = f"[未翻译] {self.subtitles[i]['content']}"
                elif isinstance(t, str):
                    if not t.strip():
                        empty_translations += 1
                        # 使用原文作为备用
                        translations[i] = f"[未翻译] {self.subtitles[i]['content']}"
            
            if empty_translations > 0:
                signals.progress.emit(f"检测到 {empty_translations} 条空翻译，已使用原文替代")
            
            # 创建缓存文件
            cache_file = os.path.join(os.path.dirname(self.output_file), f".temp_translations_{int(time.time())}.json")
            
            # 保存缓存数据 - 使用序列化辅助函数解决timedelta不可序列化的问题
            cache_data = {
                "translations": SubtitleProcessor.serialize_for_json(translations),
                "subtitles": SubtitleProcessor.serialize_for_json(self.subtitles),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            signals.progress.emit(f"已将翻译结果保存到缓存文件: {cache_file}")
            
            # 将翻译结果存入实例变量
            self.translations = translations
            
            # 将自定义术语添加到实例中
            if terminology_dict:
                self.add_custom_terminology(terminology_dict)
            
            # 执行最终错误校正
            signals.progress.emit("开始执行最终错误校正...")
            error_correction_result = await self.final_error_correction(api_client)
            
            # 从缓存文件写入字幕文件
            if error_correction_result:
                # 更新缓存文件中的翻译
                cache_data = {
                    "translations": SubtitleProcessor.serialize_for_json(self.translations),
                    "subtitles": SubtitleProcessor.serialize_for_json(self.subtitles),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
                signals.progress.emit(f"已将错误校正后的翻译结果更新到缓存文件")
            
            # 写入字幕文件
            self.write_subtitles_from_cache(self.output_file, cache_file)
            
        except Exception as e:
            error_message = f"多阶段翻译过程中出错: {str(e)}\n{traceback.format_exc()}"
            signals.error.emit(error_message)

    async def process_with_standard(self, translator, signals):
        """使用标准翻译流程处理字幕"""
        if not self.subtitles:
            signals.error.emit("没有可供翻译的字幕")
            return
            
        signals.progress.emit(f"开始标准翻译，共 {len(self.subtitles)} 条字幕...")
        
        try:
            # 测试API连接
            api_connection_successful = await self.test_api_connection()
            if not api_connection_successful:
                signals.error.emit("API连接测试失败，请检查API密钥和主机地址")
                return
                
            # 创建API客户端
            api_client = self.create_api_client()
            if not api_client:
                signals.error.emit("无法创建API客户端")
                return
                
            signals.progress.emit("API连接测试成功，开始翻译...")
            
            # 初始化缓存
            cache_data = {
                "translations": {},
                "failed_indices": []
            }
            
            # 保存初始缓存数据
            cache_file = os.path.join(os.path.dirname(self.output_file), f".temp_translations_{int(time.time())}.json")
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            # 使用批量处理翻译
            batch_size = self.config.batch_size if hasattr(self.config, 'batch_size') else 40
            translations = []
            self.failed_indices = []
            
            for i in range(0, len(self.subtitles), batch_size):
                batch = self.subtitles[i:min(i + batch_size, len(self.subtitles))]
                batch_indices = list(range(i, min(i + batch_size, len(self.subtitles))))
                
                current_batch = i // batch_size + 1
                total_batches = (len(self.subtitles) + batch_size - 1) // batch_size
                
                signals.progress.emit(f"处理批次 {current_batch}/{total_batches}, 从 {i+1} 到 {i+len(batch)}")
                
                # 提取批次字幕内容，并移除听障字幕
                batch_texts = []
                for sub in batch:
                    # 先移除听障字幕内容再进行翻译
                    cleaned_content = SubtitleProcessor.remove_hearing_impaired(sub['content'])
                    batch_texts.append(cleaned_content)
                
                # 构建批量翻译请求
                request_data = self.construct_batch_translation_request(
                    batch_texts, 
                    batch_indices,
                    self.config.source_lang,
                    self.config.target_lang,
                    self.config.netflix_style,
                    self.config.terminology_consistency
                )
                
                # 创建请求对象
                request = {
                    "model": self.config.model,
                    "messages": [
                        {"role": "system", "content": request_data["system_message"]},
                        {"role": "user", "content": request_data["user_message"]}
                    ]
                }
                
                try:
                    # 发送API请求
                    api_endpoint = f"{self.config.api_host}/v1/chat/completions"
                    
                    headers = {
                        "Authorization": f"Bearer {self.config.api_key}",
                        "Content-Type": "application/json"
                    }
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            api_endpoint,
                            headers=headers,
                            json=request,
                            timeout=aiohttp.ClientTimeout(total=180)
                        ) as response:
                            if response.status == 200:
                                result = await response.json()
                                response_text = result["choices"][0]["message"]["content"]
                                
                                # 处理响应
                                batch_translations = self.process_batch_translation_response(
                                    response_text,
                                    len(batch)
                                )
                                
                                signals.progress.emit(f"批次 {current_batch} 翻译完成，成功处理 {len(batch_translations)} 条字幕")
                                
                                # 确保翻译结果数量与批次相符
                                if len(batch_translations) < len(batch):
                                    signals.error.emit(f"警告：批次 {current_batch} 翻译结果数量 ({len(batch_translations)}) 少于预期 ({len(batch)})")
                                    # 填充缺失的翻译
                                    for j in range(len(batch_translations), len(batch)):
                                        batch_translations.append("")
                                        self.failed_indices.append(i + j + 1)
                                
                                if len(batch_translations) > len(batch):
                                    signals.error.emit(f"警告：批次 {current_batch} 翻译结果数量 ({len(batch_translations)}) 多于预期 ({len(batch)})")
                                    batch_translations = batch_translations[:len(batch)]
                                
                                # 添加到整体翻译结果
                                translations.extend(batch_translations)
                                
                                # 更新缓存
                                with open(cache_file, 'r', encoding='utf-8') as f:
                                    cache_data = json.load(f)
                                
                                # 更新或添加翻译
                                for j, trans in enumerate(batch_translations):
                                    idx = i + j + 1  # 1-indexed
                                    cache_data['translations'][str(idx)] = trans
                                
                                # 更新失败索引
                                cache_data['failed_indices'] = self.failed_indices
                                
                                with open(cache_file, 'w', encoding='utf-8') as f:
                                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
                            else:
                                signals.error.emit(f"批次 {current_batch} API请求失败: {response.status}")
                                # 标记该批次的所有字幕为失败
                                self.failed_indices.extend([i + j + 1 for j in range(len(batch))])
                                # 添加空翻译结果
                                translations.extend([""] * len(batch))
                                
                except Exception as e:
                    signals.error.emit(f"批次 {current_batch} 处理失败: {str(e)}")
                    # 标记该批次的所有字幕为失败
                    self.failed_indices.extend([i + j + 1 for j in range(len(batch))])
                    # 添加空翻译结果
                    translations.extend([""] * len(batch))
                
                # 等待以避免API限制
                await asyncio.sleep(self.config.delay)
            
            # 使用翻译结果生成字幕文件
            if translations:
                # 将翻译结果存入实例变量
                self.translations = translations
                
                # 执行最终错误校正
                signals.progress.emit("开始执行最终错误校正...")
                error_correction_result = await self.final_error_correction(api_client)
                
                # 更新缓存数据以包含修复后的翻译
                if error_correction_result:
                    # 创建新的缓存数据包含修复后的翻译
                    new_cache_data = {
                        "translations": {},
                        "failed_indices": self.failed_indices
                    }
                    
                    # 将修复后的翻译添加到新的缓存
                    for i, trans in enumerate(self.translations):
                        new_cache_data["translations"][str(i+1)] = trans
                    
                    # 写入更新后的缓存
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump(new_cache_data, f, ensure_ascii=False, indent=2)
                    
                    signals.progress.emit("已更新缓存文件，包含错误校正后的翻译")
                
                # 生成翻译后的字幕
                translated_subs = []
                
                for i, sub in enumerate(self.subtitles):
                    if i >= len(self.translations):
                        signals.progress.emit(f"警告: 字幕 {i+1} 没有对应的翻译")
                        continue
                        
                    # 获取翻译文本
                    translation = self.translations[i]
                    
                    # 处理翻译文本
                    original_content = sub['content'].strip()
                    translation = translation.strip()
                    
                    # 检查是否有空翻译
                    if not translation or (i + 1) in self.failed_indices:
                        signals.progress.emit(f"警告: 字幕 {i+1} 翻译为空或失败")
                        # 使用原文作为备用
                        translation = f"[未翻译] {original_content}"
                    
                    # 检查翻译结果是否与原文完全相同
                    elif translation.lower() == original_content.lower():
                        signals.progress.emit(f"警告: 字幕 {i+1} 翻译结果与原文相同")
                        # 标记为未翻译
                        translation = f"[未翻译] {original_content}"
                    
                    # 根据配置决定是否显示原文
                    if self.config.get("show_original", False):
                        # 双语字幕模式
                        if self.config.get("clean_punctuation", False):
                            # 清理标点符号
                            original_text = SubtitleProcessor.clean_punctuation(original_content)
                            translated_text = SubtitleProcessor.clean_punctuation(translation)
                            content = f"{translated_text}\n{original_text}"
                        else:
                            # 保留原始标点
                            content = f"{translation}\n{original_content}"
                    else:
                        # 单语字幕模式
                        if self.config.get("clean_punctuation", False):
                            # 清理标点符号
                            content = SubtitleProcessor.clean_punctuation(translation)
                        else:
                            # 保留原始标点
                            content = translation
                    
                    # 创建新的字幕对象
                    new_sub = srt.Subtitle(
                        index=sub['index'],
                        start=sub['start'],
                        end=sub['end'],
                        content=content
                    )
                    translated_subs.append(new_sub)
                
                # 写入字幕文件
                with open(self.output_file, 'w', encoding='utf-8') as f:
                    f.write(srt.compose(translated_subs))
                
                signals.progress.emit(f"翻译完成，已生成译文文件: {self.output_file}")
                
                # 清理临时缓存文件
                try:
                    if os.path.exists(cache_file):
                        os.remove(cache_file)
                except:
                    pass
            else:
                signals.error.emit("翻译失败，未获得有效的翻译结果")
        
        except Exception as e:
            signals.error.emit(f"标准翻译过程中出错: {str(e)}\n{traceback.format_exc()}")

    async def final_review_phase(self, translator, signals):
        """最终审校阶段：逐条检查翻译与原文的对应关系并修正对齐问题"""
        if not hasattr(self, 'subtitles') or not hasattr(self, 'translations') or not self.subtitles or not self.translations:
            signals.error.emit("没有可用的字幕或翻译进行最终审校")
            return False
        
        signals.progress.emit("开始最终审校阶段...")
        
        try:
            # 创建API客户端
            api_client = translator.create_api_client()
            total_items = min(len(self.subtitles), len(self.translations))
            processed_count = 0
            improved_count = 0
            
            # 逐条检查并修正
            for i in range(total_items):
                if self.should_stop:
                    signals.progress.emit("检测到停止请求，正在终止审校...")
                    return False
                
                # 获取原文和译文
                original_sub = self.subtitles[i]
                translation = self.translations[i]
                
                # 跳过已标记为未翻译的条目
                if translation.startswith("[未翻译]"):
                    processed_count += 1
                    continue
                
                # 显示进度
                if i % 10 == 0 or i == total_items - 1:
                    signals.progress.emit(f"正在审校字幕 {i+1}/{total_items}...")
                
                # 构建审校请求
                request_data = self.construct_final_review_request(
                    {"original": original_sub['content'], "translation": translation},
                    i + 1,
                    self.config.source_lang,
                    self.config.target_lang
                )
                
                try:
                    # 发送API请求
                    review_response = translator.chat(
                        model=self.config.model,
                        messages=[
                            {"role": "system", "content": request_data["system_message"]},
                            {"role": "user", "content": request_data["user_message"]}
                        ]
                    )
                    
                    if review_response:
                        # 清理响应
                        cleaned_response = self.clean_llm_response(review_response)
                        
                        # 检查中文字符数量
                        chinese_count = self.count_chinese_chars(cleaned_response)
                        
                        # 应用15字规则检测是否为非翻译内容
                        if chinese_count > 25 and not "\n" in cleaned_response:
                            signals.progress.emit(f"字幕 {i+1} 审校结果疑似包含说明文本 ({chinese_count}字)")
                            lines = cleaned_response.split("\n")
                            
                            # 尝试找到合适长度的行
                            valid_translation = None
                            for line in lines:
                                line = line.strip()
                                line_chinese_count = self.count_chinese_chars(line)
                                if 1 <= line_chinese_count <= 25:
                                    valid_translation = line
                                    break
                            
                            # 如果找到合适的行，使用它
                            if valid_translation:
                                signals.progress.emit(f"从多行响应中提取有效翻译: {valid_translation}")
                                cleaned_response = valid_translation
                            else:
                                # 如果没找到合适的行但长度仍超过15字，尝试截断
                                chinese_chars = re.findall(r'[\u4e00-\u9fff]', cleaned_response)
                                if len(chinese_chars) > 25:
                                    count = 0
                                    cut_pos = 0
                                    for j, char in enumerate(cleaned_response):
                                        if '\u4e00' <= char <= '\u9fff':
                                            count += 1
                                        if count == 25:
                                            cut_pos = j + 1
                                            break
                                    
                                    if cut_pos > 0:
                                        cleaned_response = cleaned_response[:cut_pos] + "..."
                                        signals.progress.emit(f"截断过长翻译: {cleaned_response}")
                        
                        # 检查审校结果是否有效
                        if cleaned_response and cleaned_response != translation and not cleaned_response.startswith("[未翻译]"):
                            self.translations[i] = cleaned_response
                            improved_count += 1
                            signals.progress.emit(f"字幕 {i+1} 审校完成，已优化")
                    
                    # 更新处理计数
                    processed_count += 1
                    
                    # 添加延迟
                    if i < total_items - 1:
                        await asyncio.sleep(self.config.delay)
                    
                except Exception as e:
                    signals.error.emit(f"审校字幕 {i+1} 时出错: {str(e)}")
                    continue
            
            # 汇总结果
            signals.progress.emit(f"最终审校完成! 成功处理: {processed_count}, 优化翻译: {improved_count}")
            return True
            
        except Exception as e:
            signals.error.emit(f"最终审校过程中出错: {str(e)}\n{traceback.format_exc()}")
            return False

    def construct_final_review_request(self, translation_pair, index, source_lang, target_lang):
        """构建最终审校请求"""
        system_prompt = f"""你是一个专业的{source_lang}到{target_lang}字幕翻译专家。
请审校以下字幕的翻译质量，确保译文与原文在语义上完全对应。

遵循以下规则:
1. 直接给出修正后的翻译，不要添加任何解释或前缀
2. 每句字幕控制在25个汉字以内，保持简洁
3. 不要重复原文，只输出修正后的译文
4. 不要加入"最终翻译"、"译文："等任何前缀
5. 不要添加任何开场白、结束语或评论
6. 如果原译文已经很好，可以保持不变
7. 仅输出翻译结果，不要包含任何其他内容
返回结果不要有根据您提供的规则和要求，我对字幕进行了优化调整，确保时间轴匹配，语义完整且长度适中，以下是最终翻译结果。这样类似的内容。
正确示例：
翻译内容1
翻译内容2
……

错误示例：
根据您提供的规则和要求，我对字幕进行了优化调整，确保时间轴匹配，语义完整且长度适中，以下是最终翻译结果。
翻译内容1
翻译内容2
"""
        
        user_prompt = f"""审校这条字幕翻译 [{index}]:

原文: {translation_pair['original']}
当前译文: {translation_pair['translation']}

请直接返回最终修正后的译文，不要有任何解释或额外内容。"""
        
        return {
            "system_message": system_prompt,
            "user_message": user_prompt
        }

    def is_explanation_text(self, text):
        """检查文本是否为说明性文本"""
        if not text:
            return False
        
        # 说明性文本的特征
        explanation_patterns = [
            r'^(根据|按照|参考).{0,25}(要求|规则|标准)',
            r'^(这|以下|如下).{0,5}(是|为).{0,10}(翻译|结果)',
            r'(保持|确保).{0,25}(完整|一致|准确)',
            r'(为了|已经).{0,25}(优化|调整)',
            r'(我已|我对|我将).{0,25}(翻译|优化)',
            r'(字幕|翻译).{0,10}(质量|风格|特点)'
        ]
        
        # 检查是否匹配任何说明性模式
        for pattern in explanation_patterns:
            if re.search(pattern, text):
                return True
        
        # 检查说明性词语密度
        explanation_words = ["翻译", "优化", "调整", "确保", "保持", "遵循", "规则", 
                              "要求", "风格", "质量", "长度", "适中", "流畅", "准确", 
                              "语义", "字幕", "完整", "分段"]
        
        word_count = 0
        for word in explanation_words:
            if word in text:
                word_count += 1
        
        # 如果在前30个字符中出现超过3个说明性词语，可能是说明
        if word_count >= 3 and len(text) > 25:
            return True
        
        return False

    def deep_clean_explanation(self, text):
        """深度清理说明性文本，提取实际翻译内容"""
        if not text:
            return ""
        
        # 尝试通过冒号分割
        colon_parts = re.split(r'[:：]', text, 1)
        if len(colon_parts) > 1 and self.is_explanation_text(colon_parts[0]):
            # 冒号前是说明，取冒号后内容
            cleaned = colon_parts[1].strip()
            if cleaned and self.count_chinese_chars(cleaned) <= 25:
                return cleaned
        
        # 尝试找到引号内容
        quote_match = re.search(r'["""「」『』''\'\'](.*?)["""「」『』''\'\'"]', text)
        if quote_match:
            quoted = quote_match.group(1).strip()
            if quoted:
                return quoted
        
        # 尝试截断开头的说明性文本
        for i in range(len(text)):
            if i > 25 and not self.is_explanation_text(text[:i]):
                remaining = text[i:].strip()
                if remaining and self.count_chinese_chars(remaining) <= 25:
                    return remaining
        
        # 如果上述方法都不成功，截断文本
        return self.truncate_chinese_text(text, 25)

    async def final_error_correction(self, api_client):
        """最终错误校正阶段：检测并修复未翻译或异常的字幕"""
        self.worker_signals.progress.emit("开始最终错误校正阶段...")
        
        # 检查是否有字幕和翻译结果
        if not hasattr(self, 'subtitles') or not hasattr(self, 'translations') or not self.subtitles or not self.translations:
            self.worker_signals.error.emit("没有可用的字幕或翻译进行错误校正")
            return False
        
        try:
            # 找出需要修复的字幕索引
            problematic_indices = []
            total_subtitles = len(self.subtitles)
            batch_size = self.config.batch_size if hasattr(self.config, 'batch_size') else 40
            
            self.worker_signals.progress.emit(f"检查 {total_subtitles} 条字幕中的错误...")
            
            # 分批次检查字幕
            for i in range(0, total_subtitles, batch_size):
                if self.should_stop:
                    self.worker_signals.progress.emit("检测到停止请求，正在终止错误校正...")
                    return False
                    
                batch_end = min(i + batch_size, total_subtitles)
                self.worker_signals.progress.emit(f"检查第 {i+1}-{batch_end} 条字幕...")
                
                # 检查每一条字幕
                for j in range(i, batch_end):
                    if j >= len(self.translations):
                        continue
                        
                    translation = self.translations[j]
                    
                    # 检查是否包含"未翻译"或以#开头
                    if isinstance(translation, str):
                        if "未翻译" in translation or translation.strip().startswith("#"):
                            problematic_indices.append(j)
                    elif isinstance(translation, dict) and "translation" in translation:
                        if "未翻译" in translation["translation"] or translation["translation"].strip().startswith("#"):
                            problematic_indices.append(j)
            
            if not problematic_indices:
                self.worker_signals.progress.emit("未发现需要修复的错误字幕，最终校正阶段完成！")
                return True
                
            self.worker_signals.progress.emit(f"发现 {len(problematic_indices)} 条需要修复的字幕，开始修复...")
            
            # 对每个有问题的字幕进行修复
            fixed_count = 0
            for idx in problematic_indices:
                if self.should_stop:
                    self.worker_signals.progress.emit("检测到停止请求，正在终止错误修复...")
                    return False
                
                # 获取上下文（前后各10行字幕）
                context_start = max(0, idx - 10)
                context_end = min(total_subtitles, idx + 11)
                context_subtitles = self.subtitles[context_start:context_end]
                
                # 构建字幕格式
                subtitle_blocks = []
                for i, sub in enumerate(context_subtitles):
                    original_idx = context_start + i
                    
                    # 获取原文和当前翻译
                    original_content = sub['content']
                    
                    trans = self.translations[original_idx] if original_idx < len(self.translations) else ""
                    if isinstance(trans, dict):
                        current_translation = trans.get("translation", "")
                    else:
                        current_translation = trans
                    
                    # 格式化时间码
                    start_time = format_timecode(sub['start'].total_seconds())
                    end_time = format_timecode(sub['end'].total_seconds())
                    
                    # 创建字幕块
                    subtitle_block = f"{original_idx + 1}\n{start_time} --> {end_time}\n{current_translation}\n{original_content}\n"
                    subtitle_blocks.append(subtitle_block)
                
                subtitle_text = "\n".join(subtitle_blocks)
                
                # 构建系统提示和用户提示
                system_message = """你是一位专业的字幕翻译修复专家。
请修复以下字幕中存在问题的部分（标记为"未翻译"或以"#"开头的行）。

请遵循以下规则:
1. 只修改有问题的字幕行，如果有需要，有问题行的前后3行也可以进行修改调整以优化断句，但其他行应保持不变
2. 使用上下文理解内容，确保翻译的连贯性和准确性
3. 返回完整的修复后字幕块，包括未修改的行
4. 确保每条字幕格式与原格式一致
5. 如果是双语字幕（包含原文和译文），保持双语格式
6. 修复后的字幕应与上下文保持一致的语言风格
7. 确保时间轴信息正确（按照格式：小时:分钟:秒,毫秒）
8. 不要添加任何额外的解释、注释或前缀
9. 只返回修复后的字幕块，不要包含其他内容

必须严格按照以下格式返回结果:

<translation index="1">修复后的译文1</translation>
<translation index="2">修复后的译文2</translation>
...

注意事项：
- 只返回需要修复的字幕，不需要返回没有问题的字幕
- index是字幕的序号，应该与原字幕序号一致
- 不要添加任何额外的解释或注释，只返回XML标签包裹的翻译内容
- 不要包含时间轴信息或原文内容，只需要返回翻译文本
- 不要使用Markdown格式或其他标记语言"""

                user_message = f"""以下是需要检查和修复的字幕块（每个字幕块包含字幕序号、时间码、译文和原文）：

{subtitle_text}

请识别并修复含有"未翻译"字样或以"#"开头的字幕行。

仅输出修复后的字幕翻译结果，使用以下XML格式：
<translation index="字幕序号">修复后的译文</translation>

示例：
<translation index="1272">在争吵中对方</translation>
<translation index="1273">在争吵中</translation>

注意：
1. 只输出需要修复的字幕，不需要输出没有问题的字幕
2. 字幕序号必须与原字幕序号完全匹配
3. 不要包含任何解释、注释或其他内容
4. 不要输出时间轴信息或原文，只输出译文"""

                try:
                    # 发送请求
                    response = await api_client.chat(system_message + "\n\n" + user_message)
                    
                    # 解析响应，提取修复后的翻译
                    fixed_translations = self.parse_fixed_translations(response)
                    
                    if fixed_translations:
                        # 更新翻译结果
                        for fixed_idx, fixed_text in fixed_translations.items():
                            idx_num = int(fixed_idx) - 1  # 转换为0-based索引
                            
                            if idx_num < len(self.translations):
                                if isinstance(self.translations[idx_num], dict):
                                    self.translations[idx_num]["translation"] = fixed_text
                                else:
                                    self.translations[idx_num] = fixed_text
                                    
                                fixed_count += 1
                                self.worker_signals.progress.emit(f"已修复字幕 {fixed_idx}: {fixed_text}")
                    
                    # 等待一段时间再发送下一个请求
                    await asyncio.sleep(self.config.delay)
                    
                except Exception as e:
                    self.worker_signals.error.emit(f"修复字幕 {idx+1} 时出错: {str(e)}")
                    continue
            
            self.worker_signals.progress.emit(f"最终错误校正完成，共修复 {fixed_count} 条字幕！")
            return True
            
        except Exception as e:
            self.worker_signals.error.emit(f"最终错误校正过程中出错: {str(e)}")
            return False
    
    def parse_fixed_translations(self, response):
        """解析修复后的翻译响应"""
        fixed_translations = {}
        
        # 使用正则表达式匹配<translation index="数字">内容</translation>格式
        pattern = r'<translation index="(\d+)">(.*?)</translation>'
        matches = re.findall(pattern, response, re.DOTALL)
        
        for idx, text in matches:
            fixed_translations[idx] = text.strip()
        
        return fixed_translations


class TitleBarButton(QPushButton):
    """自定义标题栏按钮"""

    def __init__(self, color, hover_color, icon=None, size=30, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.color = color
        self.hover_color = hover_color
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border-radius: 15px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
        """)
        if icon:
            self.setIcon(QIcon(icon))


class AboutDialog(QWidget):
    """关于对话框"""

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self.setWindowTitle("关于")
        self.setFixedSize(480, 420)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        # 添加无边框属性
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 添加自定义标题栏
        title_bar = QFrame()
        title_bar.setStyleSheet("background-color: #262626;")
        title_bar.setFixedHeight(30)

        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)

        # 标题
        title_label = QLabel("关于")
        title_label.setStyleSheet("color: white; font-weight: bold;")

        # 关闭按钮
        close_btn = QPushButton("×")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF5F57;
                color: white;
                border: none;
                border-radius: 15px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #BF4542;
            }
        """)
        close_btn.clicked.connect(self.close)

        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(close_btn)

        main_layout.addWidget(title_bar)

        # 设置标题栏可拖动
        self.title_bar = title_bar
        self.title_bar.mousePressEvent = self.title_bar_mouse_press
        self.title_bar.mouseMoveEvent = self.title_bar_mouse_move
        self.title_bar.mouseReleaseEvent = self.title_bar_mouse_release
        self.dragging = False
        self.drag_start_position = None

        # 内容区域
        content_frame = QWidget()
        content_frame.setStyleSheet("background-color: white;")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(20, 20, 20, 20)

        # 应用标题
        title_label = QLabel("大模型字幕翻译小助手")
        title_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(title_label)

        # 版本
        version_label = QLabel("Version 2.0.1")
        version_label.setFont(QFont("Arial", 12))
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(version_label)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # 作者信息部分
        author_section = QLabel("作者信息")
        author_section.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        scroll_layout.addWidget(author_section)

        author_info = [
            "作者：NeymarBob",
            "微博&豆瓣&小红书&bilibili：NeymarBob",
            "公众号：鲍勃的小屋",
            "github：https://github.com/chwbob",
            "联系我：chwbob@163.com"
        ]

        for info in author_info:
            info_label = QLabel(info)
            scroll_layout.addWidget(info_label)

        # 描述
        desc_section = QLabel("应用描述")
        desc_section.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        scroll_layout.addSpacing(15)
        scroll_layout.addWidget(desc_section)

        desc = "一个使用AI进行字幕翻译的小助手，支持多种语言，使用大语言模型联系上下文提高翻译质量。模仿人类字幕组，使用粗翻+精校两阶段翻译优化断句和翻译质量"
        desc_label = QLabel(desc)
        desc_label.setWordWrap(True)
        scroll_layout.addWidget(desc_label)

        # 功能列表
        features_section = QLabel("主要功能:")
        features_section.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        scroll_layout.addSpacing(15)
        scroll_layout.addWidget(features_section)

        features = [
            "- 支持SRT格式字幕文件",
            "- 多种AI模型支持",
            "- 自定义翻译提示词",
            "- 批量翻译",
            "- 可选清理标点符号",
            "- 支持自定义并统一专有术语",
            "- 支持多阶段翻译，反思优化翻译效果",
            "- 支持记录失败结果重试"
        ]

        for feature in features:
            feature_label = QLabel(feature)
            scroll_layout.addWidget(feature_label)

        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        content_layout.addWidget(scroll_area)

        # 移除底部关闭按钮，只保留标题栏的关闭按钮

        main_layout.addWidget(content_frame)

    def title_bar_mouse_press(self, event):
        """处理标题栏鼠标按下事件，用于拖动窗口"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_start_position = event.pos()

    def title_bar_mouse_move(self, event):
        """处理标题栏鼠标移动事件，用于拖动窗口"""
        if self.dragging and self.drag_start_position:
            self.move(self.pos() + event.pos() - self.drag_start_position)

    def title_bar_mouse_release(self, event):
        """处理标题栏鼠标释放事件，用于拖动窗口"""
        self.dragging = False


class DonationDialog(QWidget):
    """捐赠对话框"""

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self.setWindowTitle("支持作者")
        self.setFixedSize(400, 450)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        # 添加无边框属性
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 添加自定义标题栏
        title_bar = QFrame()
        title_bar.setStyleSheet("background-color: #262626;")
        title_bar.setFixedHeight(30)

        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)

        # 标题
        title_label = QLabel("支持作者")
        title_label.setStyleSheet("color: white; font-weight: bold;")

        # 关闭按钮
        close_btn = QPushButton("×")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF5F57;
                color: white;
                border: none;
                border-radius: 15px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #BF4542;
            }
        """)
        close_btn.clicked.connect(self.close)

        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(close_btn)

        main_layout.addWidget(title_bar)

        # 设置标题栏可拖动
        self.title_bar = title_bar
        self.title_bar.mousePressEvent = self.title_bar_mouse_press
        self.title_bar.mouseMoveEvent = self.title_bar_mouse_move
        self.title_bar.mouseReleaseEvent = self.title_bar_mouse_release
        self.dragging = False
        self.drag_start_position = None

        # 内容区域
        content_frame = QWidget()
        content_frame.setStyleSheet("background-color: white;")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title_label = QLabel("支持作者")
        title_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(title_label)

        # 捐赠提示文字
        tip_label = QLabel("如果你喜欢这个软件，请鲍勃吃一个铜锣烧吧 😋")
        tip_label.setFont(QFont("Arial", 12))
        tip_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tip_label.setWordWrap(True)
        content_layout.addWidget(tip_label)

        # 添加捐赠图片
        img_path = resource_path(os.path.join('assets', 'AAA.jpg'))
        if os.path.exists(img_path):
            pixmap = QPixmap(img_path)
            # 确保图片不超过一定大小
            max_size = 300
            if pixmap.width() > max_size or pixmap.height() > max_size:
                pixmap = pixmap.scaled(max_size, max_size,
                                       Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)

            img_label = QLabel()
            img_label.setPixmap(pixmap)
            img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            content_layout.addWidget(img_label)
        else:
            no_img_label = QLabel("图片未找到")
            no_img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            content_layout.addWidget(no_img_label)

        content_layout.addStretch()

        # 移除底部关闭按钮，只保留标题栏的关闭按钮

        main_layout.addWidget(content_frame)

    def title_bar_mouse_press(self, event):
        """处理标题栏鼠标按下事件，用于拖动窗口"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_start_position = event.pos()

    def title_bar_mouse_move(self, event):
        """处理标题栏鼠标移动事件，用于拖动窗口"""
        if self.dragging and self.drag_start_position:
            self.move(self.pos() + event.pos() - self.drag_start_position)

    def title_bar_mouse_release(self, event):
        """处理标题栏鼠标释放事件，用于拖动窗口"""
        self.dragging = False


class SubtitleTranslatorApp(QMainWindow):
    """字幕翻译应用的主窗口类"""

    def __init__(self):
        super().__init__()
        self.model_list = ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "claude-3-opus", "claude-3-sonnet", "claude-3-haiku"]
        self.saved_config = self.load_saved_config()
        self.custom_terminology = self.load_custom_terminology()
        
        # 设置当前语言
        self.current_language = self.saved_config.get('interface_language', 'zh')
        
        self.setup_ui()
        self.translation_thread = None
        self.stop_requested = False
        
        # 设置窗口无边框
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 设置应用图标
        app_icon = QIcon(resource_path(os.path.join('assets', 'icon.ico')))
        self.setWindowIcon(app_icon)
        
        # 设置窗口初始大小和最小大小
        self.resize(900, 750)
        self.setMinimumSize(800, 600)
    
    def get_text(self, key):
        """获取当前语言的翻译文本"""
        try:
            return TRANSLATIONS[self.current_language][key]
        except (KeyError, TypeError):
            # 如果找不到当前语言的翻译，尝试使用中文
            try:
                return TRANSLATIONS["zh"][key]
            except (KeyError, TypeError):
                # 如果中文也没有，返回键名
                return key

    def set_language(self, language_code):
        """设置界面语言"""
        if language_code in SUPPORTED_LANGUAGES:
            self.current_language = language_code
            self.saved_config['interface_language'] = language_code
            self.save_config()
            return True
        return False
                
    def update_ui_language(self):
        """更新界面语言"""
        # 更新窗口标题
        self.setWindowTitle(self.get_text("app_title"))
        
        # 更新主要标签
        self.title_label.setText(self.get_text("app_title"))
        self.file_label.setText(self.get_text("source_file") + "：")
        self.output_label.setText(self.get_text("output_dir") + "：")
        self.output_dir_input.setPlaceholderText(self.get_text("default_output_dir"))
        
        # 更新选项卡标题
        self.tabs.setTabText(0, self.get_text("api_settings"))
        self.tabs.setTabText(1, self.get_text("translation_settings"))
        self.tabs.setTabText(2, self.get_text("system_settings"))
        
        # 更新API设置标签
        self.api_host_label.setText(self.get_text("api_host") + "：")
        self.api_key_label.setText(self.get_text("api_key") + "：")
        self.model_label.setText(self.get_text("model") + "：")
        self.toggle_key_btn.setText(self.get_text("show") if self.api_key_input.echoMode() == QLineEdit.EchoMode.Password else self.get_text("hide"))
        
        # 更新翻译设置标签
        self.source_lang_label.setText(self.get_text("source_lang") + "：")
        self.target_lang_label.setText(self.get_text("target_lang") + "：")
        self.temperature_label.setText(self.get_text("temperature") + "：")
        self.batch_size_label.setText(self.get_text("batch_size") + "：")
        self.delay_label.setText(self.get_text("request_delay") + "：")
        
        # 更新选项框文本
        self.show_original_checkbox.setText(self.get_text("show_original"))
        self.clean_punctuation_checkbox.setText(self.get_text("clean_punctuation"))
        self.multi_phase_checkbox.setText(self.get_text("multi_phase"))
        self.recovery_checkbox.setText(self.get_text("enable_recovery"))
        self.enable_batching_checkbox.setText(self.get_text("enable_batching"))
        
        # 更新按钮文本
        self.browse_button.setText(self.get_text("browse_file"))
        self.output_button.setText(self.get_text("browse_dir"))
        self.translate_button.setText(self.get_text("start_translation"))
        self.stop_button.setText(self.get_text("stop_translation"))
        self.save_config_button.setText(self.get_text("save_config"))
        self.about_button.setText(self.get_text("about"))
        self.donation_button.setText(self.get_text("donation"))
        self.terminology_button.setText(self.get_text("show_terminology"))
    
    # 修改setup_ui方法，添加系统设置选项卡
    def setup_ui(self):
        """设置用户界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === 自定义标题栏 ===
        title_bar = QFrame()
        title_bar.setStyleSheet(f"background-color: {COLOR_DARK};")
        title_bar.setFixedHeight(30)

        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)

        # 标题
        self.title_label = QLabel(self.get_text("app_title"))
        self.title_label.setStyleSheet(f"color: {COLOR_WHITE}; font-weight: bold;")

        # 控制按钮
        minimize_btn = TitleBarButton(COLOR_WARNING, "#BD8D21")
        minimize_btn.setText("－")
        minimize_btn.clicked.connect(self.showMinimized)

        maximize_btn = TitleBarButton("#4CD964", "#2A9D38") 
        maximize_btn.setText("□")
        maximize_btn.clicked.connect(self.toggle_maximize)

        close_btn = TitleBarButton("#FF5F57", "#BF4542")
        close_btn.setText("×")
        close_btn.clicked.connect(self.close)

        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        title_layout.addWidget(minimize_btn)
        title_layout.addWidget(maximize_btn)
        title_layout.addWidget(close_btn)

        main_layout.addWidget(title_bar)

        # 用于拖动窗口
        self.title_bar = title_bar
        self.title_bar.mousePressEvent = self.title_bar_mouse_press
        self.title_bar.mouseMoveEvent = self.title_bar_mouse_move
        self.title_bar.mouseReleaseEvent = self.title_bar_mouse_release
        self.dragging = False
        self.drag_start_position = None

        # === 内容区域 ===
        content_frame = QFrame()
        content_frame.setStyleSheet("background-color: #f5f5f5;")

        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(20, 20, 20, 20)

        # === 标题和版本 ===
        header_layout = QHBoxLayout()

        # 标题
        header_title = QLabel("大模型字幕翻译小助手")
        header_title.setFont(QFont("Arial", 18, QFont.Weight.Bold))

        # 版本
        version_label = QLabel("v2.0.1")
        version_label.setFont(QFont("Arial", 9))
        version_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        header_layout.addWidget(header_title)
        header_layout.addStretch()
        header_layout.addWidget(version_label)

        content_layout.addLayout(header_layout)

        # === 文件选择 ===
        file_layout = QHBoxLayout()

        file_label = QLabel("字幕源文件：")
        self.file_path_input = QLineEdit()
        self.file_path_input.setReadOnly(True)

        browse_button = QPushButton("打开文件")
        browse_button.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #0062CC;
            }
        """)
        browse_button.clicked.connect(self.browse_file)

        file_layout.addWidget(file_label)
        file_layout.addWidget(self.file_path_input, 1)
        file_layout.addWidget(browse_button)

        content_layout.addLayout(file_layout)
        content_layout.addSpacing(10)

        # 输出目录
        output_layout = QHBoxLayout()
        output_label = QLabel("输出目录：")
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setPlaceholderText("默认与输入文件同目录")
        self.output_dir_input.setReadOnly(True)

        output_button = QPushButton("选择目录")
        output_button.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #0062CC;
            }
        """)
        output_button.clicked.connect(self.browse_output_dir)

        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_dir_input, 1)
        output_layout.addWidget(output_button)

        content_layout.addLayout(output_layout)
        content_layout.addSpacing(15)

        # === 选项卡 ===
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #CCCCCC;
                background-color: white;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #E0E0E0;
                color: #505050;
                padding: 8px 12px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                color: #007AFF;
                font-weight: bold;
            }
            QTabBar::tab:hover:!selected {
                background-color: #CCCCCC;
            }
        """)

        # API 设置选项卡
        api_tab = QWidget()
        api_layout = QGridLayout(api_tab)
        api_layout.setContentsMargins(15, 15, 15, 15)

        # API Host
        api_layout.addWidget(QLabel("API地址："), 0, 0)
        self.api_host_input = QLineEdit(self.saved_config.get('api_host', "https://api.deepseek.com"))
        api_layout.addWidget(self.api_host_input, 0, 1, 1, 2)

        # API Key
        api_layout.addWidget(QLabel("API密钥："), 1, 0)
        self.api_key_input = QLineEdit(self.saved_config.get('api_key', ""))
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        api_layout.addWidget(self.api_key_input, 1, 1)

        # Toggle API Key visibility
        self.toggle_key_btn = QPushButton("显示")
        self.toggle_key_btn.clicked.connect(self.toggle_key_visibility)
        self.toggle_key_btn.setStyleSheet("""
            QPushButton {
                background-color: #E0E0E0;
                color: black;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #CCCCCC;
            }
        """)
        api_layout.addWidget(self.toggle_key_btn, 1, 2)

        # Model
        api_layout.addWidget(QLabel("模型："), 2, 0)
        self.model_input = QLineEdit(self.saved_config.get('model', "deepseek-chat"))
        api_layout.addWidget(self.model_input, 2, 1, 1, 2)

        tabs.addTab(api_tab, "API 设置")

        # 翻译设置选项卡
        trans_tab = QWidget()
        trans_layout = QGridLayout(trans_tab)
        trans_layout.setContentsMargins(15, 15, 15, 15)

        # 源语言和目标语言
        trans_layout.addWidget(QLabel("原文语言："), 0, 0)
        self.source_lang_input = QLineEdit(self.saved_config.get('source_lang', "en"))
        trans_layout.addWidget(self.source_lang_input, 0, 1)

        trans_layout.addWidget(QLabel("目标语言："), 0, 2)
        self.target_lang_input = QLineEdit(self.saved_config.get('target_lang', "zh"))
        trans_layout.addWidget(self.target_lang_input, 0, 3)

        # 温度设置
        temp_label = QLabel("温度：")
        temp_label.setToolTip("控制翻译结果的随机性。值越高，翻译结果越多样化但可能不够稳定；值越低，翻译结果越保守稳定。建议范围：0.0-1.0")
        trans_layout.addWidget(temp_label, 1, 0)
        self.temperature_input = QDoubleSpinBox()
        self.temperature_input.setRange(0.0, 2.0)
        self.temperature_input.setSingleStep(0.1)
        self.temperature_input.setValue(float(self.saved_config.get('temperature', 0.5)))
        self.temperature_input.setToolTip("控制翻译结果的随机性。值越高，翻译结果越多样化但可能不够稳定；值越低，翻译结果越保守稳定。建议范围：0.0-1.0")
        trans_layout.addWidget(self.temperature_input, 1, 1)

        # 批量处理大小
        trans_layout.addWidget(QLabel("批处理大小："), 1, 2)
        self.batch_size_input = QSpinBox()
        self.batch_size_input.setRange(1, 100)
        self.batch_size_input.setValue(int(self.saved_config.get('batch_size', 40)))
        trans_layout.addWidget(self.batch_size_input, 1, 3)

        # 请求之间的延迟
        delay_label = QLabel("请求延迟(秒)：")
        delay_label.setToolTip("两次API请求之间的等待时间。较长的延迟可以避免触发API限制，但会增加总翻译时间。建议范围：0.5-2.0秒")
        trans_layout.addWidget(delay_label, 2, 0)
        self.delay_input = QDoubleSpinBox()
        self.delay_input.setRange(0.0, 10.0)
        self.delay_input.setSingleStep(0.5)
        self.delay_input.setValue(float(self.saved_config.get('delay', 1.0)))
        self.delay_input.setToolTip("两次API请求之间的等待时间。较长的延迟可以避免触发API限制，但会增加总翻译时间。建议范围：0.5-2.0秒")
        trans_layout.addWidget(self.delay_input, 2, 1)

        # === Checkboxes ===
        options_frame = QFrame()
        options_frame.setStyleSheet("background-color: white; border-radius: 4px; padding: 10px;")
        options_layout = QHBoxLayout(options_frame)
        options_layout.setContentsMargins(20, 20, 20, 20)
        options_layout.setSpacing(30)  # 增加间距

        # 显示原文选项
        self.show_original_checkbox = QCheckBox("显示原文")
        self.show_original_checkbox.setStyleSheet("font-size: 14px; min-height: 30px;")
        self.show_original_checkbox.setChecked(self.saved_config.get('show_original', True))
        self.show_original_checkbox.setToolTip("启用后将在翻译结果中显示原文,组成双语字幕")
        options_layout.addWidget(self.show_original_checkbox)
        
        # 清理标点符号选项
        self.clean_punctuation_checkbox = QCheckBox("清理标点")
        self.clean_punctuation_checkbox.setStyleSheet("font-size: 14px; min-height: 30px;")
        self.clean_punctuation_checkbox.setChecked(self.saved_config.get('clean_punctuation', False))
        self.clean_punctuation_checkbox.setToolTip("启用后将清理翻译结果中的多余标点符号，使标点更符合目标语言习惯")
        options_layout.addWidget(self.clean_punctuation_checkbox)
        
        # 启用批处理选项
        self.enable_batching_checkbox = QCheckBox("启用批处理")
        self.enable_batching_checkbox.setStyleSheet("font-size: 14px; min-height: 30px;")
        self.enable_batching_checkbox.setChecked(self.saved_config.get('enable_batching', True))
        self.enable_batching_checkbox.setToolTip("启用批量处理，每次处理多条字幕")
        options_layout.addWidget(self.enable_batching_checkbox)
        
        # 多阶段翻译选项
        self.multi_phase_checkbox = QCheckBox("多阶段翻译")
        self.multi_phase_checkbox.setStyleSheet("font-size: 14px; min-height: 30px;")
        self.multi_phase_checkbox.setChecked(self.saved_config.get('multi_phase', False))
        self.multi_phase_checkbox.setToolTip("使用三阶段翻译流程：初译提取术语 -> 反思优化术语 -> 终译精校断句")
        options_layout.addWidget(self.multi_phase_checkbox)
        
        # 翻译失败恢复选项
        self.recovery_checkbox = QCheckBox("启用失败恢复")
        self.recovery_checkbox.setStyleSheet("font-size: 14px; min-height: 30px;")
        self.recovery_checkbox.setChecked(self.saved_config.get('recovery_enabled', False))
        self.recovery_checkbox.setToolTip("记录失败的翻译，方便后续重试")
        options_layout.addWidget(self.recovery_checkbox)

        # 添加水平拉伸
        options_layout.addStretch()

        trans_layout.addWidget(options_frame, 3, 0, 1, 4)
        
        # 额外提示词
        trans_layout.addWidget(QLabel("额外提示词："), 4, 0, 1, 4)
        self.additional_prompt_input = QTextEdit()
        self.additional_prompt_input.setPlaceholderText("输入额外提示词，帮助AI更好地理解和翻译字幕内容。比如：这是一部漫威电影...")
        self.additional_prompt_input.setMaximumHeight(80)
        trans_layout.addWidget(self.additional_prompt_input, 5, 0, 1, 4)

        tabs.addTab(trans_tab, "翻译设置")
        
        # 自定义术语选项卡
        terms_tab = QWidget()
        terms_layout = QVBoxLayout(terms_tab)
        terms_layout.setContentsMargins(15, 15, 15, 15)
        
        # 说明文字
        terms_label = QLabel("自定义术语列表可以指定特定词汇的翻译方式，例如人名、地名等专有名词。比如：Trump->懂王")
        terms_label.setWordWrap(True)
        terms_layout.addWidget(terms_label)
        
        # 术语编辑区
        terms_frame = QFrame()
        terms_frame.setStyleSheet("background-color: white; border-radius: 4px;")
        terms_frame_layout = QVBoxLayout(terms_frame)
        
        # 创建表格
        self.terms_table = QTableWidget()
        self.terms_table.setColumnCount(2)
        self.terms_table.setHorizontalHeaderLabels(["原文", "译文"])
        self.terms_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.terms_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.terms_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: #E0E0E0;
                border: 1px solid #CCCCCC;
            }
            QHeaderView::section {
                background-color: #F0F0F0;
                padding: 6px;
                border: 1px solid #CCCCCC;
                font-weight: bold;
            }
        """)
        
        # 填充术语数据
        self.populate_terminology_table()
        
        terms_frame_layout.addWidget(self.terms_table)
        
        # 添加术语按钮区域
        terms_buttons_layout = QHBoxLayout()
        
        add_term_btn = QPushButton("添加术语")
        add_term_btn.clicked.connect(self.add_terminology_item)
        add_term_btn.setStyleSheet("""
            QPushButton {
                background-color: #34C759;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #2A9F48;
            }
        """)
        
        remove_term_btn = QPushButton("删除术语")
        remove_term_btn.clicked.connect(self.remove_terminology_item)
        remove_term_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF3B30;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #D63030;
            }
        """)
        
        save_term_btn = QPushButton("保存术语列表")
        save_term_btn.clicked.connect(self.save_terminology_table)
        save_term_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #0062CC;
            }
        """)
        
        terms_buttons_layout.addWidget(add_term_btn)
        terms_buttons_layout.addWidget(remove_term_btn)
        terms_buttons_layout.addStretch()
        terms_buttons_layout.addWidget(save_term_btn)
        
        terms_frame_layout.addLayout(terms_buttons_layout)
        terms_layout.addWidget(terms_frame)
        
        tabs.addTab(terms_tab, "术语定制")

        content_layout.addWidget(tabs)
        content_layout.addSpacing(10)

        # === 日志区域 ===
        log_frame = QFrame()
        log_frame.setStyleSheet("background-color: white; border-radius: 4px;")
        log_layout = QVBoxLayout(log_frame)
        log_layout.setContentsMargins(10, 10, 10, 10)

        log_header = QLabel("翻译日志")
        log_header.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        log_layout.addWidget(log_header)

        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setStyleSheet("""
            QTextEdit {
                background-color: #F8F8F8;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        log_layout.addWidget(self.log_display)

        content_layout.addWidget(log_frame)
        content_layout.addSpacing(10)

        # === 底部按钮区域 ===
        button_layout = QHBoxLayout()

        # 关于按钮
        about_button = QPushButton("关于")
        about_button.clicked.connect(self.show_about)
        about_button.setStyleSheet("""
            QPushButton {
                background-color: #5856D6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #4645A8;
            }
        """)
        
        # 捐赠按钮
        donation_button = QPushButton("支持作者")
        donation_button.clicked.connect(self.show_donation)
        donation_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9500;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #CC7800;
            }
        """)

        # 保存配置按钮
        save_config_button = QPushButton("保存配置")
        save_config_button.clicked.connect(self.save_config)
        save_config_button.setStyleSheet("""
            QPushButton {
                background-color: #5AC8FA;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #4A99C7;
            }
        """)

        # 停止翻译按钮
        self.stop_button = QPushButton("停止翻译")
        self.stop_button.clicked.connect(self.stop_translation)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #FF3B30;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #D63030;
            }
            QPushButton:disabled {
                background-color: #ffadad;
            }
        """)

        # 开始翻译按钮
        self.translate_button = QPushButton("开始翻译")
        self.translate_button.clicked.connect(self.start_translation)
        self.translate_button.setStyleSheet("""
            QPushButton {
                background-color: #34C759;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #2A9F48;
            }
        """)

        button_layout.addWidget(about_button)
        button_layout.addWidget(donation_button)
        button_layout.addWidget(save_config_button)
        button_layout.addStretch()
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.translate_button)

        content_layout.addLayout(button_layout)

        # 添加术语管理等工具按钮
        tools_layout = QHBoxLayout()

        # 术语管理按钮
        self.manage_terminology_btn = QPushButton("术语管理")
        self.manage_terminology_btn.setStyleSheet("""
            QPushButton {
                background-color: #28A745;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.manage_terminology_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.manage_terminology_btn.clicked.connect(self.show_terminology_dialog)

        # 添加到布局
        tools_layout.addWidget(self.manage_terminology_btn)
        tools_layout.addStretch()

        # 添加"关于"和"捐赠"按钮 - 如果需要的话
        if hasattr(self, 'about_button') and hasattr(self, 'donation_button'):
            tools_layout.addWidget(self.about_button)
            tools_layout.addWidget(self.donation_button)

        content_layout.addLayout(tools_layout)

        main_layout.addWidget(content_frame)
        
        # 窗口设置
        self.setMinimumSize(800, 700)
        self.setWindowTitle("大模型字幕翻译小助手")

    def title_bar_mouse_press(self, event):
        """处理标题栏鼠标按下事件，用于拖动窗口"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_start_position = event.pos()

    def title_bar_mouse_move(self, event):
        """处理标题栏鼠标移动事件，用于拖动窗口"""
        if self.dragging and self.drag_start_position:
            self.move(self.pos() + event.pos() - self.drag_start_position)

    def title_bar_mouse_release(self, event):
        """处理标题栏鼠标释放事件，用于拖动窗口"""
        self.dragging = False
        
    def toggle_key_visibility(self):
        """切换API密钥的可见性"""
        if self.api_key_input.echoMode() == QLineEdit.EchoMode.Password:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_key_btn.setText("隐藏")
        else:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_key_btn.setText("显示")

    def start_translation(self):
        """开始翻译过程"""
        # 检查输入文件
        if not self.file_path_input.text():
            QMessageBox.warning(self, "错误", "请选择输入文件")
            return

        # 检查API密钥
        if not self.api_key_input.text():
            QMessageBox.warning(self, "错误", "请输入API密钥")
            return

        # 准备输出文件路径
        input_file = self.file_path_input.text()
        output_dir = self.output_dir_input.text() or os.path.dirname(input_file)
        output_file = os.path.join(
            output_dir,
            f"{os.path.splitext(os.path.basename(input_file))[0]}_{self.target_lang_input.text()}.srt"
        )

        # 创建输出目录（如果不存在）
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # 显示翻译开始信息
        self.log_display.clear()
        self.log_progress(f"翻译开始: {input_file} -> {output_file}")
        
        # 创建配置对象
        config = self.create_translation_config()
        
        # 创建worker并直接使用
        self.worker = TranslationWorker(config)
        
        # 连接信号和槽
        self.worker.worker_signals.progress.connect(self.log_progress)
        self.worker.worker_signals.error.connect(self.log_error)
        self.worker.worker_signals.finished.connect(self.translation_finished)
        
        # 设置输出文件
        self.worker.output_file = output_file
        
        # 传递自定义术语表
        self.worker.custom_terminology = self.custom_terminology
        
        # 先处理字幕并设置给worker，然后再启动worker
        subtitles_for_translation = self.process_subtitle_file(input_file)
        if subtitles_for_translation:
            self.worker.subtitles = subtitles_for_translation
            
            # 更新UI状态
            self.translate_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.stop_requested = False
            
            # 启动翻译
            self.worker.start()
        
    def run_translation(self, worker, input_file, output_file):
        """在工作线程中运行翻译过程"""
        try:
            # 检查输入文件是否存在
            if not os.path.exists(input_file):
                self.worker_signals.error.emit(f"错误: 找不到输入文件 {input_file}")
                self.translation_finished()
                return
                
            # 读取字幕文件
            try:
                with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
                    file_content = f.read()
                    
                if not file_content.strip():
                    self.worker_signals.error.emit("错误: 字幕文件为空")
                    self.translation_finished()
                    return
                    
                self.worker_signals.progress.emit(f"成功读取字幕文件，文件大小: {len(file_content)} 字节")
                    
            except Exception as e:
                self.worker_signals.error.emit(f"读取字幕文件失败: {str(e)}")
                self.translation_finished()
                return
                
            try:
                # 解析字幕
                original_subs = list(srt.parse(file_content))
                if not original_subs:
                    self.worker_signals.error.emit("字幕文件为空或格式不正确")
                    self.translation_finished()
                    return
                    
                # 显示原始字幕数量
                self.worker_signals.progress.emit(f"成功读取到 {len(original_subs)} 条原始字幕")
                
            except Exception as parse_error:
                self.worker_signals.error.emit(f"解析字幕文件失败: {str(parse_error)}\n可能的原因：文件格式不是标准SRT格式")
                self.translation_finished()
                return
                
            # 直接使用原始字幕，跳过过滤步骤
            subtitles_for_translation = []
            
            for sub in original_subs:
                # 直接使用原始内容，不做任何处理
                time_info = f"{sub.start} --> {sub.end}"
                subtitles_for_translation.append({
                    "index": len(subtitles_for_translation) + 1,
                    "time_info": time_info,
                    "content": sub.content,
                    "start": sub.start,
                    "end": sub.end
                })
                    
            # 更新进度
            self.worker_signals.progress.emit(f"找到 {len(subtitles_for_translation)} 条字幕需要翻译")
            
            # 设置字幕和输出文件，但不要重新启动worker
            worker.subtitles = subtitles_for_translation
            worker.output_file = output_file
            # worker.start() - 不需要在这里启动，因为已经在start_translation中启动了
            
        except Exception as e:
            self.worker_signals.error.emit(f"翻译过程出错: {str(e)}\n{traceback.format_exc()}")
            self.translation_finished()
            
    def translation_finished(self):
        """翻译完成，清理和重置UI"""
        if self.worker and self.worker.isRunning():
            self.worker.quit()
            # 不要使用wait()阻塞UI线程
            # self.worker.wait()
        
        self.translate_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
    def stop_translation(self):
        """用户请求停止翻译"""
        if hasattr(self, 'worker') and self.worker and self.worker.isRunning():
            self.worker.stop_translation()  # 调用 worker 的 stop_translation 方法
            self.stop_requested = True
            self.log_progress("正在停止翻译...")
            self.stop_button.setEnabled(False)
            self.translate_button.setEnabled(True)  # 重新启用开始翻译按钮
            
            # 不要等待线程完成，这会阻塞主线程
            # self.worker.wait()
            
            # 检查是否有临时文件
            if hasattr(self.worker, 'output_file') and self.worker.output_file:
                cache_dir = os.path.dirname(self.worker.output_file)
                cache_file = os.path.join(cache_dir, f".temp_translations_{int(time.time())}.json")
                if os.path.exists(cache_file):
                    self.log_progress(f"已保存翻译进度到临时文件: {cache_file}")
                    
                    # 尝试复制临时文件到正式输出文件
                    try:
                        import shutil
                        shutil.copy2(cache_file, self.worker.output_file)
                        self.log_progress(f"已将当前进度保存到最终文件: {self.worker.output_file}")
                    except Exception as e:
                        self.log_progress(f"保存最终文件时出错: {str(e)}")
                        
            # 重置状态
            self.worker = None
            self.stop_requested = False

    def browse_file(self):
        """打开文件选择对话框"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择字幕文件", "", "SRT files (*.srt);;All files (*.*)"
        )
        if file_path:
            self.file_path_input.setText(file_path)
            
    def browse_output_dir(self):
        """选择输出目录"""
        output_dir = QFileDialog.getExistingDirectory(
            self, "选择输出目录", ""
        )
        if output_dir:
            self.output_dir_input.setText(output_dir)
            
    def save_config(self):
        """保存配置到文件"""
        config = {
            'source_lang': self.source_lang_input.text(),
            'target_lang': self.target_lang_input.text(),
            'api_key': self.api_key_input.text(),
            'api_host': self.api_host_input.text(),
            'model': self.model_input.text(),
            'temperature': self.temperature_input.value(),
            'batch_size': self.batch_size_input.value(),
            'delay': self.delay_input.value(),
            'show_original': self.show_original_checkbox.isChecked(),
            'clean_punctuation': self.clean_punctuation_checkbox.isChecked(),
            'netflix_style': True,  # 始终为True，不受用户控制
            'terminology_consistency': True,  # 始终为True，不受用户控制
            'multi_phase': self.multi_phase_checkbox.isChecked(),
            'recovery_enabled': self.recovery_checkbox.isChecked(),
            'enable_batching': self.enable_batching_checkbox.isChecked() # 启用批处理
        }
        
        try:
            with open('subtitle_translator_config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            # 同时保存术语表
            self.save_terminology_table()
            
            QMessageBox.information(self, "配置保存", "配置已成功保存")
        except Exception as e:
            QMessageBox.warning(self, "配置保存失败", f"无法保存配置: {str(e)}")
            
    def create_translation_config(self):
        """创建翻译配置对象"""
        # 收集界面输入
        config = TranslationConfig(
            source_lang=self.source_lang_input.text(),
            target_lang=self.target_lang_input.text(),
            api_key=self.api_key_input.text(),
            api_host=self.api_host_input.text(),
            model=self.model_input.text(),
            temperature=self.temperature_input.value(),
            batch_size=self.batch_size_input.value(),
            delay=self.delay_input.value(),
            preserve_format=True,
            netflix_style=True,  # 始终启用Netflix风格优化
            terminology_consistency=True,  # 始终启用术语一致性
            multi_phase=self.multi_phase_checkbox.isChecked(),
            recovery_enabled=self.recovery_checkbox.isChecked(),
            enable_batching=self.enable_batching_checkbox.isChecked(),  # 启用批处理
            clean_punctuation=self.clean_punctuation_checkbox.isChecked(),  # 清理标点
            show_original=self.show_original_checkbox.isChecked()  # 显示原文
        )
        return config

    def log_progress(self, message):
        """记录进度信息"""
        self.log_display.append(message)
        # 滚动到底部
        scrollbar = self.log_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def log_error(self, message):
        """记录错误信息"""
        error_message = f"错误: {message}"
        self.log_display.append(f"<span style='color:red'>{error_message}</span>")
        scrollbar = self.log_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def edit_model_list(self):
        """编辑模型列表"""
        # 将会在未来版本中实现
        QMessageBox.information(self, "模型列表编辑", "此功能将在未来版本中实现。请直接在文本框中输入模型名称。")

    def populate_terminology_table(self):
        """填充术语表格数据"""
        self.terms_table.setRowCount(0)  # 清空表格
        
        for i, (term, translation) in enumerate(self.custom_terminology.items()):
            self.terms_table.insertRow(i)
            self.terms_table.setItem(i, 0, QTableWidgetItem(term))
            self.terms_table.setItem(i, 1, QTableWidgetItem(translation))
    
    def add_terminology_item(self):
        """添加新的术语条目"""
        row_count = self.terms_table.rowCount()
        self.terms_table.insertRow(row_count)
        
        # 创建可编辑的单元格
        self.terms_table.setItem(row_count, 0, QTableWidgetItem(""))
        self.terms_table.setItem(row_count, 1, QTableWidgetItem(""))
        
        # 立即设置焦点到新添加的行
        self.terms_table.setCurrentCell(row_count, 0)
        self.terms_table.editItem(self.terms_table.item(row_count, 0))
    
    def remove_terminology_item(self):
        """删除选中的术语条目"""
        selected_rows = set()
        for item in self.terms_table.selectedItems():
            selected_rows.add(item.row())
        
        # 从大到小排序行号，以便从下往上删除，避免索引变化
        for row in sorted(selected_rows, reverse=True):
            self.terms_table.removeRow(row)
    
    def save_terminology_table(self):
        """保存术语表格到自定义术语字典"""
        new_terminology = {}
        
        for row in range(self.terms_table.rowCount()):
            term_item = self.terms_table.item(row, 0)
            translation_item = self.terms_table.item(row, 1)
            
            if term_item and translation_item:
                term = term_item.text().strip()
                translation = translation_item.text().strip()
                
                if term and translation:  # 只保存非空的术语
                    new_terminology[term] = translation
        
        # 更新术语字典
        self.custom_terminology = new_terminology
        
        # 保存到文件
        if self.save_custom_terminology():
            QMessageBox.information(self, "保存成功", "术语列表已保存")
        else:
            QMessageBox.warning(self, "保存失败", "术语列表保存失败，请检查文件权限")

    def process_subtitle_file(self, input_file):
        """处理字幕文件并返回字幕列表"""
        try:
            # 检查输入文件是否存在
            if not os.path.exists(input_file):
                self.log_error(f"错误: 找不到输入文件 {input_file}")
                return None
                
            # 显示加载进度对话框
            progress = QProgressDialog("正在加载字幕文件...", "取消", 0, 100, self)
            progress.setWindowTitle("加载中")
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.show()
            
            # 更新进度
            progress.setValue(10)
            QApplication.processEvents()
            
            # 打开文件并解析SRT字幕
            try:
                with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                    
                srt_subtitles = list(srt.parse(content))
            except Exception as e:
                self.log_error(f"解析字幕文件失败: {str(e)}")
                return None
                
            # 更新进度
            progress.setValue(30)
            QApplication.processEvents()
            
            # 转换为内部字幕格式
            subtitles_for_translation = []
            
            for sub in srt_subtitles:
                # 提取时间信息
                time_info = f"{sub.start} --> {sub.end}"
                
                # 添加到字幕列表
                subtitles_for_translation.append({
                    "index": sub.index,
                    "time_info": time_info,
                    "content": sub.content,
                    "start": sub.start,
                    "end": sub.end
                })
            
            # 更新进度
            progress.setValue(40)
            QApplication.processEvents()
            
            # 第一步：清理听障字幕
            cleaned_subtitle_count = 0
            for sub in subtitles_for_translation:
                original_content = sub["content"]
                cleaned_content = SubtitleProcessor.remove_hearing_impaired(original_content)
                if cleaned_content != original_content:
                    cleaned_subtitle_count += 1
                    sub["content"] = cleaned_content
                
            # 过滤掉清理后内容为空的字幕
            subtitles_for_translation = [sub for sub in subtitles_for_translation if sub["content"].strip()]
            
            if cleaned_subtitle_count > 0:
                self.log_progress(f"已清理 {cleaned_subtitle_count} 条字幕中的听障标记")
                
            # 更新进度
            progress.setValue(50)
            QApplication.processEvents()
                
            # 第二步：合并相似连续字幕
            original_count = len(subtitles_for_translation)
            subtitles_for_translation = SubtitleProcessor.merge_similar_consecutive_subtitles(
                subtitles_for_translation, max_time_diff=1.0
            )
            merged_count = original_count - len(subtitles_for_translation)
            
            if merged_count > 0:
                self.log_progress(f"已合并 {merged_count} 条相似连续字幕")
                    
            # 更新进度
            progress.setValue(60)
            QApplication.processEvents()
                
            # 第三步：智能合并短字幕
            original_count = len(subtitles_for_translation)
            subtitles_for_translation = SubtitleProcessor.smart_merge_subtitles(subtitles_for_translation)
            smart_merged_count = original_count - len(subtitles_for_translation)
            
            if smart_merged_count > 0:
                self.log_progress(f"已智能合并 {smart_merged_count} 条短字幕为语义完整的字幕")
                
            # 更新进度
            progress.setValue(75)
            QApplication.processEvents()
                
            # 第四步：平衡字幕长度（拆分过长字幕）
            original_count = len(subtitles_for_translation)
            subtitles_for_translation = SubtitleProcessor.balance_subtitle_length(
                subtitles_for_translation, min_chars=10, max_chars=42
            )
            balanced_count = len(subtitles_for_translation) - original_count
            
            if balanced_count > 0:
                self.log_progress(f"已拆分 {balanced_count} 条过长字幕以符合Netflix标准")
                
            # 更新进度
            progress.setValue(100)
            QApplication.processEvents()
            progress.close()
            
            self.log_progress(f"最终处理完成，需要翻译的字幕数量: {len(subtitles_for_translation)} 条")
            
            return subtitles_for_translation
            
        except Exception as e:
            self.log_error(f"处理字幕文件出错: {str(e)}\n{traceback.format_exc()}")
            return None

    def show_terminology_dialog(self):
        """显示术语管理对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("术语管理")
        dialog.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        # 创建表格
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["原文", "译文"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # 加载现有术语
        table.setRowCount(len(self.custom_terminology))
        for row, (term, translation) in enumerate(self.custom_terminology.items()):
            table.setItem(row, 0, QTableWidgetItem(term))
            table.setItem(row, 1, QTableWidgetItem(translation))
        
        # 添加按钮
        buttons_layout = QHBoxLayout()
        
        add_button = QPushButton("添加")
        add_button.clicked.connect(lambda: self.add_terminology_row(table))
        
        delete_button = QPushButton("删除")
        delete_button.clicked.connect(lambda: self.delete_terminology_row(table))
        
        import_button = QPushButton("导入")
        import_button.clicked.connect(lambda: self.import_terminology(table))
        
        export_button = QPushButton("导出")
        export_button.clicked.connect(self.export_terminology)
        
        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(delete_button)
        buttons_layout.addWidget(import_button)
        buttons_layout.addWidget(export_button)
        
        # 确定和取消按钮
        dialog_buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        dialog_buttons.accepted.connect(lambda: self.save_terminology_from_dialog(table, dialog))
        dialog_buttons.rejected.connect(dialog.reject)
        
        layout.addWidget(table)
        layout.addLayout(buttons_layout)
        layout.addWidget(dialog_buttons)
        
        dialog.exec()
        
    def add_terminology_row(self, table):
        """在术语表中添加一行"""
        row_position = table.rowCount()
        table.insertRow(row_position)
        
    def delete_terminology_row(self, table):
        """删除所选的行"""
        selected_rows = set(index.row() for index in table.selectedIndexes())
        for row in sorted(selected_rows, reverse=True):
            table.removeRow(row)
            
    def import_terminology(self, table):
        """从文件导入术语表"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入术语表", "", "JSON文件 (*.json);;CSV文件 (*.csv);;所有文件 (*.*)"
        )
        
        if not file_path:
            return
            
        try:
            imported_terminology = {}
            
            # 根据文件扩展名处理不同格式
            if file_path.lower().endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    imported_terminology = json.load(f)
            elif file_path.lower().endswith('.csv'):
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    import csv
                    reader = csv.reader(f)
                    next(reader, None)  # 跳过标题行
                    for row in reader:
                        if len(row) >= 2:
                            imported_terminology[row[0].strip()] = row[1].strip()
                            
            # 更新表格
            table.setRowCount(0)
            for term, translation in imported_terminology.items():
                row_position = table.rowCount()
                table.insertRow(row_position)
                table.setItem(row_position, 0, QTableWidgetItem(term))
                table.setItem(row_position, 1, QTableWidgetItem(translation))
                
            QMessageBox.information(self, "导入成功", f"成功导入 {len(imported_terminology)} 条术语")
            
        except Exception as e:
            QMessageBox.critical(self, "导入失败", f"导入术语表失败: {str(e)}")
            
    def export_terminology(self):
        """导出术语表到文件"""
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, "导出术语表", "", "JSON文件 (*.json);;CSV文件 (*.csv)"
        )
        
        if not file_path:
            return
            
        try:
            # 根据选择的过滤器确定文件格式
            if selected_filter == "JSON文件 (*.json)" or file_path.lower().endswith('.json'):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.custom_terminology, f, ensure_ascii=False, indent=2)
            elif selected_filter == "CSV文件 (*.csv)" or file_path.lower().endswith('.csv'):
                with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
                    import csv
                    writer = csv.writer(f)
                    writer.writerow(["原文", "译文"])
                    for term, translation in self.custom_terminology.items():
                        writer.writerow([term, translation])
                        
            QMessageBox.information(self, "导出成功", f"成功导出 {len(self.custom_terminology)} 条术语")
            
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出术语表失败: {str(e)}")
            
    def save_terminology_from_dialog(self, table, dialog):
        """从对话框保存术语表"""
        try:
            new_terminology = {}
            for row in range(table.rowCount()):
                term_item = table.item(row, 0)
                translation_item = table.item(row, 1)
                
                if term_item and translation_item:
                    term = term_item.text().strip()
                    translation = translation_item.text().strip()
                    
                    if term and translation:
                        new_terminology[term] = translation
            
            # 更新术语表
            self.custom_terminology = new_terminology
            self.save_custom_terminology()
            
            # 如果有活动的翻译线程，更新其术语表
            if self.translation_thread is not None and hasattr(self.translation_thread, 'add_custom_terminology'):
                self.translation_thread.add_custom_terminology(self.custom_terminology)
                
            QMessageBox.information(self, "保存成功", f"已保存 {len(self.custom_terminology)} 条术语")
            dialog.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存术语表失败: {str(e)}")

    def toggle_maximize(self):
        """切换窗口最大化状态"""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
            
    def on_language_changed(self, index):
        """语言改变时的处理"""
        language_code = self.language_combo.itemData(index)
        if language_code and self.current_language != language_code:
            self.current_language = language_code
            # 更新界面语言
            self.update_ui_language()
            # 保存到配置
            self.saved_config['interface_language'] = language_code
            self.save_config()
            self.log_progress(f"Interface language changed to {SUPPORTED_LANGUAGES[language_code]}")

    def load_custom_terminology(self):
        """加载自定义术语列表"""
        try:
            if os.path.exists('custom_terminology.json'):
                with open('custom_terminology.json', 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载术语列表出错: {str(e)}")
        return {}  # 返回空字典作为默认术语列表

    def save_custom_terminology(self):
        """保存自定义术语列表"""
        try:
            with open('custom_terminology.json', 'w', encoding='utf-8') as f:
                json.dump(self.custom_terminology, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存术语列表出错: {str(e)}")
            return False

    def show_about(self):
        """显示关于对话框"""
        about_dialog = AboutDialog(self)
        about_dialog.show()
        
    def show_donation(self):
        """显示捐赠对话框"""
        donation_dialog = DonationDialog(self)
        donation_dialog.show()

    def load_saved_config(self):
        """加载保存的配置"""
        try:
            if os.path.exists('subtitle_translator_config.json'):
                with open('subtitle_translator_config.json', 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载配置出错: {str(e)}")
        return {}  # 返回空字典作为默认配置


def disable_unused_qt_services():
    """禁用不需要的 Qt 服务，减少崩溃可能性"""
    try:
        # macOS 特定设置
        os.environ["QT_MAC_WANTS_LAYER"] = "1"  # 解决某些 macOS 渲染问题

        os.environ["QT_PLUGIN_PERMISSION"] = "0"  # 禁用权限请求插件
        os.environ["QT_LOCATION_DISABLED"] = "1"  # 明确禁用位置服务
        os.environ["QT_MAC_DISABLE_FOREGROUND_APPLICATION_TRANSFORM"] = "1"  # 防止某些 macOS 特定的转换

        # 禁用位置服务
        os.environ["QT_ENABLE_GEOSERVICES"] = "0"
        os.environ["QT_ENABLE_LOCATION"] = "0"

        # 禁用不必要的网络状态检查
        os.environ["QT_BEARER_POLL_TIMEOUT"] = "-1"

        # 减少调试日志输出
        os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt.qpa.*=false"

        # 禁用多媒体
        os.environ["QT_MULTIMEDIA_PREFERRED_PLUGINS"] = "nosystems"

        # 优化性能
        os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"

        # 强制使用 raster 图形后端，更稳定
        os.environ["QT_OPENGL"] = "software"

        print("已禁用不需要的 Qt 服务")
    except Exception as e:
        print(f"设置 Qt 环境变量时出错: {e}")


class APIClient:
    """API客户端，用于与模型API交互"""
    
    def __init__(self, api_key, api_base, model):
        """初始化API客户端"""
        if not api_key:
            raise ValueError("API密钥不能为空")
            
        if not model:
            raise ValueError("模型名称不能为空")
            
        self.api_key = api_key.strip()
        self.api_base = api_base.strip() if api_base else "https://api.deepseek.com"
        
        # 确保API基础URL格式正确
        if not (self.api_base.startswith("http://") or self.api_base.startswith("https://")):
            self.api_base = f"https://{self.api_base}"
            
        # 移除末尾的斜杠
        if self.api_base.endswith("/"):
            self.api_base = self.api_base[:-1]
            
        self.model = model.strip()
        self.session = None
        
        print(f"API客户端初始化成功，使用API主机: {self.api_base}")
        print(f"使用模型: {self.model}")
        print(f"API密钥前5个字符: {self.api_key[:5]}...")
        
    async def _ensure_session(self):
        """确保会话已创建"""
        if self.session is None or self.session.closed:
            try:
                self.session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=60),  # 默认60秒超时
                    connector=aiohttp.TCPConnector(limit=10, ssl=False)  # 限制连接数，禁用SSL验证如果需要
                )
                print("创建了新的API会话")
            except Exception as e:
                print(f"创建会话时出错: {str(e)}")
                raise
        return self.session
        
    async def chat(self, prompt):
        """发送聊天请求"""
        session = await self._ensure_session()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 处理不同的prompt格式
        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        elif isinstance(prompt, list):
            messages = prompt
        elif isinstance(prompt, dict):
            # 处理我们自定义的格式，包含system_message和user_message
            messages = [
                {"role": "system", "content": prompt.get("system_message", "")},
                {"role": "user", "content": prompt.get("user_message", "")}
            ]
        else:
            print(f"无效的prompt格式: {type(prompt)}")
            raise ValueError("无效的prompt格式")
            
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7
        }
        
        api_endpoint = f"{self.api_base}/v1/chat/completions"
        print(f"发送API请求到: {api_endpoint}")
        print(f"使用模型: {self.model}")
        
        # 打印完整的请求内容前30个字符
        if isinstance(prompt, str):
            print(f"请求内容前30个字符: {prompt[:30]}...")
        elif isinstance(prompt, dict):
            user_message = prompt.get("user_message", "")
            print(f"用户请求内容前30个字符: {user_message[:30]}...")
        else:
            # 只打印用户消息
            user_messages = [m for m in messages if m.get("role") == "user"]
            if user_messages:
                print(f"用户请求内容前30个字符: {user_messages[0].get('content', '')[:30]}...")
        
        try:
            async with session.post(
                api_endpoint,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"API请求失败: {response.status} - {error_text}")
                    raise Exception(f"API请求失败: {response.status} - {error_text}")
                    
                result = await response.json()
                if "choices" in result and result["choices"]:
                    response_text = result["choices"][0]["message"]["content"]
                    print(f"API响应前30个字符: {response_text[:30]}...")
                    return response_text
                else:
                    print(f"API响应缺少内容: {result}")
                    raise Exception("API响应缺少内容")
        except Exception as e:
            print(f"API请求异常: {str(e)}")
            raise Exception(f"API请求异常: {str(e)}")
            
    async def close(self):
        """关闭会话"""
        if self.session:
            await self.session.close()
            self.session = None

def set_app_style():
    """设置全局应用样式，确保在所有平台上文本可见"""
    return """
    /* 全局文本颜色设置 */
    QWidget {
        color: #000000;
    }

    /* 确保输入框文本可见 */
    QLineEdit, QTextEdit, QPlainTextEdit {
        color: #000000;
        background-color: #ffffff;
    }

    /* 确保下拉菜单文本可见 */
    QComboBox {
        color: #000000;
        background-color: #ffffff;
    }

    /* 确保标签文本可见 */
    QLabel {
        color: #000000;
    }

    /* 确保按钮文本可见 - 保留原有按钮样式但确保文本为黑色 */
    QPushButton {
        color: #000000;
    }

    /* 白色背景上的按钮文本保持黑色 */
    QPushButton[style*="background-color: white"] {
        color: #000000;
    }

    /* 深色背景上的按钮文本为白色 */
    QPushButton[style*="background-color: #007AFF"],
    QPushButton[style*="background-color: #34C759"],
    QPushButton[style*="background-color: #FF3B30"],
    QPushButton[style*="background-color: #FF9500"] {
        color: #ffffff;
    }

    /* 确保复选框文本可见 */
    QCheckBox {
        color: #000000;
    }

    /* 确保标签页文本可见 */
    QTabBar::tab {
        color: #000000;
    }
    
    /* 确保工具提示文本可见 */
    QToolTip {
        color: #000000;
        background-color: #ffffdc;
        border: 1px solid #999999;
    }
    
    /* 确保消息框文本可见 */
    QMessageBox {
        color: #000000;
        background-color: #ffffff;
    }
    
    QMessageBox QLabel {
        color: #000000;
    }
    
    QMessageBox QPushButton {
        color: #000000;
        background-color: #f0f0f0;
        border: 1px solid #cccccc;
        padding: 5px;
        border-radius: 3px;
    }
    """

# 辅助函数：将秒数转换为时间码格式 (HH:MM:SS.MS)
def format_timecode(seconds):
    """
    将秒数转换为时间码格式 (HH:MM:SS.MS)
    
    Args:
        seconds: 秒数，可以是浮点数或整数
        
    Returns:
        格式化的时间码字符串，格式为 HH:MM:SS.MS
    """
    seconds = float(seconds)  # 确保转换为浮点数
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    return f"{hours:d}:{minutes:02d}:{seconds:06.3f}"


if __name__ == "__main__":
    # 添加全局异常处理
    sys.excepthook = exception_hook

    # 添加一个日志文件处理器
    import logging

    logging.basicConfig(
        filename='app_log.txt',
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 禁用不需要的 Qt 服务
    disable_unused_qt_services()

    try:
        # PyQt6中高DPI缩放是默认启用的，不需要显式设置AA_EnableHighDpiScaling
        # 只保留AA_UseHighDpiPixmaps属性
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    except AttributeError:
        # 如果这个属性也不存在，就完全跳过高DPI设置
        pass

    app = QApplication(sys.argv)

    # 设置应用样式
    app.setStyle("Fusion")
    app.setStyleSheet(set_app_style())


    window = SubtitleTranslatorApp()
    window.show()

    sys.exit(app.exec())