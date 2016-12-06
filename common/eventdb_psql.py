"""
NERD event database wrapper.

Provides PSQLEventDatabase class -- an abstract layer above the database system 
implementing event database. The events are stored in PostgreSQL database.
"""
from __future__ import print_function

import json
import logging
import datetime

import dateutil.parser
import psycopg2
from psycopg2.extras import Json, Inet

class BadEntityType(ValueError):
    pass

class PSQLEventDatabase:
    """
    Event database storing IDEA record into PostgreSQL.
    """

    def __init__(self, config):
        """
        Initialize all internal structures as neccessary.
        """
        self.log = logging.getLogger('EventDB')
        #self.log.setLevel('DEBUG')
        
        # Create database connection
        self.db = psycopg2.connect(database=config.get('userdb.dbname', 'nerd'), # TODO eventdb instead of userdb
                                   user=config.get('userdb.dbuser', 'nerd'))

    def __del__(self):
        """
        Destructor. Close connection to database.
        """
        self.db.close()


    def get(self, etype, key, limit=None):
        """
        Return all events where given IP is among Sources.
        
        Arguments:
        etype   entity type (str), must be 'ip'
        key     entity identifier (str), e.g. '192.0.2.42'
        limit   max number of returned events
        
        Return a list of IDEA messages (strings).
        
        Raise BadEntityType if etype is not 'ip'.
        """
        if etype != 'ip':
            raise BadEntityType("etype must be 'ip'")
        
        cur = self.db.cursor()
        #cur.execute("SELECT idea FROM events WHERE %s = ANY(sources) ORDER BY detecttime DESC LIMIT %s", (key, limit))
        cur.execute("SELECT idea FROM events_sources INNER JOIN events ON events_sources.message_id = events.id WHERE source_ip = %s ORDER BY detecttime DESC LIMIT %s", (Inet(key), limit))
        self.db.commit() # Every query automatically opens a transaction, close it.
        
        result = cur.fetchall()
        result = [row[0] for row in result]
        
        print(result)
        return result


    def put(self, idea):
        """
        Store an IDEA message into the database.
        
        Arguments:
        idea    IDEA message as a string
        """
        # Decode IDEA
        idea = json.loads(idea)
        
        # Get ID
        try:
            id = idea.get('ID')
        except KeyError:
            self.log.error("ID field not found, skipping...")
            return
        
        # Get all source and target IPv4 addresses in the IDEA message
        sources = [ip for src in idea.get('Source', []) for ip in src.get('IP4', [])]
        targets = [ip for tgt in idea.get('Target', []) for ip in tgt.get('IP4', [])]
        
        # Parse timestamps
        try:
            detecttime = dateutil.parser.parse(idea.get('DetectTime'))
        except KeyError:
            self.log.error("Message ID {}: DetectTime not found, skipping...".format(idea.get('ID','N/A')))
            return
        except ValueError:
            self.log.error("Message ID {}: Unknown format of DetectTime, skipping ...".format(idea.get('ID','N/A')))
            return
        
        # If EventTime is not present, try WinStartTime instead (similiary for CeaseTime and WinEndTime)
        starttime = idea.get('EventTime', idea.get('WinStartTime', None))
        if starttime:
            starttime = dateutil.parser.parse(starttime)
        endtime = idea.get('CeaseTime', idea.get('WinEndTime', None))
        if endtime:
            endtime = dateutil.parser.parse(endtime)
        
        # Convert to UTC and remove timezone information
        detecttime = detecttime.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        if starttime:
            starttime = starttime.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        if endtime:
            endtime = endtime.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        
        self.log.debug("New event: %s, %s, %s, %s, %s, %s\n%s" % (id, sources, targets, detecttime, starttime, endtime, idea))
        #print("New event: %s, %s, %s, %s, %s, %s\n%s" % (id, sources, targets, detecttime, starttime, endtime, idea))
        
        # Store the record to database
        cur = self.db.cursor()
        try:
            cur.execute("""
                INSERT INTO events 
                (id, sources, targets, detecttime, starttime, endtime, idea)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                #(id, list(map(Inet,sources)), list(map(Inet,targets)), detecttime, starttime, endtime, Json(idea))
                (id, None, None, detecttime, starttime, endtime, Json(idea))
            )
            for source in sources:
                cur.execute(
                    "INSERT INTO events_sources (source_ip, message_id) VALUES (%s, %s)",
                    (Inet(source), id)
                )
            for target in targets:
                cur.execute(
                    "INSERT INTO events_targets (target_ip, message_id) VALUES (%s, %s)",
                    (Inet(target), id)
                )
            self.db.commit() # Close transaction (the first command opens it automatically)
        except Exception as e:
            self.log.error(str(e))
            self.db.rollback() # Rollback all non-commited changes