import html
import re
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QTextCursor

class OutputTextManager:
    def __init__(self, output_text, color_manager):
        self.output_text = output_text
        self.color_manager = color_manager
        self.text_buffer = ""
        self.last_line = ""
        self.color_pattern = re.compile(r'\[(\d+)m')
        self.setup_update_timer()

    def setup_update_timer(self):
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.flush_text_buffer)
        self.update_timer.start(100)

    def update_output_text(self, text):
        text = re.sub(r'\r(?!\n)', '\n', text)
        lines = text.split('\n')

        for line in lines:
            line = re.sub(r'(?<!\[)\s*\[(?!\d+m)|\](?!\s*\[)\s*', '', line)
            
            if self.last_line and line.startswith(self.last_line.rstrip()):
                self.text_buffer = self.text_buffer[:-len(self.last_line)] + line + '\n'
            else:
                self.text_buffer += line + '\n'

            self.last_line = line

        if len(self.text_buffer) > 4096:
            self.flush_text_buffer()

    def flush_text_buffer(self):
        if not self.text_buffer:
            return

        cursor = self.output_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        parts = re.split(r'(\[(?:\d+;)*\d+m)', self.text_buffer)

        html_text = ""
        current_color = self.color_manager.color_map["0"]

        for part in parts:
            if part.startswith('[') and part.endswith('m'):
                color_code = part[1:-1].split(';')[-1]
                current_color = self.color_manager.color_map.get(color_code, self.color_manager.color_map["0"])
            else:
                escaped_part = html.escape(part).replace('\n', '<br>')
                html_text += f'<span style="color:{current_color.name()};">{escaped_part}</span>'

        cursor.insertHtml(html_text)
        self.output_text.setTextCursor(cursor)
        self.output_text.ensureCursorVisible()
        self.text_buffer = ""

    def cleanup(self):
        self.update_timer.stop()