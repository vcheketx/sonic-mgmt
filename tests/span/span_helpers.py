'''
Helper functions for span tests
'''

import ptf.testutils as testutils

from random import randint

def verify_mirroring_flow(ptfadapter, mirror_session):
    '''
    Send packet from ptf and verify it on monitor port

    Args:
        ptfadapter: ptfadapter fixture
        src_port: ptf port index, from which packet will be sent
        monitor: ptf port index, where packet will be verified on
    '''

    sources = mirror_session['sources']
    direction = mirror_session['direction']
    monitor = mirror_session['monitor']
    
    for session_source_port in sources:
        if 'rx' in direction or 'both' in direction:
            sorce_port = session_source_port
            destination_port = get_random_opposite_port(session_source_port)
            send_and_check_mirrored(ptfadapter,
                                    sorce_port,
                                    destination_port,
                                    monitor)
        elif 'tx' in direction or 'both' in direction:
            sorce_port = get_random_opposite_port(session_source_port)
            destination_port = session_source_port 
            send_and_check_mirrored(ptfadapter,
                                    sorce_port,
                                    destination_port,
                                    monitor)
        

def get_random_opposite_port(ports_for_test, port):
    '''
    For upstream port, return a random downstream port.
    Return upstream port if passed downstream port

    Args:
        ports_for_test: fixture with dict of available upstream/downstream ports
        port: DUT port name, for which to find an opposite port
    '''
    for port_group in ports_for_test.keys():
        ports = ports_for_test[port_group]
        if port not in ports and port_group != 'monitor':
            return ports[randint(0, len(ports)-1)]

def generate_packet(ptfadapter, source_port, dst_port):
    src_mac = ptfadapter.dataplane.get_mac(0, source_port)
    dst_mac = ptfadapter.dataplane.get_mac(0, destination_port)

    pkt = testutils.simple_icmp_packet(eth_src=src_mac, eth_dst='ff:ff:ff:ff:ff:ff')
    #pkt = testutils.simple_icmp_packet(eth_src=src_mac, eth_dst=dst_mac)
    return pkt

def send_and_check_mirrored(ptfadapter, src, monitor):
    ptfadapter.dataplane.flush()
    testutils.send(ptfadapter, src_port, pkt)
    testutils.verify_packet(ptfadapter, pkt, mirror_session['monitor'])

