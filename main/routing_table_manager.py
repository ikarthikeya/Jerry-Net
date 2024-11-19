import socket
import time
import threading

class RoutingTableManager:
    def __init__(self, server_addr, buffer_size, timeout, update_interval=15, inactive_timeout=30):
        self.server_addr = server_addr
        self.buffer_size = buffer_size
        self.timeout = timeout
        self.update_interval = update_interval
        self.inactive_timeout = inactive_timeout
        self.routing_table = {}
        self.lock = threading.Lock()

    def update_routing_table(self, self_node_num):
        """
        Periodically update the routing table by querying satellites.
        Satellites that respond are added to the routing table.
        """
        while True:
            try:
                inquire_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                inquire_socket.settimeout(self.timeout)

                # Send inquiry to server
                flag = 0
                pn, tp, cu = 0, 0, 0
                header = flag.to_bytes(4, 'big') + self_node_num.to_bytes(4, 'big') \
                         + pn.to_bytes(4, 'big') + tp.to_bytes(4, 'big')
                inquiry = header + cu.to_bytes(4, 'big')
                
                for id,ports in self.server_addr.items():
                    inquire_socket.sendto(inquiry, ('127.0.0.1',ports['receive']))

                    # Wait for satellite response
                    try:
                        ack, addr = inquire_socket.recvfrom(self.buffer_size)
                        node_id = f"Satellite-{int.from_bytes(ack[4:8], 'big')}"
                        sat_lat = int.from_bytes(ack[8:12], 'big', signed=True)
                        sat_lon = int.from_bytes(ack[12:16], 'big', signed=True)

                        # Add or update the satellite in the routing table
                        with self.lock:
                            self.routing_table[id] = {
                                "latitude": sat_lat,
                                "longitude": sat_lon,
                                "last_updated": time.time(),
                                "address": ports['receive']
                            }
                        print(f"Satellite {node_id} added/updated in the routing table.")

                    except socket.timeout:
                        print("Satellite inquiry timed out.")
            except Exception as e:
                print(f"Error updating routing table: {e}")
            finally:
                inquire_socket.close()
            print(self.routing_table)
            # Sleep for the update interval
            time.sleep(self.update_interval)

    def cleanup_routing_table(self):
        """
        Remove satellites that haven't been updated within the timeout period.
        """
        current_time = time.time()
        with self.lock:
            inactive_ids = [
                sat_id for sat_id, info in self.routing_table.items()
                if current_time - info["last_updated"] > self.inactive_timeout
            ]
            for sat_id in inactive_ids:
                del self.routing_table[sat_id]
                print(f"Satellite {sat_id} removed from the routing table (inactive).")

    def get_active_satellites(self):
        """
        Retrieve a list of active satellites from the routing table.
        """
        with self.lock:
            return [
                (info["latitude"], info["longitude"], sat_id)
                for sat_id, info in self.routing_table.items()
            ]
