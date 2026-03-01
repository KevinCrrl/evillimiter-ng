import threading

from evillimiter_ng.console import shell
from evillimiter_ng.common.globals import BIN_TC, BIN_IPTABLES
from evillimiter_ng.console.io import IO


class Limiter(object):
    class HostLimitIDs(object):
        def __init__(self, upload_id, download_id):
            self.upload_id = upload_id
            self.download_id = download_id

    def __init__(self, interface):
        self.interface = interface
        self._host_dict = {}
        self._host_dict_lock = threading.Lock()

    def limit(self, host, direction, rate):
        """
        Limits the uload/dload traffic of a host
        to a specified rate
        """
        host_ids = self._new_host_limit_ids(host, direction)

        if (direction & Direction.OUTGOING) == Direction.OUTGOING:
            # add a class to the root qdisc with specified rate
            shell.execute_suppressed(f'{BIN_TC} class add dev {self.interface} parent 1:0 classid 1:{host_ids.upload_id} htb rate {rate} burst {rate * 1.1}')
            # add a fw filter that filters packets marked with the corresponding ID
            shell.execute_suppressed(f'{BIN_TC} filter add dev {self.interface} parent 1:0 protocol ip prio {host_ids.upload_id} handle {host_ids.upload_id} fw flowid 1:{host_ids.upload_id}')
            # marks outgoing packets 
            shell.execute_suppressed(f'{BIN_IPTABLES} -t mangle -A POSTROUTING -s {host.ip} -j MARK --set-mark {host_ids.upload_id}')
        if (direction & Direction.INCOMING) == Direction.INCOMING:
            # add a class to the root qdisc with specified rate
            shell.execute_suppressed(f'{BIN_TC} class add dev {self.interface} parent 1:0 classid 1:{host_ids.download_id} htb rate {rate} burst {rate * 1.1}')
            # add a fw filter that filters packets marked with the corresponding ID
            shell.execute_suppressed(f'{BIN_TC} filter add dev {self.interface} parent 1:0 protocol ip prio {host_ids.download_id} handle {host_ids.download_id} fw flowid 1:{host_ids.download_id}')
            # marks incoming packets
            shell.execute_suppressed(f'{BIN_IPTABLES} -t mangle -A PREROUTING -d {host.ip} -j MARK --set-mark {host_ids.download_id}')

        host.limited = True

        with self._host_dict_lock:
            self._host_dict[host] = { 'ids': host_ids, 'rate': rate, 'direction': direction }

    def block(self, host, direction):
        host_ids = self._new_host_limit_ids(host, direction)

        if (direction & Direction.OUTGOING) == Direction.OUTGOING:
            # drops forwarded packets with matching source
            shell.execute_suppressed(f'{BIN_IPTABLES} -t filter -A FORWARD -s {host.ip} -j DROP')
        if (direction & Direction.INCOMING) == Direction.INCOMING:
            # drops forwarded packets with matching destination
            shell.execute_suppressed(f'{BIN_IPTABLES} -t filter -A FORWARD -d {host.ip} -j DROP')

        host.blocked = True

        with self._host_dict_lock:
            self._host_dict[host] = { 'ids': host_ids, 'rate': None, 'direction': direction }

    def unlimit(self, host, direction):
        if not host.limited and not host.blocked:
            return
            
        with self._host_dict_lock:
            host_ids = self._host_dict[host]['ids']

            if (direction & Direction.OUTGOING) == Direction.OUTGOING:
                self._delete_tc_class(host_ids.upload_id)
                self._delete_iptables_entries(host, direction, host_ids.upload_id)
            if (direction & Direction.INCOMING) == Direction.INCOMING:
                self._delete_tc_class(host_ids.download_id)
                self._delete_iptables_entries(host, direction, host_ids.download_id)

            del self._host_dict[host]

        host.limited = False
        host.blocked = False

    def replace(self, old_host, new_host):
        self._host_dict_lock.acquire()
        info = self._host_dict[old_host] if old_host in self._host_dict else None
        self._host_dict_lock.release()

        if info is not None:
            self.unlimit(old_host, Direction.BOTH)

            if info['rate'] is None:
                self.block(new_host, info['direction'])
            else:
                self.limit(new_host, info['direction'], info['rate'])

    def pretty_status(self, host):
        """
        Gets the host limitation status in a formatted and colored string
        """
        with self._host_dict_lock:
            if host in self._host_dict:
                rate = self._host_dict[host]['rate']
                direction = self._host_dict[host]['direction']
                uload = None
                dload = None
                final = ''

                if direction in (Direction.BOTH, Direction.OUTGOING):
                    uload = '0bit' if rate is None else rate
                if direction in (Direction.BOTH, Direction.INCOMING):
                    dload = '0bit' if rate is None else rate

                if uload is not None:
                    final += f'{uload}↑'
                if dload is not None:
                    final += f' {dload}↓'

                return f'{IO.LIGHTYELLOW}{final.strip()}{IO.END_LIGHTYELLOW}'

            return f'{IO.BOLD_LIGHTGREEN}Free{IO.END_BOLD_LIGHTGREEN}'

    def _new_host_limit_ids(self, host, direction):
        """
        Get limit information for corresponding host
        If not present, create new 
        """
        host_ids = None

        self._host_dict_lock.acquire()
        present = host in self._host_dict
        self._host_dict_lock.release()

        if present:
            host_ids = self._host_dict[host]['ids']
            self.unlimit(host, direction)
        
        return Limiter.HostLimitIDs(*self._create_ids()) if host_ids is None else host_ids

    def _create_ids(self):
        """
        Returns unique IDs that are
        currently not in use
        """
        def generate_id(*exc):
            """
            Generates a unique, unused ID
            exc: IDs that will not be used (exceptions)
            """
            id_ = 1
            with self._host_dict_lock:
                while True:
                    if id_ not in exc:
                        v = (x for x in self._host_dict.values())
                        ids = (x['ids'] for x in v)
                        if id_ not in (x for y in ids for x in [y.upload_id, y.download_id]):
                            return id_
                    id_ += 1

        id1 = generate_id()
        return (id1, generate_id(id1))

    def _delete_tc_class(self, id_):
        """
        Deletes the tc class and applied filters
        for a given ID (host)
        """
        shell.execute_suppressed(f'{BIN_TC} filter del dev {self.interface} parent 1:0 prio {id_}')
        shell.execute_suppressed(f'{BIN_TC} class del dev {self.interface} parent 1:0 classid 1:{id_}')

    def _delete_iptables_entries(self, host, direction, id_):
        """
        Deletes iptables rules for a given ID (host)
        """
        if (direction & Direction.OUTGOING) == Direction.OUTGOING:
            shell.execute_suppressed(f'{BIN_IPTABLES} -t mangle -D POSTROUTING -s {host.ip} -j MARK --set-mark {id_}')
            shell.execute_suppressed(f'{BIN_IPTABLES} -t filter -D FORWARD -s {host.ip} -j DROP')
        if (direction & Direction.INCOMING) == Direction.INCOMING:
            shell.execute_suppressed(f'{BIN_IPTABLES} -t mangle -D PREROUTING -d {host.ip} -j MARK --set-mark {id_}')
            shell.execute_suppressed(f'{BIN_IPTABLES} -t filter -D FORWARD -d {host.ip} -j DROP')


class Direction:
    NONE = 0
    OUTGOING = 1
    INCOMING = 2
    BOTH = 3

    def pretty_direction(direction):
        if direction == Direction.OUTGOING:
            return 'upload'
        if direction == Direction.INCOMING:
            return 'download'
        if direction == Direction.BOTH:
            return 'upload / download'    
        return '-'
