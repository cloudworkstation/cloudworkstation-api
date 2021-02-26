from decouple import config
import logging
from data import get_ddb_item

TABLE_NAME = config("TABLE_NAME")

logger = logging.getLogger(__name__)

def get_machine_def(machine_def_id):
  """
  Get a single machine def based on ID
  """
  logger.info(f"Getting machine def for {machine_def_id}")
  machine_def = get_ddb_item(TABLE_NAME, domain="machine_def", sub_id=machine_def_id)
  if machine_def:
    return machine_def
  else:
    return None