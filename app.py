import json
import logging
from flask import Flask, request, redirect
from flask_cors import CORS

from ecs import create_desktop_instance, destroy_desktop_instance
from groups import get_groups_and_roles
from entitlements import get_entitlements_for_roles
from machinedef import get_machine_def
from instance import get_instances_by_username
from security import secured
from utils import success_json_response, check_for_keys, get_rand_string
from errors import error_handler, ResourceNotFoundException, BadRequestException

# setup app
app = Flask(__name__)
CORS(app)

# set logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] (%(threadName)-10s) %(message)s')
logger = logging.getLogger(__name__)

# pre-cache useful data
get_groups_and_roles()

@app.route("/", methods=["GET"])
@error_handler
@secured
def root(username, roles):
  return success_json_response({
    "status": "okay",
    "username": username,
    "roles": roles
  })

@app.route("/entitlement", methods=["GET"])
@error_handler
@secured
def get_entitlements(username, roles):
  return success_json_response(get_entitlements_for_roles(roles, username))

@app.route("/instance", methods=["GET"])
@error_handler
@secured
def get_instances(username, roles):
  instances = get_instances_by_username(username)
  return success_json_response(instances)

@app.route("/instance", methods=["POST"])
@error_handler
@secured
def create_instance(username, roles):
  # check if the request is JSON
  if request.json:
    missing = check_for_keys(
      dict = request.json,
      keys = ["action", "machine_def_id", "screen_geometry"]
    )
    if missing:
      raise BadRequestException(f"The following keys are missing from the request: {missing}")
    else:
      if request.json["action"] not in ["create"]:
        raise BadRequestException("Invalid action")
      if request.json["screen_geometry"] not in ["1920x1080", "1280x720"]:
        raise BadRequestException("Invalid screen geometry")
      # get entitlements
      entitlements = get_entitlements_for_roles(roles, username)
      selected_entitlement = None
      for entitlement in entitlements:
        if entitlement["machine_def_id"] == request.json["machine_def_id"]:
          selected_entitlement = entitlement
      if selected_entitlement:
        if selected_entitlement["total_allowed_instances"] - selected_entitlement["current_instances"] > 0:
          # we can provision it
          # get machine def
          machine_def = get_machine_def(machine_def_id=selected_entitlement["machine_def_id"])
          desktop_id = get_rand_string(8)
          # if an override id was set then use it
          if "desktop_id" in request.json:
            desktop_id = request.json["desktop_id"]
          # create task to provision
          response = create_desktop_instance(
            desktop_id=desktop_id,
            ami_id=machine_def["ami_id"],
            machine_username=username,
            screen_geometry=request.json["screen_geometry"],
            machine_def_id=selected_entitlement["machine_def_id"],
            instance_type=machine_def["instance_type"],
            user_data=machine_def["user_data"]
          )
          if response:
            return success_json_response({
              "desktop_id": desktop_id,
              "status": "okay",
              "message": "created task to create instance"
            })
          else:
            return success_json_response({
              "status": "error"
            })
        else:
          raise ResourceNotFoundException("No available capacity to start this instance")
      else:
        raise ResourceNotFoundException("No matching machine_def found")
  else:
    raise BadRequestException("Request should be JSON")

@app.route("/instance/<instanceid>", methods=["GET"])
@error_handler
@secured
def get_instance(username, roles, instanceid):
  instances = get_instances_by_username(username)
  if instanceid in instances:
    return success_json_response(instances[instanceid])
  else:
    raise ResourceNotFoundException(f"An instance with id '{instanceid}' was not found")

@app.route("/instance/<instanceid>", methods=["DELETE"])
@error_handler
@secured
def delete_instance(username, roles, instanceid):
  instances = get_instances_by_username(username)
  if instanceid in instances:
    # need to trigger delete
    instance = instances[instanceid]
    machine_def = get_machine_def(machine_def_id=instance["machine_def_id"])
    # create task to provision
    response = destroy_desktop_instance(
      desktop_id=instanceid,
      ami_id=machine_def["ami_id"],
      machine_username=username,
      screen_geometry=instance["screengeometry"],
      machine_def_id=instance["machine_def_id"],
      instance_type=machine_def["instance_type"],
      user_data=machine_def["user_data"]
    )
    if response:
      return success_json_response({
        "desktop_id": instanceid,
        "status": "okay",
        "message": "created task to remove instance"
      })
    else:
      return success_json_response({
        "status": "error"
      })
  else:
    raise ResourceNotFoundException(f"An instance with id '{instanceid}' was not found")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")