import logging
# import sys

# logger = logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# # Create handlers
c_handler = logging.StreamHandler()
f_handler = logging.FileHandler('tools/file.log', encoding='Utf-8')
c_handler.setLevel(logging.INFO)
f_handler.setLevel(logging.DEBUG)

# # Create formatters and add it to handlers
c_format = logging.Formatter('%(levelname)s - %(message)s')
f_format = logging.Formatter("%(asctime)s -- %(name)s -- %(levelname)s -- %(funcName)s:%(lineno)d -- %(message)s")

c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)

# # Add handlers to the logger
logger.addHandler(c_handler)
logger.addHandler(f_handler)
logger.info(f"New session")
# logger.log(level=logging.INFO, msg='Log info')
# logger.error('Log error')
# except:
# logger.error("uncaught exception: %s", traceback.format_exc())