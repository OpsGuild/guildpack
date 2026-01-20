import asyncio
import time
import uuid
import sys
import logging
import oguild

# Test imports
from oguild import (
    logger as og_logger, 
    Logger as OGLogger,
    Ok as OGOk, 
    Error as OGError, 
    police as og_police,
    sanitize_fields as og_sanitize,
    ErrorMiddleware as OGErrorMiddleware
)
from oguild.utils import Case as OGCase, convert_dict_keys as og_convert_keys

try:
    from guildpack import (
        logger as gp_logger,
        Logger as GPLogger,
        Ok as GPOk,
        Error as GPError,
        police as gp_police
    )
    from guildpack.utils import Case as GPCase
    HAS_GUILDPACK = True
except ImportError:
    HAS_GUILDPACK = False

async def test_log_inheritance():
    og_logger.info("--- Testing log level inheritance ---")
    og_logger.setLevel(logging.INFO)
    og_logger.info("Main logger set to INFO.")
    
    # 3. Test Error class inheritance
    og_logger.info("Triggering Error while level is INFO. Internal DEBUG logs should be suppressed.")
    try:
        raise OGError("Test Error suppression via level", code=500)
    except Exception:
        pass

async def test_log_toggles():
    og_logger.info("--- Testing explicit log toggles (Stack Trace & Attributes) ---")
    # Even if level is DEBUG, we should be able to suppress specific logs
    og_logger.setLevel(logging.DEBUG)
    og_logger.info("Level set to DEBUG.")

    og_logger.info("1. Triggering Error with BOTH toggles OFF. You should see NO 'Error attributes' or 'Stack trace' below.")
    try:
        raise OGError(
            "Silent Error", 
            include_stack_trace=False, 
            include_error_attributes=False
        )
    except Exception:
        pass

    og_logger.info("2. Triggering Error with ONLY Attributes ON.")
    try:
        raise OGError(
            "Attributes only", 
            include_stack_trace=False, 
            include_error_attributes=True
        )
    except Exception:
        pass

    og_logger.info("Resetting level to INFO.")
    og_logger.setLevel(logging.INFO)

async def test_middleware_toggles():
    og_logger.info("--- Testing Middleware log toggles ---")
    # Simulate middleware initialization with toggles OFF
    mw = OGErrorMiddleware(
        None, 
        include_stack_trace=False, 
        include_error_attributes=False
    )
    
    og_logger.info("Processing exception through Middleware (toggles OFF). Should be silent.")
    try:
        # Pass a raw exception
        mw.handle_exception(ValueError("Middleware test exception"))
    except Exception:
        pass

async def main():
    og_logger.info("==========================================")
    og_logger.info("🏗️  STARTING COMPREHENSIVE MANUAL TEST")
    og_logger.info("==========================================")
    
    try:
        await test_log_inheritance()
        await test_log_toggles()
        await test_middleware_toggles()
        
        # Original tests
        raw_data = {"user_id": 1, "password": "secret_password", "_id": uuid.uuid4()}
        sanitized = await og_sanitize(raw_data)
        og_logger.info(f"OG Sanitized Data: {sanitized}")
        
    except Exception as e:
        og_logger.critical(f"Unexpected crash in test app: {e}")
        import traceback
        traceback.print_exc()

    og_logger.info("==========================================")
    og_logger.info("🏁 MANUAL TEST COMPLETED")
    og_logger.info("==========================================")
    await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
