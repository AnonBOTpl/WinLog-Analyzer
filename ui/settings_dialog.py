import json
import keyring

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QComboBox, QLineEdit, QPushButton, QLabel,
    QMessageBox, QDialogButtonBox, QFrame,
)
from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal

from core.ai_client import validate_key, list_models
from core.paths import resource_path, data_file
from core.i18n import t, available_languages, load as i18n_load

SERVICE_NAME = "winlog-analyzer"
SETTINGS_PATH = data_file("config/settings.json")

KEYRING_KEYS = {
    "gemini": "gemini",
    "claude": "anthropic",
    "openai": "openai",
    "groq": "groq",
}

PROVIDER_LABELS = {
    "gemini": "Google Gemini",
    "claude": "Claude (Anthropic)",
    "openai": "OpenAI",
    "groq": "Groq",
}


def load_settings() -> dict:
    try:
        with open(SETTINGS_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"selected_provider": "gemini", "selected_model": "gemini-2.5-flash", "language": "en"}


def get_api_key(provider: str = "gemini") -> str:
    return keyring.get_password(SERVICE_NAME, KEYRING_KEYS.get(provider, provider)) or ""


class ScanModelsWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, provider: str, api_key: str):
        super().__init__()
        self.provider = provider
        self.api_key = api_key

    def run(self):
        try:
            models = self._scan()
            self.finished.emit(models)
        except Exception as e:
            self.error.emit(str(e))

    def _scan(self) -> list[str]:
        key = self.api_key
        if not key:
            raise ValueError(t("error_no_api_key_title"))
        return list_models(self.provider, key)


class TestKeyWorker(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, provider: str, api_key: str):
        super().__init__()
        self.provider = provider
        self.api_key = api_key

    def run(self):
        try:
            ok, msg = self._test()
            self.finished.emit(ok, msg)
        except Exception as e:
            self.finished.emit(False, str(e))

    def _test(self) -> tuple[bool, str]:
        key = self.api_key
        if not key:
            return False, t("error_no_api_key_title")
        ok = validate_key(self.provider, key)
        return ok, t("settings_key_valid") if ok else t("settings_key_invalid")


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._workers = []
        self._settings = load_settings()

        self.setWindowTitle(t("settings_title"))
        self.setMinimumWidth(550)
        self.setModal(True)

        self._setup_ui()
        self._load_current_values()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Provider selection
        prov_layout = QHBoxLayout()
        prov_layout.addWidget(QLabel(t("settings_provider_label")))
        self.cmb_provider = QComboBox()
        for key, label in PROVIDER_LABELS.items():
            self.cmb_provider.addItem(label, key)
        self.cmb_provider.currentIndexChanged.connect(self._on_provider_changed)
        prov_layout.addWidget(self.cmb_provider, 1)
        layout.addLayout(prov_layout)

        # API Key
        key_layout = QVBoxLayout()
        key_layout.addWidget(QLabel(t("settings_api_key_label")))

        key_row = QHBoxLayout()
        self.txt_api_key = QLineEdit()
        self.txt_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_api_key.setPlaceholderText(t("settings_api_key_placeholder", provider=t("app_title")))
        key_row.addWidget(self.txt_api_key, 1)

        self.btn_save_key = QPushButton(t("settings_save_key"))
        self.btn_save_key.clicked.connect(self._save_key)
        key_row.addWidget(self.btn_save_key)

        self.btn_test_key = QPushButton(t("settings_test_key"))
        self.btn_test_key.clicked.connect(self._test_key)
        key_row.addWidget(self.btn_test_key)

        self.btn_delete_key = QPushButton(t("settings_delete_key"))
        self.btn_delete_key.setStyleSheet("color: #E74C3C;")
        self.btn_delete_key.clicked.connect(self._delete_key)
        key_row.addWidget(self.btn_delete_key)

        key_layout.addLayout(key_row)
        layout.addLayout(key_layout)

        self.lbl_key_status = QLabel("")
        layout.addWidget(self.lbl_key_status)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #2C3E50;")
        layout.addWidget(sep)

        # Model scanning
        scan_layout = QHBoxLayout()
        scan_layout.addWidget(QLabel(t("settings_model_label")))
        self.cmb_model = QComboBox()
        self.cmb_model.setMinimumWidth(200)
        self.cmb_model.addItem(t("settings_model_placeholder"))
        scan_layout.addWidget(self.cmb_model, 1)

        self.btn_scan = QPushButton(t("settings_scan_models"))
        self.btn_scan.clicked.connect(self._scan_models)
        scan_layout.addWidget(self.btn_scan)

        layout.addLayout(scan_layout)

        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("color: #2C3E50;")
        layout.addWidget(sep2)

        # Language selection
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel(t("settings_language_label")))
        self.cmb_language = QComboBox()
        for lang in available_languages():
            self.cmb_language.addItem(lang["name"], lang["code"])
        self.cmb_language.setCurrentIndex(-1)
        lang_layout.addWidget(self.cmb_language, 1)
        layout.addLayout(lang_layout)

        self.lbl_lang_restart = QLabel(t("settings_language_restart"))
        self.lbl_lang_restart.setStyleSheet("color: #5D6D7E; font-size: 8pt;")
        layout.addWidget(self.lbl_lang_restart)

        # Separator
        sep3 = QFrame()
        sep3.setFrameShape(QFrame.Shape.HLine)
        sep3.setStyleSheet("color: #2C3E50;")
        layout.addWidget(sep3)

        # Buttons
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.button(QDialogButtonBox.StandardButton.Ok).setText(t("dialog_ok"))
        btn_box.button(QDialogButtonBox.StandardButton.Cancel).setText(t("dialog_cancel"))
        btn_box.accepted.connect(self._save_settings)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _save_settings_to_file(self):
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(self._settings, f, indent=2)

    def _load_current_values(self):
        provider = self._settings.get("selected_provider", "gemini")
        idx = self.cmb_provider.findData(provider)
        if idx >= 0:
            self.cmb_provider.setCurrentIndex(idx)

        model = self._settings.get("selected_model", "")
        self._load_saved_key()
        self._load_saved_model(model)

        lang = self._settings.get("language", "en")
        li = self.cmb_language.findData(lang)
        if li >= 0:
            self.cmb_language.setCurrentIndex(li)

    def _load_saved_key(self):
        provider = self.cmb_provider.currentData()
        keyring_key = KEYRING_KEYS.get(provider, provider)
        saved = keyring.get_password(SERVICE_NAME, keyring_key) or ""
        self.txt_api_key.setText(saved)

    def _load_saved_model(self, model: str):
        self.cmb_model.clear()
        if model:
            self.cmb_model.addItem(model)
            self.cmb_model.setCurrentIndex(0)
        else:
            self.cmb_model.addItem("Kliknij Skanuj aby pobrać modele")

    def _on_provider_changed(self):
        provider = self.cmb_provider.currentData()
        label = PROVIDER_LABELS.get(provider, provider)
        self.txt_api_key.setPlaceholderText(t("settings_api_key_placeholder", provider=label))
        self.lbl_key_status.setText("")
        self._load_saved_key()
        self.cmb_model.clear()
        self.cmb_model.addItem(t("settings_model_placeholder"))

    def _save_key(self):
        provider = self.cmb_provider.currentData()
        keyring_key = KEYRING_KEYS.get(provider, provider)
        key = self.txt_api_key.text().strip()

        if not key:
            QMessageBox.warning(self, t("warning_title"), t("settings_key_empty_warning"))
            return

        keyring.set_password(SERVICE_NAME, keyring_key, key)
        self.lbl_key_status.setStyleSheet("color: #27AE60;")
        self.lbl_key_status.setText(t("settings_key_saved"))

    def _delete_key(self):
        provider = self.cmb_provider.currentData()
        keyring_key = KEYRING_KEYS.get(provider, provider)
        try:
            keyring.delete_password(SERVICE_NAME, keyring_key)
        except keyring.errors.PasswordDeleteError:
            pass
        self.txt_api_key.clear()
        self.lbl_key_status.setStyleSheet("color: #E74C3C;")
        self.lbl_key_status.setText(t("settings_delete_key"))

    def _test_key(self):
        if self._worker is not None:
            return

        provider = self.cmb_provider.currentData()
        key = self.txt_api_key.text().strip()

        if not key:
            QMessageBox.warning(self, t("warning_title"), t("settings_key_test_warning"))
            return

        self.btn_test_key.setEnabled(False)
        self.lbl_key_status.setStyleSheet("color: #F39C12;")
        self.lbl_key_status.setText(t("settings_testing"))

        self._worker = TestKeyWorker(provider, key)
        self._worker.finished.connect(self._on_test_finished)
        self._worker.start()
        self._test_timer = QTimer.singleShot(15000, self._on_test_timeout)

    def _on_test_finished(self, ok: bool, msg: str):
        self.btn_test_key.setEnabled(True)
        display = t("settings_key_valid") if ok else t("settings_key_invalid")
        color = "#27AE60" if ok else "#E74C3C"
        self.lbl_key_status.setStyleSheet(f"color: {color};")
        self.lbl_key_status.setText(f"{'✅' if ok else '❌'} {display}")
        self._worker = None

    def _on_test_timeout(self):
        if self._worker is not None:
            self._worker.terminate()
            self._worker = None
            self.btn_test_key.setEnabled(True)
            self.lbl_key_status.setStyleSheet("color: #E74C3C;")
            self.lbl_key_status.setText(t("error_timeout", timeout=15))

    def _scan_models(self):
        if self._worker is not None:
            return

        provider = self.cmb_provider.currentData()
        key = self.txt_api_key.text().strip()

        if not key:
            QMessageBox.warning(self, t("warning_title"), t("settings_scan_warning"))
            return

        self.btn_scan.setEnabled(False)
        self.btn_scan.setText(t("settings_scanning"))
        self.cmb_model.clear()
        self.cmb_model.addItem(t("settings_scanning"))

        self._worker = ScanModelsWorker(provider, key)
        self._worker.finished.connect(self._on_scan_finished)
        self._worker.error.connect(self._on_scan_error)
        self._worker.start()
        self._scan_timer = QTimer.singleShot(30000, self._on_scan_timeout)

    def _on_scan_finished(self, models: list[str]):
        self.btn_scan.setEnabled(True)
        self.btn_scan.setText(t("settings_scan_models"))
        self.cmb_model.clear()

        if not models:
            self.cmb_model.addItem(t("settings_no_models"))
            self._worker = None
            return

        self.cmb_model.addItems(models)
        saved_model = self._settings.get("selected_model", "")
        if saved_model in models:
            self.cmb_model.setCurrentText(saved_model)
        self._worker = None

    def _on_scan_error(self, msg: str):
        self.btn_scan.setEnabled(True)
        self.btn_scan.setText(t("settings_scan_models"))
        self.cmb_model.clear()
        self.cmb_model.addItem(t("settings_scan_error", msg=msg))
        self._worker = None

    def _on_scan_timeout(self):
        if self._worker is not None:
            self._worker.terminate()
            self._worker = None
            self.btn_scan.setEnabled(True)
            self.btn_scan.setText(t("settings_scan_models"))
            self.cmb_model.clear()
            self.cmb_model.addItem(t("settings_scan_error", msg=t("error_timeout", timeout=30)))

    def _save_settings(self):
        provider = self.cmb_provider.currentData()
        model = self.cmb_model.currentText()
        lang = self.cmb_language.currentData()

        sentinels = [t("settings_model_placeholder"), t("settings_no_models"), t("settings_scanning")]
        if model in sentinels:
            model = ""

        old_lang = self._settings.get("language", "en")
        self._settings["selected_provider"] = provider
        self._settings["selected_model"] = model or self._settings.get("selected_model", "")
        if lang:
            self._settings["language"] = lang
        self._save_settings_to_file()
        self.accept()

        if lang and lang != old_lang:
            QMessageBox.information(
                self, t("settings_title"),
                t("settings_language_restart"),
            )
