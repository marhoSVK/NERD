#!/usr/bin/env python3

import sys
from time import sleep
import logging

import core.config
#import core.db
import core.mongodb
import core.update_manager
import modules.base
# TODO load everything automatically (or everything specified in config)
#import modules.test_module
import modules.event_receiver
import modules.dns
import modules.geolocation
import core.eventdb

############

DEFAULT_CONFIG_FILE = "./nerd.cfg"

LOGFORMAT = "%(asctime)-15s,%(threadName)s,%(name)s: %(levelname)s %(message)s"
LOGDATEFORMAT = "%Y-%m-%dT%H:%M:%S"

############


if __name__ == "__main__":

    # Initialize logging mechanism
    
    logging.basicConfig(level=logging.DEBUG, format=LOGFORMAT, datefmt=LOGDATEFORMAT)
    logger = logging.getLogger()
    
    
    logger.info("NERDd start")
    
    # Load configuration
    # TODO parse arguments using ArgParse
    if len(sys.argv) >= 2:
        cfg_file = sys.argv[1]
    else:
        cfg_file = DEFAULT_CONFIG_FILE
    config = core.config.read_config(cfg_file)
    
    # Create main NERDd components
    #db = core.db.EntityDatabase({})
    db = core.mongodb.MongoEntityDatabase(config)
    eventdb = core.eventdb.FileEventDatabase(config)
    update_manager = core.update_manager.UpdateManager(config, db)
    
    # Instantiate modules
    # TODO create all modules automatically (loop over all modules.* and find all objects derived from NERDModule)
    module_list = [
        modules.event_receiver.EventReceiver(config, update_manager, eventdb),
        #modules.test_module.TestModule(config, update_manager),
        modules.dns.DNSResolver(config, update_manager),
        modules.geolocation.Geolocation(config, update_manager),
    ]
    
    # Run update manager thread/process
    logger.info("Starting UpdateManager")
    update_manager.start()
    
    # Run modules that have their own threads/processes
    # (if they don't have, start() should do nothing)
    for module in module_list:
        module.start()
    
    ####
    
    #sleep(1)
    
    # Simulate some update requests
#     update_manager.update(('ip', '195.113.228.57'), [('set','X',123)])
#     update_manager.update(('ip', '195.113.144.230'), [('event','!sleep',1)])
#     update_manager.update(('ip', '147.229.9.23'), [('set','B',1),('set','X',321)])
#     sleep(2)
#     update_manager.update(('ip', '195.113.228.57'), [('set','B',8),('set','X',5555)])
    
    print("-------------------------------------------------------------------")
    print("Reading events from "+str(config.get('warden_filer_path'))+"/incoming")
    print()
    print("*** Enter anything to quit ***")
    try:
        input()
    except KeyboardInterrupt:
        pass
    
    logger.info("Stopping running components ...")
    for module in module_list:
        module.stop()
    update_manager.stop()
    
    
    # Print records from DB
    logger.info("Finished.")
#     print(db.get('ip', '195.113.228.57'))
#     print(db.get('ip', '195.113.144.230'))
#     print(db.get('ip', '147.229.9.23'))

#     print(eventdb.get('ip','109.201.152.239'))
#     print(eventdb.get('ip','109.92.248.130'))
#     print(eventdb.get('ip','1.2.3.44'))

    
#     while len(threads) > 0:
#         try:
#             # Join all threads using a timeout so it doesn't block
#             # Filter out threads which have been joined or are None
#             threads = filter(lambda (m,t): t.isAlive(), threads)
#             for m,t in threads:
#                 t.join(1)
#         except KeyboardInterrupt:
#             if second_interrupt:
#                 print("Second interrupt caught, stopping immediately")
#                 break
#             # Tell to all live threads to stop
#             print("KeyboardInterrupt, stopping running modules ...")
#             for m,t in threads:
#                 if t.isAlive() and hasattr(m, 'stop'):
#                     m.stop()
#             second_interrupt = True
#     
    logger.info("Main thread exitting")
    logging.shutdown()




