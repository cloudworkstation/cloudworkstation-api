"""
security.py

Contains code which manages access to API routes
"""
import logging
from functools import wraps
from flask import request, g

from errors import BadRequestException, AccessDeniedException
from groups import group_role_map

logger = logging.getLogger(__name__)

def admin_only(f):
  """
  Decorator which checks that the user has the 'admin' role
  """
  @wraps(f)
  def decorated_function(*args, **kwargs):
    """
    Function to check headers are present and check their validity
    """
    if "roles" in kwargs:
      if "admin" in kwargs["roles"]:
        return f(*args, **kwargs)
      else:
        logger.info("User does not have admin role")
        raise AccessDeniedException("Required role is not present")
    else:
      logger.info("Roles kwarg is missing")
      raise BadRequestException("Could not find role information")
  
  return decorated_function


def secured(f):
  """
  Decorator to check that a request has valid headers and matches the requirements
  """
  @wraps(f)
  def decorated_function(*args, **kwargs):
    """
    Function to check headers are present and check their validity
    """
    logger.info("Secured decorator has started")
    logger.debug("Details passed to the secured decorator", extra={"headers": request.headers})
    if "x-remote-user" in request.headers:
      username = request.headers["x-remote-user"]
      if "x-remote-user-groups" in request.headers:
        groups = request.headers["x-remote-user-groups"]
        logger.info(f"Groups from header: {groups}")
        groups = groups.split(",")
        # map groups to roles
        roles = []
        for group in groups:
          if group in group_role_map:
            roles.extend(group_role_map[group])
        logger.info("Raw roles list: {groups}".format(groups=roles))
        roles = list(set(roles))
        return f(username, roles, *args, **kwargs)
      else:
        logger.info("X-Remote-User-Groups header is missing from request")
        raise BadRequestException("X-Remote-User-Groups header is missing")
    else:
      logger.info("X-Remote-User header is missing")
      raise BadRequestException("X-Remote-User header is missing")
  
  return decorated_function