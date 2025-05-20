import logging
import json
import traceback
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('asm_debug')

def log_request(request, label="Request"):
    """Log request details for debugging"""
    try:
        logger.debug(f"--- {label} ---")
        logger.debug(f"Method: {request.method}")
        logger.debug(f"Path: {request.path}")
        logger.debug(f"GET Params: {request.GET}")
        
        # Log headers selectively (excluding sensitive ones)
        safe_headers = {k: v for k, v in request.headers.items() 
                       if k.lower() not in ('cookie', 'authorization')}
        logger.debug(f"Headers: {safe_headers}")
        
        # Log user if authenticated
        if hasattr(request, 'user') and request.user.is_authenticated:
            logger.debug(f"User: {request.user.username}")
        
        logger.debug("-------------------")
    except Exception as e:
        logger.error(f"Error logging request: {e}")

def log_data(data, label="Data"):
    """Log data (trying to pretty print JSON if possible)"""
    try:
        if isinstance(data, (dict, list)):
            logger.debug(f"--- {label} ---")
            # Attempt to serialize with custom encoder
            class DateTimeEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, datetime):
                        return obj.isoformat()
                    return super().default(obj)
            
            try:
                json_str = json.dumps(data, indent=2, cls=DateTimeEncoder)
                logger.debug(json_str)
            except TypeError:
                # If JSON serialization fails, fall back to str()
                logger.debug(f"Could not serialize as JSON: {str(data)}")
        else:
            logger.debug(f"--- {label} ---")
            logger.debug(str(data))
        logger.debug("-------------------")
    except Exception as e:
        logger.error(f"Error logging data: {e}")

def log_exception(e, label="Exception"):
    """Log exception with traceback"""
    try:
        logger.error(f"--- {label} ---")
        logger.error(f"Exception: {type(e).__name__}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        logger.error("-------------------")
    except Exception as error:
        logger.error(f"Error logging exception: {error}")