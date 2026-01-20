import asyncio
import time
import uuid
import sys

# Test oguild imports
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

# Test guildpack imports (alias)
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

async def test_oguild_features():
    og_logger.info("--- Testing oguild functionality ---")
    
    # 1. Logger
    og_logger.debug("OG Dynamic Logger Debug")
    custom_og = OGLogger(logger_name="OG_Explicit").get_logger()
    custom_og.info("OG Explicit Logger Info")
    
    # 2. Ok Response
    res_ok = OGOk(data={"key": "value"}, message="Success from oguild")
    og_logger.info(f"OG Ok Response: {res_ok}", format=True)
    
    # 3. Error Response & Police
    @og_police
    def og_protected_func(should_fail=False):
        if should_fail:
            # Error raises immediately by default
            OGError("Intentional oguild error", 400)
        return "Everything is fine"

    og_logger.info(f"OG Protected Func (Success): {og_protected_func()}")
    
    try:
        og_protected_func(should_fail=True)
    except Exception as e:
        og_logger.error(f"Caught OG Protected Error: {e}")
    
    # 4. Utils (Sanitize & Case)
    raw_data = {"user_id": 1, "password": "secret_password", "_id": uuid.uuid4()}
    # sanitize_fields is async
    sanitized = await og_sanitize(raw_data)
    og_logger.info(f"OG Sanitized Data: {sanitized}")
    
    camel_data = og_convert_keys({"first_name": "horduntech"}, OGCase.CAMEL)
    og_logger.info(f"OG Case Conversion: {camel_data}")

async def test_guildpack_features():
    if not HAS_GUILDPACK:
        og_logger.warning("guildpack package not found, skipping its tests")
        return

    gp_logger.info("--- Testing guildpack (alias) functionality ---")
    
    # 1. Logger
    gp_logger.info("GP Dynamic Logger Info")
    
    # 2. Ok Response
    res_ok = GPOk(201, "Created from guildpack", {"id": 100})
    gp_logger.info(f"GP Ok Response: {res_ok}", format=True)
    
    # 3. Error Response & Police
    @gp_police
    async def gp_protected_async():
        # Testing Error with status code
        raise GPError("Guildpack Async Error", 500)

    try:
        await gp_protected_async()
    except Exception as e:
        gp_logger.error(f"Caught GP Async Protected Error: {e}")

    # 4. Case Enum
    snake_key = "IsThisCamel?"
    # Just checking the enum exists and works
    gp_logger.info(f"GP Case Enum Member: {GPCase.SNAKE}")

async def main():
    og_logger.info("==========================================")
    og_logger.info("🏗️  STARTING COMPREHENSIVE MANUAL TEST")
    og_logger.info("==========================================")
    
    try:
        await test_oguild_features()
        await test_guildpack_features()
        
        # Test Middleware instantiation
        mw = OGErrorMiddleware(None)
        og_logger.info("OG ErrorMiddleware instantiated successfully")
        
    except Exception as e:
        og_logger.critical(f"Unexpected crash in test app: {e}")
        import traceback
        traceback.print_exc()

    og_logger.info("==========================================")
    og_logger.info("🏁 MANUAL TEST COMPLETED")
    og_logger.info("==========================================")
    
    # Wait a moment for logs to flush before exiting
    await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
