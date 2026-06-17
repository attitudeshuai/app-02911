def test_import_app_package():
    import app
    assert hasattr(app, "__version__")


def test_import_logger():
    from app.logger import logger
    assert logger is not None


def test_import_config():
    from app.config import Theme, Window, App, Font
    assert Theme.BG is not None
    assert Window.TITLE is not None
    assert App.DEFAULT_WORKSPACE is not None
    assert Font.SIZE > 0


def test_import_command_modules():
    from app.commands.base import CommandResult, OutputType
    from app.commands.command_router import CommandRouter
    from app.commands.dos_commands import DosCommands
    from app.commands.cargo_executor import CargoExecutor

    assert CommandResult is not None
    assert CommandRouter is not None
    assert DosCommands is not None
    assert CargoExecutor is not None
    assert len(OutputType) > 0


def test_command_router_instantiation():
    from app.commands.command_router import CommandRouter
    router = CommandRouter()
    assert router is not None
    assert hasattr(router, "execute")
    assert hasattr(router, "parse_input")


def test_command_result_basic():
    from app.commands.base import CommandResult, OutputType
    result = CommandResult()
    assert result.success is True
    assert result.lines == []
    assert result.clear_screen is False

    result.add_error("test error")
    assert result.success is False
    assert len(result.lines) == 1
    assert result.lines[0][1] == OutputType.ERROR

    result.add_success("test success")
    result.add_info("test info")
    result.add_warning("test warning")
    result.add_system("test system")
    assert len(result.lines) == 5
