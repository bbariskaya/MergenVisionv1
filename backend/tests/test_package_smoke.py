"""Smoke tests for the mergenvision package boundary."""

import mergenvision


def test_package_version_is_present():
    assert hasattr(mergenvision, "__version__")
    assert isinstance(mergenvision.__version__, str)
    assert mergenvision.__version__ == "0.1.0"


def test_package_submodules_are_importable():
    # These imports verify that the layer directories are valid Python packages.
    from mergenvision import api, application, config, domain, infrastructure, ports

    assert api is not None
    assert application is not None
    assert config is not None
    assert domain is not None
    assert infrastructure is not None
    assert ports is not None
