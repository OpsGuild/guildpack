"""Test that both oguild.response and oguild.responses imports work correctly."""

import pytest


class TestResponseImportAliases:
    """Test import aliases for singular/plural forms."""

    def test_response_import_works(self):
        """Test that original oguild.response import still works."""
        from oguild.response import (AuthenticationErrorHandler,
                                     CommonErrorHandler, DatabaseErrorHandler,
                                     Error, FileErrorHandler,
                                     NetworkErrorHandler, Ok,
                                     ValidationErrorHandler, police)

        assert Ok is not None
        assert Error is not None
        assert police is not None
        assert CommonErrorHandler is not None

    def test_responses_import_works(self):
        """Test that new oguild.responses import works."""
        from oguild.responses import (AuthenticationErrorHandler,
                                      CommonErrorHandler, DatabaseErrorHandler,
                                      Error, FileErrorHandler,
                                      NetworkErrorHandler, Ok,
                                      ValidationErrorHandler, police)

        assert Ok is not None
        assert Error is not None
        assert police is not None
        assert CommonErrorHandler is not None

    def test_imports_are_identical(self):
        """Test that oguild.response and oguild.responses provide identical objects."""
        from oguild.response import CommonErrorHandler as ResponseCommonHandler
        from oguild.response import Error as ResponseError
        from oguild.response import Ok as ResponseOk
        from oguild.response import police as response_police
        from oguild.responses import \
            CommonErrorHandler as ResponsesCommonHandler
        from oguild.responses import Error as ResponsesError
        from oguild.responses import Ok as ResponsesOk
        from oguild.responses import police as responses_police

        # They should be the same classes/functions
        assert ResponseOk is ResponsesOk, "Ok classes should be identical"
        assert (
            ResponseError is ResponsesError
        ), "Error classes should be identical"
        assert (
            response_police is responses_police
        ), "police functions should be identical"
        assert (
            ResponseCommonHandler is ResponsesCommonHandler
        ), "CommonErrorHandler classes should be identical"

    def test_module_direct_import(self):
        """Test direct module imports work."""
        import oguild.response as response_module
        import oguild.responses as responses_module

        assert hasattr(response_module, "Ok"), "oguild.response should have Ok"
        assert hasattr(
            responses_module, "Ok"
        ), "oguild.responses should have Ok"
        assert hasattr(
            response_module, "Error"
        ), "oguild.response should have Error"
        assert hasattr(
            responses_module, "Error"
        ), "oguild.responses should have Error"
        assert hasattr(
            response_module, "police"
        ), "oguild.response should have police"
        assert hasattr(
            responses_module, "police"
        ), "oguild.responses should have police"

    def test_response_functionality(self):
        """Test that response classes work through both import paths."""
        from oguild.response import Error as ResponseError
        from oguild.response import Ok as ResponseOk
        from oguild.responses import Error as ResponsesError
        from oguild.responses import Ok as ResponsesOk

        # Test Ok functionality
        response_ok = ResponseOk(200, "Success")
        responses_ok = ResponsesOk(200, "Success")

        # They should work identically
        assert response_ok is not None
        assert responses_ok is not None

        # Test Error functionality (without raising)
        try:
            response_error = ResponseError(
                "Test error", _raise_immediately=False
            )
            responses_error = ResponsesError(
                "Test error", _raise_immediately=False
            )

            assert response_error is not None
            assert responses_error is not None
            assert hasattr(response_error, "to_dict")
            assert hasattr(responses_error, "to_dict")
        except Exception:
            pytest.fail(
                "Error creation should not raise when _raise_immediately=False"
            )

    def test_police_decorator_functionality(self):
        """Test that police decorator works through both import paths."""
        from oguild.response import police as response_police
        from oguild.responses import police as responses_police

        assert response_police is responses_police

        @response_police
        def test_func():
            return "success"

        result = test_func()
        assert result == "success"
