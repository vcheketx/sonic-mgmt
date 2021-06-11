'''
Conftest file for span tests
'''

import pytest
#from span_helpers import 

@pytest.fixture(scope="module")
def cfg_facts(duthosts, rand_one_dut_hostname):
    '''
    Used to get config facts for selected DUT

    Args:
        duthosts: All DUTs belonging to the testbed.
        rand_one_dut_hostname: hostname of a random chosen dut to run test.
    '''
    duthost = duthosts[rand_one_dut_hostname]
    return duthost.config_facts(host=duthost.hostname, source="persistent")['ansible_facts']

@pytest.fixture(scope="module")
def ports_for_test(cfg_facts):
    '''
    Used to select 3 ports for test and generate info on them

    Args:
        duthosts: All DUTs belonging to the testbed.
        rand_one_dut_hostname: hostname of a random chosen dut to run test.
        cfg_facts: pytest fixture

    Return:
        dict: port info for 3 selected ports
    '''
    # Select vlan for test
    vlans = cfg_facts['VLAN']
    vlan = [vlans[vlan]['vlanid'] for vlan in vlans.keys()][0]

    # Select 3 ports for test
    ports = cfg_facts['VLAN_MEMBER']['Vlan{}'.format(vlan)]
    lags = cfg_facts['PORTCHANNEL'].keys()
    monitor = ports.pop[0]


    # Return dict with names of ports, available for mirror session, 
    # list of other ports and LAGs, and monitor port
    return {
        'lags': lags,
        'ports': ports,
        'monitor': monitor,
        'vlan': vlan
    }

@pytest.fixture(scope='module', autouse=True)
def setup_monitor_port(duthosts, rand_one_dut_hostname, ports_for_test, cfg_facts):
    '''
    Used to prepare monitor port for test

    Args:
        duthosts: All DUTs belonging to the testbed.
        rand_one_dut_hostname: hostname of a random chosen dut to run test.
        ports_for_test: pytest fixture containing info on selected ports
    '''
    duthost = duthosts[rand_one_dut_hostname]

    port = ports_for_test['monitor']
    vlan = ports_for_test['vlan']
    tagging_mode = cfg_facts['VLAN_MEMBER']['Vlan{}'.format(vlan)][port]['tagging_mode']
        

    # Remove monitor port from vlan members
    duthost.command('config vlan member del {} {}'.format(vlan, port))

    yield

    # Add monitor port to vlan members
    duthost.command('config vlan member add {} {} --{}'.format(vlan, port, tagging_mode))

@pytest.mark.parametrize('direction', ['rx', 'tx', 'both'])
@pytest.mark.parametrize('sources', ['port'])
#@pytest.mark.parametrize('sources', ['port', 'lag', 'port,port', 'port,lag', 'lag,lag'])
@pytest.fixture
def session_info(request, ports_for_test, sources):
    '''
    Used to generate mirroring session info based on selected ports

    Args:
        request: pytest request object.
        ports_for_test: pytest fixture containing info on selected ports

    Return:
        dict: mirroring session configuration params and port indices
    '''
    src = []
    ports = ports_for_test['ports'][:]
    lags = ports_for_test['lags'][:]

    for source_type in sources.split(','):
        if 'port' in source_type:
            src.append(ports.pop(0))
        elif 'lag' in source_type:
            src.append(lags.pop(0))
    dst = ports_for_test['monitor']

    return {
        'name':'session_1',
        'monitor': dst,
        'source_ports': src,
        'direction': direction,
    }

@pytest.fixture
def setup_session(duthosts, rand_one_dut_hostname, session_info):
    '''
    Used to add/remove mirroring session on DUT

    Args:
        duthosts: All DUTs belonging to the testbed.
        rand_one_dut_hostname: hostname of a random chosen dut to run test.
        session_info: pytest fixture containing mirroring session info

    Return:
        dict: ptf port indices for session source ports and monitor port
    '''
    duthost = duthosts[rand_one_dut_hostname]
    src_ports = ",".join(session_info["source_ports"]).rstrip(',')
    # Add mirroring session
    duthost.command('config mirror_session span add {} {} {} {}'.format(
        session_info["name"],
        session_info["destination_port"],
        src_ports,
        session_info["direction"]
        )
                   )
    yield 

    # Remove mirroring session
    duthost.command('config mirror_session remove {}'.format(session_info["session_name"]))
