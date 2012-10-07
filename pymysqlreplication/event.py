import struct 
from datetime import datetime

from pymysql.util import byte2int, int2byte



class BinLogEvent(object):
    def __init__(self, from_packet, event_size, table_map):
        self.packet = from_packet
        self.table_map = table_map
        self.event_type = self.packet.event_type
        self.timestamp = self.packet.timestamp
        self.event_size = event_size

    def _read_table_id(self):
        # Table ID is 6 byte
        table_id = self.packet.read(6) + int2byte(0) + int2byte(0)   # pad little-endian number
        return struct.unpack('<Q', table_id)[0]

    def dump(self):
        print "=== %s ===" % (self.__class__.__name__)
        print "Date: %s" % (datetime.fromtimestamp(self.timestamp).isoformat())
        print "Event size: %d" % (self.event_size)
        print "Read bytes: %d" % (self.packet.read_bytes)
        self._dump()
        print
    
    def _dump(self):
        '''Core data dumped for the event'''
        pass


class RotateEvent(BinLogEvent):
    pass


class FormatDescriptionEvent(BinLogEvent):
    pass


class XidEvent(BinLogEvent):
    """
        A COMMIT event

        Attributes:
            xid: Transaction ID for 2PC
    """

    def __init__(self, from_packet, event_size, table_map):
        super(XidEvent, self).__init__(from_packet, event_size, table_map)
        self.xid = struct.unpack('<Q', self.packet.read(8))[0]

    def _dump(self):
        super(XidEvent, self)._dump()
        print "Transaction ID: %d" % (self.xid)


class QueryEvent(BinLogEvent):
    def __init__(self, from_packet, event_size, table_map):
        super(QueryEvent, self).__init__(from_packet, event_size, table_map)

        # Post-header
        self.slave_proxy_id = struct.unpack('<I', self.packet.read(4))[0]
        self.execution_time = struct.unpack('<I', self.packet.read(4))[0]
        self.schema_length =  byte2int(self.packet.read(1))
        self.error_code = struct.unpack('<H', self.packet.read(2))[0]
        self.status_vars_length = struct.unpack('<H', self.packet.read(2))[0]

        # Payload
        self.status_vars = self.packet.read(self.status_vars_length)
        self.schema =  self.packet.read(self.schema_length)
        self.packet.advance(1)

        self.query = self.packet.read(event_size - 13 - self.status_vars_length - self.schema_length - 1)
        #string[EOF]    query

    def _dump(self):
        super(QueryEvent, self)._dump()
        print "Schema: %s" % (self.schema)
        print "Execution time: %d" % (self.execution_time) 
        print "Query: %s" % (self.query)

