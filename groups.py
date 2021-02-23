from decouple import config
import logging
from data import get_ddb_items_with_keys

TABLE_NAME = config("TABLE_NAME")
group_role_map = {}

logger = logging.getLogger(__name__)

def get_groups_and_roles():
  """
  Gets group and role mapping from database
  """
  logger.info("Getting group/role map")
  groups = get_ddb_items_with_keys(TABLE_NAME, domain="group")
  group_role_map.clear()
  for group in groups:
    group_role_map.update({
      group["sub_id"]: group["roles"]
    })