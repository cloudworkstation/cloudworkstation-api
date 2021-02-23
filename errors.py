"""
Code to manage errors
"""
from functools import wraps
import logging
from utils import exception_to_json_response, generic_exception_json_response

logger = logging.getLogger(__name__)

class ResourceNotFoundException(Exception):
    """Error thrown for missing resources"""
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)

class BadRequestException(Exception):
    """Error thrown for Bad requests, requests which do not conform to the expectations of the application"""
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)

def error_handler(f):
    """
    Function to manage errors coming back to webservice calls
    """
    @wraps(f)
    def error_decorator(*args, **kwargs):
        """
        Function to manage errors coming back to webservice calls
        """
        try:
            return f(*args, **kwargs)
        except ResourceNotFoundException as err:
          return exception_to_json_response(err, 404)
        except BadRequestException as err:
            return exception_to_json_response(err, 400)
        #except Exception as err:
        #    logger.error(err, exc_info=True)
        #    return generic_exception_json_response(500)
    return error_decorator