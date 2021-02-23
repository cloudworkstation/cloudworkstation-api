from decouple import config
import logging
from data import get_ddb_items_with_keys, get_ddb_item
from instance import scan_for_instances_with_tags

TABLE_NAME = config("TABLE_NAME")

logger = logging.getLogger(__name__)

def get_entitlements_for_roles(roles, username):
  """
  Gets entitlements for a set of toles
  """
  logger.info("Getting entitlements for roles: {roles}".format(roles=roles))
  flattened_entitlements = []
  for role in roles:
    role_record = get_ddb_item(TABLE_NAME, domain="role", sub_id=role)
    if role_record:
      if "entitlements" in role_record:
        entitlements = role_record["entitlements"]
        for entitlement in entitlements:
          entitlement = get_ddb_item(TABLE_NAME, domain="entitlement", sub_id=entitlement)
          instances = scan_for_instances_with_tags([
            {
              "name": "MachineDef",
              "value": entitlement["machine_def"]
            },
            {
              "name": "MachineType",
              "value": "Desktop"
            },
            {
              "name": "Username",
              "value": username
            }
          ])
          flattened_entitlements.append({
            "machine_def_id": entitlement["machine_def"],
            "total_allowed_instances": entitlement["machine_count"],
            "current_instances": len(instances)
          })
  return flattened_entitlements