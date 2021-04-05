from gevent import monkey
monkey.patch_all()

import logging
from decouple import config
from gunicorn.app.base import Application, Config
from app import app
from messageprocessor import get_processor
from sqs import SqsHandler

from gevent import Greenlet

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] (%(threadName)-10s) %(message)s")
logger = logging.getLogger(__name__)

class GUnicornFlaskApplication(Application):
  def __init__(self, app):
    self.usage, self.callable, self.prog, self.app = None, None, None, app
    
  def run(self, **options):
    self.cfg = Config()
    [self.cfg.set(key, value) for key, value in options.items()]
    return Application.run(self)

  load = lambda self:self.app

def starting(worker):
  logger.info("post_worker_init called")
  global sqs_handler, sqs_queue_url, message_processor, mpg
  sqs_handler = SqsHandler(
    topic_name=config("EC2_SNS_TOPIC"),
    kms_id=config("KMS_KEY_ID")
  )
  sqs_queue_url = sqs_handler.create_queue_and_subscribe()
  message_processor = get_processor(
    queueurl=sqs_queue_url
  )
  mpg = Greenlet(message_processor.run)
  mpg.start()

def stopping(server, worker):
  logger.info("worker_exit called")
  global mpg, sqs_handler
  mpg.join()
  sqs_handler.unsubscribe_and_delete_queue()

if __name__ == "__main__":
  g_app = GUnicornFlaskApplication(app)
  g_app.run(
    worker_class="gevent",
    #workers=1,
    post_worker_init=starting,
    worker_exit=stopping
  )