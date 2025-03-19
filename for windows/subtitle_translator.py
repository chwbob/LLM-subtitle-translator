import sys
import os
import re
import json
import asyncio
import aiohttp
import srt
import nest_asyncio
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, QLineEdit,
                             QFileDialog, QTextEdit, QWidget, QVBoxLayout, QHBoxLayout,
                             QTabWidget, QFrame, QCheckBox, QMessageBox, QComboBox,
                             QScrollArea, QGridLayout, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import Qt, QObject, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont, QPixmap

# 应用 nest_asyncio 来解决事件循环问题
nest_asyncio.apply()


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
    source_lang: str
    target_lang: str
    delay: float
    temperature: float
    api_host: str
    api_key: str
    model: str
    additional_prompt: str
    batch_size: int = 30
    show_original: bool = True
    clean_punctuation: bool = True
    custom_prompt: Optional[str] = None


class SubtitleProcessor:
    @staticmethod
    def remove_hearing_impaired(text: str) -> str:
        """删除听障字幕（方括号内的内容）"""
        return re.sub(r'\[.*?\]', '', text).strip()

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


class WorkerSignals(QObject):
    progress = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)


class TranslationWorker(QThread):
    def __init__(self, config, file_path, output_path, parent=None):
        super().__init__(parent)
        self.config = config
        self.file_path = file_path
        self.output_path = output_path
        self.signals = WorkerSignals()
        self.is_running = True
        self.temp_output_path = self.output_path + ".temp"
        # 添加跟踪已翻译字幕的变量
        self.processed_subs = []
        self.original_subs = []
        self.current_batch = 0
        self.total_batches = 0

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.translate_file_async())
        except Exception as e:
            self.signals.error.emit(f"Error: {str(e)}")
        finally:
            self.signals.finished.emit()

    def stop(self):
        self.is_running = False

    async def translate_file_async(self):
        """异步文件翻译处理"""
        try:
            # 使用 errors='replace' 处理编码问题
            with open(self.file_path, 'r', encoding='utf-8', errors='replace') as f:
                file_content = f.read()

            try:
                self.original_subs = list(srt.parse(file_content))
            except Exception as parse_error:
                self.signals.error.emit(f"解析字幕文件失败: {str(parse_error)}\n可能的原因：文件格式不是标准SRT格式")
                return

            # 检查字幕列表是否为空
            if not self.original_subs:
                self.signals.error.emit("字幕文件为空或格式不正确")
                return

            # 预处理字幕
            self.processed_subs = []  # 清空已处理字幕列表
            subtitles_for_translation = []

            self.signals.progress.emit("正在预处理字幕...")

            for sub in self.original_subs:
                # 删除听障字幕
                cleaned_text = SubtitleProcessor.remove_hearing_impaired(sub.content)
                if cleaned_text.strip():
                    time_info = f"{sub.start} --> {sub.end}"
                    subtitles_for_translation.append({
                        "index": len(subtitles_for_translation) + 1,
                        "time_info": time_info,
                        "content": cleaned_text,
                        "start": sub.start,
                        "end": sub.end
                    })

            # 检查是否有有效字幕需要翻译
            if not subtitles_for_translation:
                self.signals.error.emit("没有找到有效的字幕内容进行翻译")
                return

            self.signals.progress.emit(f"找到 {len(subtitles_for_translation)} 条字幕需要翻译")

            # 计算批次总数
            BATCH_SIZE = self.config.batch_size
            batches = [subtitles_for_translation[i:i + BATCH_SIZE] for i in
                       range(0, len(subtitles_for_translation), BATCH_SIZE)]
            self.total_batches = len(batches)
            self.signals.progress.emit(f"将分为 {self.total_batches} 个批次进行翻译")

            try:
                # 批量翻译所有字幕
                translations = await self.bulk_translate_subtitles(subtitles_for_translation, self.config)

                # 如果翻译被用户中断，部分翻译结果将在bulk_translate_subtitles方法中保存
                if not self.is_running:
                    self.signals.progress.emit("\n翻译已被用户中断，已翻译部分已保存")
                    return

                # 检查翻译结果
                if not translations:
                    self.signals.error.emit("翻译结果为空")
                    return

                if len(translations) != len(subtitles_for_translation):
                    self.signals.progress.emit(
                        f"警告: 翻译结果数量不匹配 (接收到 {len(translations)}, 预期 {len(subtitles_for_translation)})")
                    # 继续处理可用的翻译结果

                # 组合原文和译文，生成最终结果
                self.process_and_save_translations(subtitles_for_translation, translations, final=True)

                # 翻译完成，可以移除临时文件
                if os.path.exists(self.temp_output_path):
                    try:
                        os.remove(self.temp_output_path)
                    except:
                        pass  # 忽略临时文件删除失败

                self.signals.progress.emit("\n翻译完成！")
                # 使用signal通知完成，而不是直接弹出消息框
                self.signals.progress.emit(f"翻译已完成！翻译字幕保存地址：\n{self.output_path}")

            except Exception as e:
                import traceback
                error_msg = f"翻译过程中出错: {str(e)}\n{traceback.format_exc()}"
                self.signals.error.emit(error_msg)

        except Exception as e:
            import traceback
            error_msg = f"处理文件过程中出错: {str(e)}\n{traceback.format_exc()}"
            self.signals.error.emit(error_msg)

    def remove_duplicate_subtitles(self, subtitles):
        """去除内容和时间轴完全相同的重复字幕"""
        if not subtitles:
            return []

        unique_subtitles = []
        # 用于检查重复的字典，键为 (start, end, content)
        seen = {}

        for sub in subtitles:
            # 创建一个唯一键来标识字幕 (开始时间, 结束时间, 内容)
            key = (str(sub.start), str(sub.end), sub.content)

            # 如果这个字幕之前没见过，就添加到结果列表中
            if key not in seen:
                seen[key] = True
                unique_subtitles.append(sub)

        # 重新编号字幕
        for i, sub in enumerate(unique_subtitles):
            unique_subtitles[i] = srt.Subtitle(
                index=i + 1,  # 从1开始编号
                start=sub.start,
                end=sub.end,
                content=sub.content
            )

        removed_count = len(subtitles) - len(unique_subtitles)
        if removed_count > 0:
            self.signals.progress.emit(f"已移除 {removed_count} 条重复字幕")

        return unique_subtitles

    # 修改 process_and_save_translations 方法，在保存之前添加去重处理
    def process_and_save_translations(self, subtitles, translations, final=False):
        """处理翻译结果并保存到文件"""
        # 限制处理的翻译数量，以防数量不匹配
        translations_to_process = min(len(subtitles), len(translations))

        # 组合原文和译文，并处理标点符号
        for i in range(translations_to_process):
            sub_info = subtitles[i]
            translation = translations[i]

            # 处理翻译文本
            if self.config.clean_punctuation:
                processed_translation = SubtitleProcessor.clean_punctuation(translation)
            else:
                processed_translation = translation

            # 根据是否显示原文来组织内容
            if self.config.show_original:
                # 处理原文，合并多行为单行，去除不必要的换行
                original_content = sub_info['content'].replace('\n', ' ').strip()
                content = f"{processed_translation}\n{original_content}"
            else:
                content = processed_translation

            new_subtitle = srt.Subtitle(
                index=len(self.processed_subs) + 1,  # 使用整体序号
                start=sub_info["start"],
                end=sub_info["end"],
                content=content
            )
            self.processed_subs.append(new_subtitle)

        # 为了避免频繁IO操作，可以考虑设置保存间隔
        try:
            # 确定保存的目标文件
            save_path = self.output_path if final else self.temp_output_path

            # 如果是最终保存，则进行字幕去重处理
            if final:
                self.signals.progress.emit("正在移除重复字幕...")
                self.processed_subs = self.remove_duplicate_subtitles(self.processed_subs)

            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(srt.compose(self.processed_subs))

            if not final:
                self.signals.progress.emit(
                    f"已保存当前翻译进度 ({len(self.processed_subs)}/{len(self.original_subs)})...")
        except Exception as save_error:
            self.signals.progress.emit(f"保存进度时出错: {str(save_error)}")

    async def bulk_translate_subtitles(self, subtitles: List[dict], config: TranslationConfig) -> List[str]:
        """批量翻译所有字幕，每个批次带有上下文"""
        # 将字幕分成较小的批次
        BATCH_SIZE = config.batch_size
        batches = []

        # 分批并记录每个批次的实际需要翻译的范围
        for i in range(0, len(subtitles), BATCH_SIZE):
            end_idx = min(i + BATCH_SIZE, len(subtitles))
            batches.append((i, end_idx))

        all_translations = []

        for batch_index, (start_idx, end_idx) in enumerate(batches):
            self.current_batch = batch_index + 1

            if not self.is_running:
                # 用户中断翻译，保存当前进度
                self.signals.progress.emit(f"\n翻译被用户中断，已完成 {batch_index}/{len(batches)} 个批次")
                # 保存当前已翻译的部分
                if all_translations:
                    self.process_and_save_translations(subtitles[:len(all_translations)], all_translations)
                return all_translations

            self.signals.progress.emit(f"\n处理批次 {batch_index + 1}/{len(batches)}...")

            # 计算上下文边界
            context_start = max(0, start_idx - 5)  # 前5行，但不超出范围
            context_end = min(len(subtitles), end_idx + 5)  # 后5行，但不超出范围

            # 使用上下文创建批次
            context_batch = subtitles[context_start:context_end]
            # 记录实际需要翻译的起止索引(相对于context_batch)
            translate_start = start_idx - context_start
            translate_end = end_idx - context_start

            # 最大重试次数
            max_retries = 3
            retry_count = 0
            batch_translations = []

            while retry_count < max_retries and self.is_running:
                try:
                    # 构建包含时间轴信息的字幕文本
                    formatted_subtitles = []
                    for idx, sub in enumerate(context_batch):
                        # 标记需要翻译的行
                        prefix = "TRANSLATE: " if translate_start <= idx < translate_end else "CONTEXT: "
                        formatted_subtitles.append(
                            f"{prefix}[{sub['index']}] {sub['time_info']}\n{sub['content']}"
                        )

                    all_subtitles_text = "\n\n".join(formatted_subtitles)

                    # 构建系统提示词
                    system_prompt = f"""You are a professional subtitle translator.
    Your task is to translate subtitles from {config.source_lang} to {config.target_lang}.
    Important requirements:
    1. ONLY translate the lines marked with 'TRANSLATE:', ignore lines marked with 'CONTEXT:'
    2. The 'CONTEXT:' lines are provided to help you understand the context
    3. Keep the time information untouched
    4. Translate considering the full context and natural flow
    5. Ensure translations fit within their time slots
    6. Return translations in the EXACT same order as the input, ONLY for the 'TRANSLATE:' lines
    7. Only return the translations, not the time information or line numbers

    Additional context: {config.additional_prompt}"""

                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Please translate these subtitles:\n\n{all_subtitles_text}"}
                    ]

                    self.signals.progress.emit(
                        f"翻译字幕 {subtitles[start_idx]['index']} 到 {subtitles[end_idx - 1]['index']}...")
                    self.signals.progress.emit(
                        f"上下文范围: {subtitles[context_start]['index']} 到 {subtitles[context_end - 1]['index']}")

                    timeout = aiohttp.ClientTimeout(total=180)  # 增加超时时间到3分钟

                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        headers = {
                            "Authorization": f"Bearer {config.api_key}",
                            "Content-Type": "application/json"
                        }
                        payload = {
                            "model": config.model,
                            "messages": messages,
                            "temperature": config.temperature
                        }

                        try:
                            # 使用 json 参数传递 payload
                            async with session.post(
                                    f"{config.api_host}/v1/chat/completions",
                                    headers=headers,
                                    json=payload
                            ) as response:
                                if response.status != 200:
                                    error_text = await response.text()
                                    raise Exception(f"API请求失败，状态码: {response.status}, 错误: {error_text}")

                                result = await response.json()
                                if "choices" in result and result["choices"]:
                                    translation = result["choices"][0]["message"]["content"]
                                    batch_translations = self.parse_bulk_translation(translation)

                                    # 验证翻译结果数量是否匹配
                                    expected_count = end_idx - start_idx
                                    if len(batch_translations) != expected_count:
                                        self.signals.progress.emit(
                                            f"警告: 翻译结果数量不匹配 (接收到 {len(batch_translations)}, 预期 {expected_count})")
                                        # 如果翻译结果数量不对，可能需要重试或特殊处理
                                        if len(batch_translations) > 0:  # 至少有一些翻译结果
                                            # 如果翻译结果较少，使用原文填充
                                            if len(batch_translations) < expected_count:
                                                missing_count = expected_count - len(batch_translations)
                                                self.signals.progress.emit(f"填充 {missing_count} 条缺失翻译...")
                                                for i in range(len(batch_translations), expected_count):
                                                    original_idx = start_idx + i
                                                    if original_idx < len(subtitles):
                                                        batch_translations.append(subtitles[original_idx]['content'])
                                            # 如果翻译结果较多，截断
                                            elif len(batch_translations) > expected_count:
                                                self.signals.progress.emit(
                                                    f"截断多余的 {len(batch_translations) - expected_count} 条翻译...")
                                                batch_translations = batch_translations[:expected_count]

                                            all_translations.extend(batch_translations)
                                            self.signals.progress.emit("使用调整后的翻译结果继续...")
                                            break
                                        else:
                                            raise Exception("翻译结果为空")
                                    else:
                                        all_translations.extend(batch_translations)
                                        self.signals.progress.emit("批次翻译成功")

                                        # 批次完成后，保存当前进度
                                        current_index = end_idx
                                        subtitles_translated = subtitles[:min(current_index, len(subtitles))]
                                        self.process_and_save_translations(subtitles_translated, all_translations)

                                        break  # 成功处理，跳出重试循环
                                else:
                                    raise Exception(f"翻译失败，API返回: {result}")
                        except aiohttp.ClientError as client_err:
                            retry_count += 1
                            self.signals.progress.emit(
                                f"网络错误 (尝试 {retry_count}/{max_retries}): {str(client_err)}")
                            if retry_count >= max_retries:
                                self.signals.progress.emit(f"网络错误，无法连接到API")
                                # 对于失败的批次，添加原文作为占位符
                                placeholder_translations = [sub['content'] for sub in subtitles[start_idx:end_idx]]
                                all_translations.extend(placeholder_translations)
                            else:
                                # 在重试之前等待更长时间
                                await asyncio.sleep(5 * retry_count)  # 递增等待时间

                except Exception as e:
                    retry_count += 1
                    error_msg = f"批次 {batch_index + 1} 处理错误 (尝试 {retry_count}/{max_retries}): {str(e)}"
                    self.signals.progress.emit(error_msg)

                    if retry_count >= max_retries:
                        self.signals.progress.emit(f"在 {max_retries} 次尝试后批次处理失败")
                        # 对于失败的批次，添加原文作为占位符
                        placeholder_translations = [sub['content'] for sub in subtitles[start_idx:end_idx]]
                        all_translations.extend(placeholder_translations)

                        # 即使批次失败，也保存当前进度
                        current_index = end_idx
                        subtitles_translated = subtitles[:min(current_index, len(subtitles))]
                        self.process_and_save_translations(subtitles_translated, all_translations)
                    else:
                        # 在重试之前等待一段时间
                        await asyncio.sleep(5 * retry_count)  # 递增等待时间

            # 处理完一批后休息一下
            await asyncio.sleep(config.delay)

        return all_translations

    def parse_bulk_translation(self, translation_text: str) -> List[str]:
        """解析批量翻译结果，使其更加健壮"""
        translations = []
        current_translation = []

        if not translation_text:
            self.signals.progress.emit("警告: 收到空的翻译结果")
            return []

        lines = translation_text.split('\n')
        index_pattern = re.compile(r'^\s*\[\s*\d+\s*\]')  # 匹配更多可能的索引格式
        time_pattern = re.compile(r'^\s*\d+:\d+:\d+')  # 匹配时间轴开头

        for line in lines:
            line = line.strip()
            if not line:
                if current_translation:
                    translations.append('\n'.join(current_translation))
                    current_translation = []
                continue

            # 检查是否是新字幕的开始
            if index_pattern.match(line) or line.startswith('[') and ']' in line:
                if current_translation:
                    translations.append('\n'.join(current_translation))
                    current_translation = []
            # 排除时间轴行
            elif not time_pattern.match(line) and not line.startswith('-->') and not ' --> ' in line:
                current_translation.append(line)

        # 添加最后一个翻译
        if current_translation:
            translations.append('\n'.join(current_translation))

        # 如果没有解析出任何翻译，尝试直接返回整个文本
        if not translations and translation_text.strip():
            self.signals.progress.emit("警告: 翻译解析失败，使用完整响应")
            return [translation_text.strip()]

        return translations


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
        version_label = QLabel("Version 1.1.0")
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

        desc = "一个使用AI进行字幕翻译的小助手，支持多种语言，使用大语言模型联系上下文提高翻译质量"
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
            "- 可选保留原文"
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
    def __init__(self):
        super().__init__()

        # 设置窗口标题和大小
        self.setWindowTitle("大模型字幕翻译小助手")
        self.setMinimumSize(900, 700)

        # 使用自定义标题栏（无边框窗口）
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)

        # 加载配置
        self.config_file = "translator_config.json"
        self.saved_config = self.load_config()

        # 获取模型列表
        self.model_list = self.saved_config.get('model_list',
                                                ['deepseek-chat', 'deepseek-reasoner', 'qwen-turbo', 'qwen-plus', 'qwen-max-latest',
                                                 'moonshot-v1-32k', 'doubao-lite-128k', 'gpt-4o'])

        # 设置UI
        self.setup_ui()

        # 初始化翻译线程
        self.translation_thread = None

        # 使窗口居中显示
        self.center_window()
        icon_path = resource_path(os.path.join('assets', 'icon.ico'))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    def center_window(self):
        """使窗口在屏幕中央显示"""
        screen_geometry = QApplication.primaryScreen().geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

    def load_config(self) -> dict:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
        return {}

    def save_config(self):
        """保存配置到文件"""
        config = {
            'api_host': self.api_host_input.text(),
            'api_key': self.api_key_input.text(),
            'model': self.model_combo.currentText(),
            'source_lang': self.source_lang_input.text(),
            'target_lang': self.target_lang_input.text(),
            'delay': float(self.delay_input.text() or 1.0),
            'temperature': float(self.temperature_input.text() or 0.7),
            'batch_size': int(self.batch_size_input.text() or 30),
            'show_original': self.show_original_cb.isChecked(),
            'clean_punctuation': self.clean_punct_cb.isChecked(),
            'model_list': self.model_list
        }
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def setup_ui(self):
        """设置用户界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === 自定义标题栏 ===
        title_bar = QFrame()
        title_bar.setStyleSheet("background-color: #262626;")
        title_bar.setFixedHeight(30)

        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)

        # 标题
        title_label = QLabel("大模型字幕翻译小助手")
        title_label.setStyleSheet("color: white; font-weight: bold;")

        # 控制按钮
        minimize_btn = TitleBarButton("#FDBC2C", "#BD8D21")
        minimize_btn.setText("－")
        minimize_btn.clicked.connect(self.showMinimized)

        close_btn = TitleBarButton("#FF5F57", "#BF4542")
        close_btn.setText("×")
        close_btn.clicked.connect(self.close)

        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(minimize_btn)
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
        version_label = QLabel("v1.1.0")
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

        browse_button = QPushButton("打开地址")
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

        # === 选项卡 ===
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border: 1px solid #cccccc;
                border-bottom: none;
            }
        """)

        # API设置选项卡
        api_tab = QWidget()
        api_layout = QGridLayout(api_tab)
        api_layout.setContentsMargins(15, 15, 15, 15)

        # API Host
        api_layout.addWidget(QLabel("API HOST:"), 0, 0)
        self.api_host_input = QLineEdit(self.saved_config.get('api_host', "https://api.deepseek.com"))
        self.api_host_input.setToolTip("API服务地址，例如：https://api.deepseek.com")
        api_layout.addWidget(self.api_host_input, 0, 1, 1, 2)

        # API Key
        api_layout.addWidget(QLabel("API Key:"), 1, 0)
        self.api_key_input = QLineEdit(self.saved_config.get('api_key', ""))
        self.api_key_input.setToolTip("你的API密钥，用于访问AI服务")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        api_layout.addWidget(self.api_key_input, 1, 1)

        # 显示/隐藏API Key按钮
        self.toggle_key_btn = QPushButton("显示")
        self.toggle_key_btn.clicked.connect(self.toggle_api_key)
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
        self.model_combo = QComboBox()
        self.model_combo.setToolTip("选择要使用的AI模型")
        self.model_combo.addItems(self.model_list)
        current_model = self.saved_config.get('model', self.model_list[0] if self.model_list else "")
        if current_model in self.model_list:
            self.model_combo.setCurrentText(current_model)
        api_layout.addWidget(self.model_combo, 2, 1)

        # 编辑模型列表按钮
        edit_models_btn = QPushButton("编辑列表")
        edit_models_btn.clicked.connect(self.edit_model_list)
        edit_models_btn.setStyleSheet("""
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
        api_layout.addWidget(edit_models_btn, 2, 2)

        tabs.addTab(api_tab, "API 设置")

        # 翻译设置选项卡
        trans_tab = QWidget()
        trans_layout = QGridLayout(trans_tab)
        trans_layout.setContentsMargins(15, 15, 15, 15)

        # 源语言和目标语言
        trans_layout.addWidget(QLabel("原文语言："), 0, 0)
        self.source_lang_input = QLineEdit(self.saved_config.get('source_lang', "English"))
        trans_layout.addWidget(self.source_lang_input, 0, 1)

        trans_layout.addWidget(QLabel("译文语言："), 0, 2)
        self.target_lang_input = QLineEdit(self.saved_config.get('target_lang', "Chinese"))
        trans_layout.addWidget(self.target_lang_input, 0, 3)

        # 延迟和温度
        trans_layout.addWidget(QLabel("延迟（秒）:"), 1, 0)
        self.delay_input = QLineEdit(str(self.saved_config.get('delay', 1.0)))
        self.delay_input.setToolTip("API请求之间的延迟时间，单位为秒")
        trans_layout.addWidget(self.delay_input, 1, 1)

        trans_layout.addWidget(QLabel("温度："), 1, 2)
        self.temperature_input = QLineEdit(str(self.saved_config.get('temperature', 0.7)))
        self.temperature_input.setToolTip("温度参数控制翻译的创造性，值越高创造性越强")
        trans_layout.addWidget(self.temperature_input, 1, 3)

        # 显示原文和清理标点选项
        self.show_original_cb = QCheckBox("显示原文（在翻译下方保留原始字幕）")
        self.show_original_cb.setChecked(self.saved_config.get('show_original', True))
        self.show_original_cb.setToolTip("启用后，原始字幕将在翻译下方保留")
        trans_layout.addWidget(self.show_original_cb, 2, 0, 1, 2)

        self.clean_punct_cb = QCheckBox("清理标点符号（将标点替换为空格）")
        self.clean_punct_cb.setChecked(self.saved_config.get('clean_punctuation', True))
        self.clean_punct_cb.setToolTip("对于机器翻译识别可能更好，但对某些语言可能不适用")
        trans_layout.addWidget(self.clean_punct_cb, 2, 2, 1, 2)

        # 附加提示词
        trans_layout.addWidget(QLabel("额外信息："), 3, 0)
        self.additional_prompt_input = QLineEdit()
        self.additional_prompt_input.setToolTip("向AI添加额外的上下文信息，例如：这是一部科幻电影")
        trans_layout.addWidget(self.additional_prompt_input, 3, 1, 1, 3)

        tabs.addTab(trans_tab, "翻译设置")

        # 高级设置选项卡
        adv_tab = QWidget()
        adv_layout = QVBoxLayout(adv_tab)
        adv_layout.setContentsMargins(15, 15, 15, 15)

        batch_size_layout = QHBoxLayout()
        batch_size_layout.addWidget(QLabel("每批字幕数量（不建议轻易改动）："))
        self.batch_size_input = QLineEdit(str(self.saved_config.get('batch_size', 30)))
        self.batch_size_input.setToolTip("每次发送给API处理的字幕句子数量，值越大翻译速度越快，但可能会超出API限制")
        batch_size_layout.addWidget(self.batch_size_input)
        adv_layout.addLayout(batch_size_layout)

        adv_layout.addWidget(QLabel("自定义系统提示词（请勿轻易改动！）："))

        self.custom_prompt_text = QTextEdit()
        self.custom_prompt_text.setToolTip("高级用户可以自定义系统提示词，使用{{target_lang}}和{{additional}}作为变量")
        self.default_prompt = """You are a professional subtitle translator.
You will only receive subtitles and are only required to translate, no need for any replies.
Note: {{additional}}
Translate the input text into {{target_lang}}.
Do not merge sentences, translate them individually.
Return only the translated text, no additional explanations.
Keep the translation natural and fluent."""
        self.custom_prompt_text.setPlainText(self.default_prompt)
        self.custom_prompt_text.setFont(QFont("Consolas", 10))
        adv_layout.addWidget(self.custom_prompt_text)

        reset_button = QPushButton("还原为默认")
        reset_button.clicked.connect(self.reset_prompt)
        reset_button.setStyleSheet("""
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
        adv_layout.addWidget(reset_button, alignment=Qt.AlignmentFlag.AlignLeft)

        tabs.addTab(adv_tab, "高级设置")

        content_layout.addWidget(tabs)

        # === 进度显示区域 ===
        progress_group = QFrame()
        progress_group.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
        """)
        progress_layout = QVBoxLayout(progress_group)

        progress_label = QLabel("翻译进度")
        progress_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        progress_layout.addWidget(progress_label)

        self.progress_text = QTextEdit()
        self.progress_text.setReadOnly(True)
        self.progress_text.setFont(QFont("Consolas", 10))
        progress_layout.addWidget(self.progress_text)

        content_layout.addWidget(progress_group)

        # === 控制按钮 ===
        button_layout = QHBoxLayout()

        # 关于按钮
        about_button = QPushButton("关于")
        about_button.clicked.connect(self.show_about)
        about_button.setStyleSheet("""
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

        # 支持作者按钮
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
        self.start_button = QPushButton("开始翻译")
        self.start_button.clicked.connect(self.start_translation)
        self.start_button.setStyleSheet("""
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
            QPushButton:disabled {
                background-color: #a8e9b6;
            }
        """)

        button_layout.addWidget(about_button)
        button_layout.addWidget(donation_button)
        button_layout.addStretch()
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.start_button)

        content_layout.addLayout(button_layout)

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

    def toggle_api_key(self):
        """切换API密钥显示/隐藏"""
        if self.api_key_input.echoMode() == QLineEdit.EchoMode.Password:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_key_btn.setText("隐藏")
        else:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_key_btn.setText("显示")

    def edit_model_list(self):
        """编辑模型列表"""
        # 创建对话框
        dialog = QWidget(self, Qt.WindowType.Window)
        dialog.setWindowTitle("编辑模型列表")
        dialog.setFixedSize(450, 350)
        dialog.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)

        layout = QVBoxLayout(dialog)

        # 标题
        title = QLabel("可用模型")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)

        # 模型列表
        models_scroll = QScrollArea()
        models_scroll.setWidgetResizable(True)
        models_scroll.setFrameShape(QFrame.Shape.NoFrame)

        models_container = QWidget()
        models_layout = QVBoxLayout(models_container)

        # 使用当前模型列表初始化
        self.model_checkboxes = {}
        for model in sorted(self.model_list):
            cb = QCheckBox(model)
            cb.setChecked(True)
            self.model_checkboxes[model] = cb
            models_layout.addWidget(cb)

        models_scroll.setWidget(models_container)
        layout.addWidget(models_scroll)

        # 添加新模型的UI
        input_layout = QHBoxLayout()

        self.new_model_input = QLineEdit()
        self.new_model_input.setPlaceholderText("Add new model...")

        add_button = QPushButton("添加")
        add_button.clicked.connect(self.add_new_model)
        add_button.setStyleSheet("""
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

        input_layout.addWidget(self.new_model_input)
        input_layout.addWidget(add_button)

        layout.addLayout(input_layout)

        # 按钮
        buttons_layout = QHBoxLayout()

        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(dialog.close)
        cancel_button.setStyleSheet("""
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

        save_button = QPushButton("保存")
        save_button.clicked.connect(lambda: self.save_models(dialog))
        save_button.setStyleSheet("""
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

        buttons_layout.addWidget(cancel_button)
        buttons_layout.addWidget(save_button)

        layout.addLayout(buttons_layout)

        # 保存对话框引用并显示
        self.models_dialog = dialog
        self.models_container = models_container
        self.models_layout = models_layout
        dialog.show()

    def add_new_model(self):
        """添加新模型到列表"""
        model_name = self.new_model_input.text().strip()
        if model_name and model_name not in self.model_checkboxes:
            cb = QCheckBox(model_name)
            cb.setChecked(True)
            self.model_checkboxes[model_name] = cb
            self.models_layout.addWidget(cb)
            self.new_model_input.clear()

    def save_models(self, dialog):
        """保存模型列表"""
        selected_models = [model for model, cb in self.model_checkboxes.items() if cb.isChecked()]
        if not selected_models:
            QMessageBox.warning(self, "警告", "请最少选择一种模型")
            return

        self.model_list = selected_models

        # 更新下拉菜单
        current_model = self.model_combo.currentText()
        self.model_combo.clear()
        self.model_combo.addItems(self.model_list)

        # 如果当前选中的模型还在列表中，则保持选中
        if current_model in self.model_list:
            self.model_combo.setCurrentText(current_model)

        # 保存配置
        self.save_config()
        dialog.close()

    def reset_prompt(self):
        """重置为默认提示词"""
        self.custom_prompt_text.setPlainText(self.default_prompt)

    def browse_file(self):
        """打开文件选择对话框"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择字幕文件", "", "SRT files (*.srt);;All files (*.*)"
        )
        if file_path:
            self.file_path_input.setText(file_path)

    def show_about(self):
        """显示关于对话框"""
        about_dialog = AboutDialog(self)
        about_dialog.show()

    def show_donation(self):
        """显示捐赠对话框"""
        donation_dialog = DonationDialog(self)
        donation_dialog.show()

    def log_progress(self, message):
        """记录进度信息"""
        self.progress_text.append(message)
        # 滚动到底部
        scrollbar = self.progress_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def start_translation(self):
        """开始翻译"""
        if not self.file_path_input.text():
            QMessageBox.critical(self, "错误", "请选择一个字幕源文件。")
            return

        if not self.api_key_input.text():
            QMessageBox.critical(self, "错误", "请输入API Key。")
            return

        # 检查必填字段
        try:
            float(self.delay_input.text())
            float(self.temperature_input.text())
        except ValueError:
            QMessageBox.critical(self, "错误", "延迟和温度必须是有效的数字。")
            return

        try:
            float(self.delay_input.text())
            float(self.temperature_input.text())
            batch_size = int(self.batch_size_input.text())
            if batch_size <= 0:
                raise ValueError("批次大小必须为正整数")
        except ValueError:
            QMessageBox.critical(self, "错误", "延迟、温度和批次大小必须是有效的数字。批次大小必须为正整数。")
            return
        output_path, _ = QFileDialog.getSaveFileName(
            self, "保存翻译字幕", "", "SRT files (*.srt);;All files (*.*)"
        )
        if not output_path:
            return  # 用户取消了保存对话框

        # 创建配置
        config = TranslationConfig(
            source_lang=self.source_lang_input.text(),
            target_lang=self.target_lang_input.text(),
            delay=float(self.delay_input.text()),
            temperature=float(self.temperature_input.text()),
            api_host=self.api_host_input.text(),
            api_key=self.api_key_input.text(),
            model=self.model_combo.currentText(),
            additional_prompt=self.additional_prompt_input.text(),
            batch_size=batch_size,
            show_original=self.show_original_cb.isChecked(),
            clean_punctuation=self.clean_punct_cb.isChecked(),
            custom_prompt=self.custom_prompt_text.toPlainText()
        )

        # 保存配置
        self.save_config()

        # 清空进度文本
        self.progress_text.clear()

        # 创建并启动翻译线程
        self.translation_thread = TranslationWorker(config, self.file_path_input.text(), output_path)
        self.translation_thread.signals.progress.connect(self.log_progress)
        self.translation_thread.signals.finished.connect(self.translation_finished)
        self.translation_thread.signals.error.connect(self.translation_error)

        # 更新按钮状态
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        # 启动线程
        self.translation_thread.start()

    def stop_translation(self):
        """停止翻译"""
        if self.translation_thread and self.translation_thread.isRunning():
            self.translation_thread.stop()
            self.log_progress("正在停止翻译并保存当前进度...")

            # 为了让用户知道保存位置的信息
            if hasattr(self.translation_thread, 'temp_output_path') and os.path.exists(
                    self.translation_thread.temp_output_path):
                self.log_progress(f"已保存翻译进度到临时文件: {self.translation_thread.temp_output_path}")
                self.log_progress(
                    f"当前完成进度: 批次 {self.translation_thread.current_batch}/{self.translation_thread.total_batches}")

                # 可以考虑复制临时文件到正式输出文件
                try:
                    import shutil
                    shutil.copy2(self.translation_thread.temp_output_path, self.translation_thread.output_path)
                    self.log_progress(f"已将当前进度保存到最终文件: {self.translation_thread.output_path}")
                except Exception as e:
                    self.log_progress(f"保存最终文件时出错: {str(e)}")

    def translation_finished(self):
        """翻译完成的处理"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def translation_error(self, message):
        """翻译错误的处理"""
        self.log_progress(f"\n错误: {message}")
        QMessageBox.critical(self, "翻译错误", f"翻译过程中出现错误:\n\n{message}\n\n请检查日志了解详情。")
        self.translation_finished()

    def closeEvent(self, event):
        """处理窗口关闭事件"""
        if self.translation_thread and self.translation_thread.isRunning():
            # 检查是否有临时文件
            has_temp_file = (hasattr(self.translation_thread, 'temp_output_path') and
                             os.path.exists(self.translation_thread.temp_output_path))

            message = "翻译正在进行中。确定要退出吗？"
            if has_temp_file:
                message += f"\n\n当前翻译进度已保存到:\n{self.translation_thread.temp_output_path}"

            reply = QMessageBox.question(
                self, "确认", message,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # 如果用户确认退出，先保存进度
                self.stop_translation()
                self.translation_thread.wait()  # 等待线程结束
                event.accept()
            else:
                event.ignore()
        else:
            self.save_config()
            event.accept()


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

    window = SubtitleTranslatorApp()
    window.show()

    sys.exit(app.exec())