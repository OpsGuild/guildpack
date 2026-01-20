import pytest
import sys
import os

# Add both python/ and alias/ to sys.path to simulate they are installed
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, os.path.join(ROOT, "python"))
sys.path.insert(0, os.path.join(ROOT, "alias"))


def test_alias_top_level_exports():
    """Verify that guildpack re-exports main items."""
    import guildpack
    assert hasattr(guildpack, 'Logger')
    assert hasattr(guildpack, 'logger')
    assert hasattr(guildpack, 'Ok')
    assert hasattr(guildpack, 'Error')


def test_alias_submodule_logs():
    """Verify that guildpack.logs proxy works."""
    from guildpack.logs import Logger
    from oguild.logs import Logger as OLogger
    assert Logger is OLogger

    import guildpack.logs
    assert hasattr(guildpack.logs, 'Logger')


def test_alias_submodule_utils():
    """Verify that guildpack.utils proxy works."""
    from guildpack.utils import Case, to_snake, serialize_response
    from oguild.utils import Case as OCase
    assert Case is OCase
    assert hasattr(to_snake, '__call__')
    assert hasattr(serialize_response, '__call__')


def test_alias_submodule_response():
    """Verify that guildpack.response proxy works."""
    from guildpack.response import Ok
    from oguild.response import Ok as OOk
    assert Ok is OOk


def test_alias_submodule_middleware():
    """Verify that guildpack.middleware proxy works."""
    from guildpack.middleware import ErrorMiddleware
    from oguild.middleware import ErrorMiddleware as OErrorMiddleware
    assert ErrorMiddleware is OErrorMiddleware


def test_alias_plural_variants():
    """Verify that plural submodule variants work."""
    import guildpack.responses
    import guildpack.middlewares
    import guildpack.log

    assert hasattr(guildpack.responses, 'Ok')
    assert hasattr(guildpack.middlewares, 'ErrorMiddleware')
    assert hasattr(guildpack.log, 'Logger')


if __name__ == "__main__":
    pytest.main([__file__])
