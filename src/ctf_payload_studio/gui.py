"""Analiz, dönüşüm ve karşılaştırma için yerel PyQt5 arayüzü."""

from __future__ import annotations

import sys
from collections.abc import Callable

from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ctf_payload_studio.analyzer import analyze_text
from ctf_payload_studio.compare import compare_texts
from ctf_payload_studio.errors import StudioError
from ctf_payload_studio.models import Context, TransformName
from ctf_payload_studio.pipeline import run_pipeline
from ctf_payload_studio.reporting import analysis_text, comparison_text, pipeline_text


class StudioWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("CTF Payload Studio 4.0 — Çevrimdışı Savunma Laboratuvarı")
        self.resize(980, 720)
        tabs = QTabWidget()
        tabs.addTab(self._analysis_tab(), "Analiz")
        tabs.addTab(self._pipeline_tab(), "Dönüşüm Zinciri")
        tabs.addTab(self._compare_tab(), "Karşılaştırma")
        self.setCentralWidget(tabs)
        self.statusBar().showMessage("Ağ, subprocess ve payload üretimi devre dışıdır.")

    def _context_box(self) -> QComboBox:
        box = QComboBox()
        box.addItems([item.value for item in Context])
        return box

    def _analysis_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        controls = QHBoxLayout()
        self.analysis_context = self._context_box()
        button = QPushButton("Statik analiz et")
        button.clicked.connect(self._analyze)
        controls.addWidget(QLabel("Bağlam:"))
        controls.addWidget(self.analysis_context)
        controls.addWidget(button)
        self.analysis_input = QPlainTextEdit()
        self.analysis_input.setPlaceholderText(
            "İncelenecek metni buraya yapıştırın (en fazla 64 KiB)."
        )
        self.analysis_output = QPlainTextEdit()
        self.analysis_output.setReadOnly(True)
        layout.addLayout(controls)
        layout.addWidget(QLabel("Girdi"))
        layout.addWidget(self.analysis_input)
        layout.addWidget(QLabel("Açıklanabilir rapor"))
        layout.addWidget(self.analysis_output)
        return widget

    def _pipeline_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        controls = QHBoxLayout()
        self.transform_box = QComboBox()
        self.transform_box.addItems([item.value for item in TransformName])
        add_button = QPushButton("Adım ekle")
        add_button.clicked.connect(self._add_step)
        remove_button = QPushButton("Seçili adımı kaldır")
        remove_button.clicked.connect(self._remove_step)
        run_button = QPushButton("Zinciri çalıştır")
        run_button.clicked.connect(self._run_pipeline)
        controls.addWidget(self.transform_box)
        controls.addWidget(add_button)
        controls.addWidget(remove_button)
        controls.addWidget(run_button)
        self.pipeline_steps = QListWidget()
        self.pipeline_input = QPlainTextEdit()
        self.pipeline_output = QPlainTextEdit()
        self.pipeline_output.setReadOnly(True)
        layout.addLayout(controls)
        layout.addWidget(self.pipeline_steps)
        layout.addWidget(QLabel("Girdi"))
        layout.addWidget(self.pipeline_input)
        layout.addWidget(QLabel("Çıktı ve provenance grafiği"))
        layout.addWidget(self.pipeline_output)
        return widget

    def _compare_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        controls = QHBoxLayout()
        self.compare_context = self._context_box()
        button = QPushButton("Karşılaştır")
        button.clicked.connect(self._compare)
        controls.addWidget(QLabel("Bağlam:"))
        controls.addWidget(self.compare_context)
        controls.addWidget(button)
        inputs = QHBoxLayout()
        self.compare_left = QPlainTextEdit()
        self.compare_right = QPlainTextEdit()
        inputs.addWidget(self.compare_left)
        inputs.addWidget(self.compare_right)
        self.compare_output = QPlainTextEdit()
        self.compare_output.setReadOnly(True)
        layout.addLayout(controls)
        layout.addLayout(inputs)
        layout.addWidget(self.compare_output)
        return widget

    def _guard(self, callback: Callable[[], None]) -> None:
        try:
            callback()
        except StudioError as exc:
            QMessageBox.warning(self, "Girdi hatası", str(exc))

    def _analyze(self) -> None:
        def action() -> None:
            report = analyze_text(
                self.analysis_input.toPlainText(), Context(self.analysis_context.currentText())
            )
            self.analysis_output.setPlainText(analysis_text(report))

        self._guard(action)

    def _add_step(self) -> None:
        if self.pipeline_steps.count() < 12:
            self.pipeline_steps.addItem(self.transform_box.currentText())

    def _remove_step(self) -> None:
        row = self.pipeline_steps.currentRow()
        if row >= 0:
            self.pipeline_steps.takeItem(row)

    def _run_pipeline(self) -> None:
        def action() -> None:
            names = [
                TransformName(self.pipeline_steps.item(index).text())
                for index in range(self.pipeline_steps.count())
            ]
            result = run_pipeline(self.pipeline_input.toPlainText(), names)
            self.pipeline_output.setPlainText(pipeline_text(result))

        self._guard(action)

    def _compare(self) -> None:
        def action() -> None:
            report = compare_texts(
                self.compare_left.toPlainText(),
                self.compare_right.toPlainText(),
                Context(self.compare_context.currentText()),
            )
            self.compare_output.setPlainText(comparison_text(report))

        self._guard(action)


def run_gui() -> int:
    application = QApplication.instance() or QApplication(sys.argv)
    application.setApplicationName("CTF Payload Studio")
    window = StudioWindow()
    window.show()
    return application.exec_()
