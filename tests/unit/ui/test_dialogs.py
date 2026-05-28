import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"


from app.ui.dialogs.dialog_framework import DialogConfig, DialogResult
from app.ui.dialogs.error_dialog import ErrorDialog
from app.ui.dialogs.notification_toast import ToastNotification, ToastType


class TestDialogConfig:
    def test_defaults(self):
        config = DialogConfig()
        assert config.title == ""
        assert config.message == ""
        assert config.buttons == ["OK"]
        assert config.modal is True

    def test_custom(self):
        config = DialogConfig(
            title="Test",
            message="Hello",
            buttons=["Yes", "No", "Cancel"],
            default_button="Yes",
            cancel_button="Cancel",
        )
        assert len(config.buttons) == 3
        assert config.default_button == "Yes"


class TestDialogResult:
    def test_enum_values(self):
        assert DialogResult.ACCEPTED.name == "ACCEPTED"
        assert DialogResult.REJECTED.name == "REJECTED"
        assert DialogResult.CLOSED.name == "CLOSED"


class TestToastType:
    def test_enum_values(self):
        assert ToastType.INFO.name == "INFO"
        assert ToastType.SUCCESS.name == "SUCCESS"
        assert ToastType.WARNING.name == "WARNING"
        assert ToastType.ERROR.name == "ERROR"

    def test_styles_defined(self):
        for t in ToastType:
            assert t in ToastNotification.STYLES
            style = ToastNotification.STYLES[t]
            assert "bg" in style
            assert "fg" in style
            assert "icon" in style


class TestErrorDialog:
    def test_static_show_methods(self):
        assert callable(ErrorDialog.show_error)
        assert callable(ErrorDialog.show_warning)
        assert callable(ErrorDialog.show_info)
