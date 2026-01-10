import sys
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, Qt
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QTabWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QPlainTextEdit,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QCheckBox,
    QMessageBox,
    QComboBox,
    QFileDialog,
)
from PyQt6.QtGui import QPixmap
import jai_assistant as jai
from jai_assistant import execute_command, UserSession
from jai_calendar import CalendarManager
import tts
import stt
from jai_media import handle_media_command
try:
    import muse
except Exception:
    muse = None


class CommandWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, session: UserSession, command: str):
        super().__init__()
        self.session = session
        self.command = command

    def run(self):
        try:
            result = execute_command(self.command, self.session, suppress_tts=True)
            self.finished.emit(result or "")
        except Exception as e:
            self.error.emit(str(e))


class VoiceControlWorker(QThread):
    recognized = pyqtSignal(str)
    error = pyqtSignal(str)
    stopped = pyqtSignal()

    def __init__(self, language: str = "en-US"):
        super().__init__()
        self.language = language
        self._running = True

    def stop(self):
        self._running = False

    def run(self):
        try:
            while self._running:
                try:
                    txt = stt.listen_for_command(timeout=15, language=self.language)
                    if not self._running:
                        break
                    if txt:
                        self.recognized.emit(txt)
                    else:
                        self.error.emit("No speech recognized")
                except Exception as e:
                    self.error.emit(str(e))
        finally:
            self.stopped.emit()


class STTWorker(QThread):
    recognized = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, timeout: int = 6, language: str = "en-US"):
        super().__init__()
        self.timeout = timeout
        self.language = language

    def run(self):
        try:
            # Gracefully handle missing SpeechRecognition dependency
            if getattr(stt, "sr", None) is None:
                self.error.emit("SpeechRecognition not available. Install: pip install SpeechRecognition")
                return
            text = stt.listen_for_command(timeout=self.timeout, language=self.language)
            if text:
                self.recognized.emit(text)
            else:
                self.error.emit("No speech recognized")
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JAI Assistant GUI")
        self.resize(1000, 720)

        self.session = UserSession("admin")
        self.calendar = getattr(jai, "calendar_manager", None) or CalendarManager()

        self.stt_language = "en-US"
        try:
            tts.TTS_PREFERRED_VOICE = "david"
        except Exception:
            pass
        self.voice_worker = None

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self._init_assistant_tab()
        self._init_calendar_tab()
        self._init_memory_tab()
        self._init_logs_tab()
        self._init_music_tab()
        self._init_muse_tab()
        self._init_settings_tab()

        self.log_timer = QTimer(self)
        self.log_timer.timeout.connect(self._refresh_logs)
        self.log_timer.start(2000)

    def _init_assistant_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        self.chat_view = QPlainTextEdit()
        self.chat_view.setReadOnly(True)
        layout.addWidget(self.chat_view)

        self.task_progress = QProgressBar()
        self.task_progress.setRange(0, 100)
        self.task_progress.setValue(100)
        self.task_progress.setTextVisible(True)
        self.task_progress.setFormat("Ready")
        layout.addWidget(self.task_progress)

        row = QHBoxLayout()
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("Type a command (e.g., 'what time is it', 'news', 'remind me to call mom at 3pm')")
        row.addWidget(self.input_line, 1)

        self.speak_checkbox = QCheckBox("Speak response")
        self.speak_checkbox.setChecked(True)
        row.addWidget(self.speak_checkbox)

        self.listen_btn = QPushButton("🎤 Speak")
        self.listen_btn.clicked.connect(self._on_listen_clicked)
        row.addWidget(self.listen_btn)

        # Disable Speak if SpeechRecognition is not available
        if getattr(stt, "sr", None) is None:
            self.listen_btn.setEnabled(False)
            self.listen_btn.setToolTip("SpeechRecognition not available. Install: pip install SpeechRecognition")

        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self._on_send_clicked)
        row.addWidget(self.send_btn)

        layout.addLayout(row)
        self.tabs.addTab(page, "Assistant")

    def _init_music_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        row1 = QHBoxLayout()
        self.music_song_input = QLineEdit()
        self.music_song_input.setPlaceholderText("Song or query (e.g., 'Shape of You' or 'play song Despacito')")
        row1.addWidget(self.music_song_input, 2)
        self.music_play_btn = QPushButton("Play Song")
        self.music_play_btn.clicked.connect(self._on_music_play_clicked)
        row1.addWidget(self.music_play_btn)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.music_playpause_btn = QPushButton("Play/Pause")
        self.music_playpause_btn.clicked.connect(lambda: self._handle_media("pause"))
        row2.addWidget(self.music_playpause_btn)
        self.music_next_btn = QPushButton("Next")
        self.music_next_btn.clicked.connect(lambda: self._handle_media("next track"))
        row2.addWidget(self.music_next_btn)
        self.music_prev_btn = QPushButton("Previous")
        self.music_prev_btn.clicked.connect(lambda: self._handle_media("previous track"))
        row2.addWidget(self.music_prev_btn)
        layout.addLayout(row2)

        row3 = QHBoxLayout()
        self.vol_down_btn = QPushButton("Vol -")
        self.vol_down_btn.clicked.connect(lambda: self._handle_media("volume down"))
        row3.addWidget(self.vol_down_btn)
        self.vol_up_btn = QPushButton("Vol +")
        self.vol_up_btn.clicked.connect(lambda: self._handle_media("volume up"))
        row3.addWidget(self.vol_up_btn)
        self.mute_btn = QPushButton("Mute")
        self.mute_btn.clicked.connect(lambda: self._handle_media("mute"))
        row3.addWidget(self.mute_btn)
        self.unmute_btn = QPushButton("Unmute")
        self.unmute_btn.clicked.connect(lambda: self._handle_media("unmute"))
        row3.addWidget(self.unmute_btn)
        layout.addLayout(row3)

        row4 = QHBoxLayout()
        self.yt_query_input = QLineEdit()
        self.yt_query_input.setPlaceholderText("YouTube search (e.g., 'lofi beats')")
        row4.addWidget(self.yt_query_input, 2)
        self.yt_search_btn = QPushButton("Search YouTube")
        self.yt_search_btn.clicked.connect(self._on_youtube_search)
        row4.addWidget(self.yt_search_btn)
        layout.addLayout(row4)

        self.tabs.addTab(page, "Music")

    def _init_muse_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        row1 = QHBoxLayout()
        self.muse_prompt_input = QLineEdit()
        self.muse_prompt_input.setPlaceholderText("Image prompt")
        row1.addWidget(self.muse_prompt_input, 2)
        self.muse_size_combo = QComboBox()
        self.muse_size_combo.addItems(["512x512", "768x768", "1024x1024"])
        row1.addWidget(self.muse_size_combo)
        self.muse_generate_btn = QPushButton("Generate Image")
        self.muse_generate_btn.clicked.connect(self._on_muse_generate)
        row1.addWidget(self.muse_generate_btn)
        layout.addLayout(row1)

        self.muse_image_label = QLabel()
        self.muse_image_label.setMinimumHeight(280)
        self.muse_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.muse_image_label)

        row2 = QHBoxLayout()
        self.muse_audio_input = QLineEdit()
        self.muse_audio_input.setPlaceholderText("Audio file path (.wav)")
        row2.addWidget(self.muse_audio_input, 2)
        self.muse_audio_browse = QPushButton("Browse")
        self.muse_audio_browse.clicked.connect(self._on_muse_browse_audio)
        row2.addWidget(self.muse_audio_browse)
        self.muse_transcribe_btn = QPushButton("Transcribe")
        self.muse_transcribe_btn.clicked.connect(self._on_muse_transcribe)
        row2.addWidget(self.muse_transcribe_btn)
        layout.addLayout(row2)

        self.muse_transcript_view = QPlainTextEdit()
        self.muse_transcript_view.setReadOnly(True)
        layout.addWidget(self.muse_transcript_view)

        row3 = QHBoxLayout()
        self.muse_detect_input = QLineEdit()
        self.muse_detect_input.setPlaceholderText("Image file path")
        row3.addWidget(self.muse_detect_input, 2)
        self.muse_detect_browse = QPushButton("Browse")
        self.muse_detect_browse.clicked.connect(self._on_muse_browse_image)
        row3.addWidget(self.muse_detect_browse)
        self.muse_detect_btn = QPushButton("Detect Objects")
        self.muse_detect_btn.clicked.connect(self._on_muse_detect)
        row3.addWidget(self.muse_detect_btn)
        layout.addLayout(row3)

        self.muse_detect_label = QLabel()
        self.muse_detect_label.setMinimumHeight(220)
        self.muse_detect_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.muse_detect_label)

        self.muse_detect_info = QPlainTextEdit()
        self.muse_detect_info.setReadOnly(True)
        layout.addWidget(self.muse_detect_info)

        row4 = QHBoxLayout()
        self.muse_search_input = QLineEdit()
        self.muse_search_input.setPlaceholderText("Image search query")
        row4.addWidget(self.muse_search_input, 2)
        self.muse_search_btn = QPushButton("Search Images")
        self.muse_search_btn.clicked.connect(self._on_muse_search)
        row4.addWidget(self.muse_search_btn)
        layout.addLayout(row4)

        self.muse_search_results = QPlainTextEdit()
        self.muse_search_results.setReadOnly(True)
        layout.addWidget(self.muse_search_results)

        self.tabs.addTab(page, "Muse")

    def _set_image_label(self, label: QLabel, path: Path):
        try:
            pix = QPixmap(str(path))
            if not pix.isNull():
                w = min(640, pix.width())
                label.setPixmap(pix.scaledToWidth(w, Qt.TransformationMode.SmoothTransformation))
        except Exception:
            pass

    def _on_muse_generate(self):
        if muse is None:
            self._append_chat("Muse", "Muse is not available. Install dependencies and restart: pillow, opencv-python, numpy, duckduckgo-search, openai")
            return
        prompt = self.muse_prompt_input.text().strip()
        if not prompt:
            return
        self._set_busy(True, "Generating…")
        try:
            size = self.muse_size_combo.currentText()
            p = muse.generate_image(prompt, size=size)
            self._append_chat("Muse", f"Image saved: {p}")
            self._set_image_label(self.muse_image_label, Path(p))
        except Exception as e:
            self._append_chat("Muse", str(e))
        self._set_busy(False)

    def _on_muse_browse_audio(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Select audio", "", "Audio Files (*.wav *.mp3 *.flac);;All Files (*)")
        if fn:
            self.muse_audio_input.setText(fn)

    def _on_muse_transcribe(self):
        if muse is None:
            self._append_chat("Muse", "Muse is not available. Install dependencies and restart: pillow, opencv-python, numpy, duckduckgo-search, openai")
            return
        fp = self.muse_audio_input.text().strip()
        if not fp:
            return
        self._set_busy(True, "Transcribing…")
        try:
            txt = muse.transcribe_audio_file(fp)
            self.muse_transcript_view.setPlainText(txt)
            self._append_chat("Muse", "Transcription complete")
        except Exception as e:
            self._append_chat("Muse", str(e))
        self._set_busy(False)

    def _on_muse_browse_image(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Select image", "", "Images (*.png *.jpg *.jpeg *.bmp);;All Files (*)")
        if fn:
            self.muse_detect_input.setText(fn)

    def _on_muse_detect(self):
        if muse is None:
            self._append_chat("Muse", "Muse is not available. Install dependencies and restart: pillow, opencv-python, numpy, duckduckgo-search, openai")
            return
        fp = self.muse_detect_input.text().strip()
        if not fp:
            return
        self._set_busy(True, "Analyzing…")
        try:
            out, labels = muse.detect_objects_in_image(fp)
            if out:
                self._set_image_label(self.muse_detect_label, Path(out))
            self.muse_detect_info.setPlainText(", ".join(labels) if labels else "")
            msg = f"Annotated: {out}" if out else "Done"
            self._append_chat("Muse", msg)
        except Exception as e:
            self._append_chat("Muse", str(e))
        self._set_busy(False)

    def _on_muse_search(self):
        if muse is None:
            self._append_chat("Muse", "Muse is not available. Install dependencies and restart: pillow, opencv-python, numpy, duckduckgo-search, openai")
            return
        q = self.muse_search_input.text().strip()
        if not q:
            return
        self._set_busy(True, "Searching…")
        try:
            paths = muse.image_search(q, max_results=5)
            if paths:
                text = "\n".join(str(p) for p in paths)
                self.muse_search_results.setPlainText(text)
                self._append_chat("Muse", f"Saved {len(paths)} images")
            else:
                self.muse_search_results.setPlainText("")
                self._append_chat("Muse", "No results")
        except Exception as e:
            self._append_chat("Muse", str(e))
        self._set_busy(False)

    def _init_settings_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("STT Language"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("English (US)", userData="en-US")
        self.lang_combo.addItem("Hindi", userData="hi-IN")
        self.lang_combo.addItem("Arabic", userData="ar-SA")
        self.lang_combo.addItem("Urdu", userData="ur-PK")
        self.lang_combo.addItem("French", userData="fr-FR")
        self.lang_combo.currentIndexChanged.connect(self._on_language_changed)
        row1.addWidget(self.lang_combo, 1)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Preferred Voice Keyword"))
        self.voice_pref_input = QLineEdit()
        self.voice_pref_input.setPlaceholderText("e.g., 'david' for male")
        self.voice_pref_input.setText("david")
        row2.addWidget(self.voice_pref_input, 1)
        self.voice_apply_btn = QPushButton("Apply Voice")
        self.voice_apply_btn.clicked.connect(self._on_apply_voice_pref)
        row2.addWidget(self.voice_apply_btn)
        layout.addLayout(row2)

        row3 = QHBoxLayout()
        self.voice_control_btn = QPushButton("Start Voice Control")
        self.voice_control_btn.clicked.connect(self._on_toggle_voice_control)
        row3.addWidget(self.voice_control_btn)
        layout.addLayout(row3)

        # Disable continuous voice control if SpeechRecognition is unavailable
        if getattr(stt, "sr", None) is None:
            self.voice_control_btn.setEnabled(False)
            self.voice_control_btn.setToolTip("SpeechRecognition not available. Install: pip install SpeechRecognition & PyAudio")

        self.tabs.addTab(page, "Settings")

    def _on_send_clicked(self):
        text = self.input_line.text().strip()
        if not text:
            return
        self._append_chat("You", text)
        self._set_busy(True, "Processing…")
        self.send_btn.setEnabled(False)
        self.listen_btn.setEnabled(False)
        self.input_line.setEnabled(False)

        self.cmd_worker = CommandWorker(self.session, text)
        self.cmd_worker.finished.connect(self._on_command_finished)
        self.cmd_worker.error.connect(self._on_command_error)
        self.cmd_worker.start()

    def _on_command_finished(self, result: str):
        self._append_chat("JAI", result or "")
        if self.speak_checkbox.isChecked() and result:
            try:
                tts.speak(result)
            except Exception:
                pass
        self._set_busy(False)
        self.send_btn.setEnabled(True)
        self.listen_btn.setEnabled(True)
        self.input_line.setEnabled(True)
        self.input_line.setText("")

    def _on_command_error(self, err: str):
        self._append_chat("Error", err)
        self._set_busy(False)
        self.send_btn.setEnabled(True)
        self.listen_btn.setEnabled(True)
        self.input_line.setEnabled(True)

    def _on_listen_clicked(self):
        self._set_busy(True, "Listening…")
        self.send_btn.setEnabled(False)
        self.listen_btn.setEnabled(False)
        self.input_line.setEnabled(False)

        self.stt_worker = STTWorker(timeout=15, language=self.stt_language)
        self.stt_worker.recognized.connect(self._on_stt_recognized)
        self.stt_worker.error.connect(self._on_stt_error)
        self.stt_worker.start()

    def _on_stt_recognized(self, text: str):
        self.input_line.setText(text)
        self._set_busy(False)
        self.send_btn.setEnabled(True)
        self.listen_btn.setEnabled(True)
        self.input_line.setEnabled(True)
        self._on_send_clicked()

    def _on_stt_error(self, err: str):
        self._append_chat("Voice", err)
        self._set_busy(False)
        self.send_btn.setEnabled(True)
        self.listen_btn.setEnabled(True)
        self.input_line.setEnabled(True)

    def _append_chat(self, who: str, msg: str):
        self.chat_view.appendPlainText(f"{who}: {msg}")
        sb = self.chat_view.verticalScrollBar()
        sb.setValue(sb.maximum())


    def _speak(self, text: str):
        if self.speak_checkbox.isChecked() and text:
            try:
                tts.speak(text)
            except Exception:
                pass


    def _handle_media(self, command: str):
        try:
            res = handle_media_command(command) or ""
            if res:
                self._append_chat("Media", res)
                self._speak(res)
        except Exception as e:
            self._append_chat("Media", str(e))

    def _on_music_play_clicked(self):
        text = self.music_song_input.text().strip()
        if text:
            if not text.lower().startswith("play"):
                cmd = f"play song {text}"
            else:
                cmd = text
            self._handle_media(cmd)

    def _on_youtube_search(self):
        q = self.yt_query_input.text().strip()
        if q:
            self._handle_media(f"search youtube for {q}")

    def _set_busy(self, busy: bool, text: str | None = None):
        if busy:
            self.task_progress.setRange(0, 0)
            if text:
                self.task_progress.setFormat(text)
        else:
            self.task_progress.setRange(0, 100)
            self.task_progress.setValue(100)
            self.task_progress.setFormat("Ready")

    def _init_calendar_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        layout.addWidget(QLabel("Pending Reminders"))
        self.reminders_list = QListWidget()
        layout.addWidget(self.reminders_list)

        form_row1 = QHBoxLayout()
        self.rem_title = QLineEdit()
        self.rem_title.setPlaceholderText("Reminder title")
        form_row1.addWidget(self.rem_title, 2)

        self.rem_time_expr = QLineEdit()
        self.rem_time_expr.setPlaceholderText("Time (e.g., 'in 10 minutes', 'tomorrow 3 pm', 'at 9:20 pm')")
        form_row1.addWidget(self.rem_time_expr, 2)

        self.rem_add_btn = QPushButton("Add Reminder")
        self.rem_add_btn.clicked.connect(self._on_add_reminder)
        form_row1.addWidget(self.rem_add_btn)
        layout.addLayout(form_row1)

        row2 = QHBoxLayout()
        self.rem_refresh_btn = QPushButton("Refresh")
        self.rem_refresh_btn.clicked.connect(self._refresh_reminders)
        row2.addWidget(self.rem_refresh_btn)

        self.rem_clear_btn = QPushButton("Delete All Pending")
        self.rem_clear_btn.clicked.connect(self._clear_pending_reminders)
        row2.addWidget(self.rem_clear_btn)
        layout.addLayout(row2)

        self.tabs.addTab(page, "Calendar")
        self._refresh_reminders()

    def _refresh_reminders(self):
        try:
            self.reminders_list.clear()
            reminders = self.calendar.get_pending_reminders()
            for r in reminders:
                item = QListWidgetItem(f"{r['title']} @ {r['remind_at']}")
                self.reminders_list.addItem(item)
        except Exception as e:
            QMessageBox.warning(self, "Calendar", f"Failed to load reminders: {e}")

    def _on_add_reminder(self):
        title = self.rem_title.text().strip()
        expr = self.rem_time_expr.text().strip()
        if not title or not expr:
            QMessageBox.information(self, "Calendar", "Please enter title and time expression.")
            return
        try:
            dt = self.calendar.parse_relative_time(expr)
            if not dt:
                QMessageBox.warning(self, "Calendar", f"Could not parse time: {expr}")
                return
            self.calendar.add_reminder(title, dt)
            self.rem_title.setText("")
            self.rem_time_expr.setText("")
            self._refresh_reminders()
        except Exception as e:
            QMessageBox.warning(self, "Calendar", f"Failed to add reminder: {e}")

    def _clear_pending_reminders(self):
        try:
            count = self.calendar.delete_all_reminders()
            QMessageBox.information(self, "Calendar", f"Deleted {count} pending reminders.")
            self._refresh_reminders()
        except Exception as e:
            QMessageBox.warning(self, "Calendar", f"Failed to delete reminders: {e}")

    def _init_memory_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        layout.addWidget(QLabel("Short-Term Memory (last 10)"))
        self.st_table = QTableWidget(0, 2)
        self.st_table.setHorizontalHeaderLabels(["Timestamp", "Content"])
        self.st_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.st_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.st_table)

        layout.addWidget(QLabel("Long-Term Memory"))
        self.lt_table = QTableWidget(0, 3)
        self.lt_table.setHorizontalHeaderLabels(["Key", "Value", "Importance"])
        self.lt_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.lt_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.lt_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.lt_table)

        form1 = QHBoxLayout()
        self.mem_key = QLineEdit()
        self.mem_key.setPlaceholderText("Key")
        form1.addWidget(self.mem_key)
        self.mem_value = QLineEdit()
        self.mem_value.setPlaceholderText("Value")
        form1.addWidget(self.mem_value, 1)
        self.mem_add_btn = QPushButton("Remember/Update")
        self.mem_add_btn.clicked.connect(self._on_mem_add_update)
        form1.addWidget(self.mem_add_btn)
        layout.addLayout(form1)

        form2 = QHBoxLayout()
        self.mem_forget_key = QLineEdit()
        self.mem_forget_key.setPlaceholderText("Key to forget")
        form2.addWidget(self.mem_forget_key)
        self.mem_forget_btn = QPushButton("Forget")
        self.mem_forget_btn.clicked.connect(self._on_mem_forget)
        form2.addWidget(self.mem_forget_btn)
        self.mem_refresh_btn = QPushButton("Refresh")
        self.mem_refresh_btn.clicked.connect(self._refresh_memory_tables)
        form2.addWidget(self.mem_refresh_btn)
        layout.addLayout(form2)

        self.tabs.addTab(page, "Memory")
        self._refresh_memory_tables()

    def _refresh_memory_tables(self):
        try:
            st_items = self.session.memory.get_short_term(limit=10)
            self.st_table.setRowCount(0)
            for item in st_items:
                row = self.st_table.rowCount()
                self.st_table.insertRow(row)
                self.st_table.setItem(row, 0, QTableWidgetItem(item.get("timestamp", "")))
                content = item.get("content", "")
                if isinstance(content, dict):
                    content = str(content)
                self.st_table.setItem(row, 1, QTableWidgetItem(content))
        except Exception as e:
            QMessageBox.warning(self, "Memory", f"Failed to load short-term memory: {e}")

        try:
            lt_items = self.session.memory.get_long_term(min_importance=0.0)
            self.lt_table.setRowCount(0)
            for item in lt_items:
                row = self.lt_table.rowCount()
                self.lt_table.insertRow(row)
                self.lt_table.setItem(row, 0, QTableWidgetItem(str(item.get("key", ""))))
                self.lt_table.setItem(row, 1, QTableWidgetItem(str(item.get("value", ""))))
                self.lt_table.setItem(row, 2, QTableWidgetItem(str(item.get("importance", ""))))
        except Exception as e:
            QMessageBox.warning(self, "Memory", f"Failed to load long-term memory: {e}")

    def _on_mem_add_update(self):
        key = self.mem_key.text().strip()
        val = self.mem_value.text().strip()
        if not key or not val:
            QMessageBox.information(self, "Memory", "Enter key and value.")
            return
        if self.session.memory.recall_long_term(key) is None:
            self.session.memory.remember_long_term(key, val, importance=0.5)
        else:
            self.session.memory.update_long_term(key, val)
        self._refresh_memory_tables()

    def _on_mem_forget(self):
        key = self.mem_forget_key.text().strip()
        if not key:
            return
        self.session.memory.forget_long_term(key)
        self._refresh_memory_tables()

    def _init_logs_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        layout.addWidget(self.log_view)

        row = QHBoxLayout()
        self.log_refresh_btn = QPushButton("Refresh")
        self.log_refresh_btn.clicked.connect(self._refresh_logs)
        row.addWidget(self.log_refresh_btn)
        layout.addLayout(row)

        self.tabs.addTab(page, "Logs")
        self._refresh_logs()

    def _refresh_logs(self):
        try:
            fp = Path("jai_assistant.log")
            if fp.exists():
                data = fp.read_text(encoding="utf-8", errors="ignore")
                if len(data) > 20000:
                    data = data[-20000:]
                self.log_view.setPlainText(data)
                sb = self.log_view.verticalScrollBar()
                sb.setValue(sb.maximum())
        except Exception:
            pass

    def _switch_to_tab(self, name: str) -> bool:
        target = name.strip().lower()
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i).strip().lower() == target:
                self.tabs.setCurrentIndex(i)
                return True
        return False

    def _on_language_changed(self):
        idx = self.lang_combo.currentIndex()
        code = self.lang_combo.itemData(idx)
        if code:
            self.stt_language = code
        if self.voice_worker and self.voice_worker.isRunning():
            try:
                self.voice_worker.language = self.stt_language
            except Exception:
                pass

    def _on_apply_voice_pref(self):
        pref = self.voice_pref_input.text().strip().lower()
        try:
            tts.TTS_PREFERRED_VOICE = pref or "david"
        except Exception:
            pass

    def _on_toggle_voice_control(self):
        if self.voice_worker and self.voice_worker.isRunning():
            try:
                self.voice_worker.stop()
            except Exception:
                pass
            self.voice_control_btn.setText("Start Voice Control")
            return
        self.voice_worker = VoiceControlWorker(language=self.stt_language)
        self.voice_worker.recognized.connect(self._on_voice_recognized)
        self.voice_worker.error.connect(self._on_voice_error)
        self.voice_worker.stopped.connect(lambda: self._append_chat("Voice", "Stopped"))
        self.voice_worker.start()
        self.voice_control_btn.setText("Stop Voice Control")

    def _on_voice_recognized(self, text: str):
        self._append_chat("Voice", text)
        s = text.strip().lower()
        tab_map = {
            "assistant": "Assistant",
            "calendar": "Calendar",
            "memory": "Memory",
            "logs": "Logs",
            "music": "Music",
            "settings": "Settings",
        }
        for key, label in tab_map.items():
            if f"open {key} tab" in s or f"switch to {key}" in s or s == key:
                if self._switch_to_tab(label):
                    msg = f"Opening {label} tab"
                    self._append_chat("JAI", msg)
                    self._speak(msg)
                return
        media_res = handle_media_command(s)
        if media_res:
            self._append_chat("Media", media_res)
            self._speak(media_res)
            return
        self.input_line.setText(text)
        self._on_send_clicked()

    def _on_voice_error(self, err: str):
        if err and err.strip().lower() != "no speech recognized":
            self._append_chat("Voice", err)


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
