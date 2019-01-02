#!/usr/bin/env python

import subprocess
import traceback
import argparse
import sys
import time
import logging

import yaml
import prometheus_client

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument('--config', default=sys.argv[0] + '.yml', help='config file location')
parser.add_argument('--log_level', default='INFO', help='logging level')
args = parser.parse_args()

conf = dict()
for key in vars(args):
    conf[key] = vars(args)[key]

# configure logging
log = logging.getLogger(__name__)
log.setLevel(args.log_level)
FORMAT = '%(asctime)s %(levelname)s %(message)s'
logging.basicConfig(format=FORMAT)

# Create metrics
# collector metrics
REQUEST_TIME = prometheus_client.Summary('request_processing_seconds', 'Time spent processing request')
collector_errors = prometheus_client.Counter('collector_errors', 'Total number of errors')
# custom metrics
#snmp_interface_speed_bits = prometheus_client.Gauge('snmp_interface_speed', 'Interface speed', ['index'])
snmp_interface_in_bytes_total = prometheus_client.Gauge('snmp_interface_in_bytes_total', 'Interface trafic In bytes', ['net_dev_index', 'host'])
snmp_interface_out_bytes_total = prometheus_client.Gauge('snmp_interface_out_bytes_total', 'Interface trafic Out bytes', ['net_dev_index', 'host'])
snmp_interface_in_packets_total = prometheus_client.Gauge('snmp_interface_in_packets_total', 'Interface packets In', ['net_dev_index', 'host'])
snmp_interface_out_packets_total = prometheus_client.Gauge('snmp_interface_out_packets_total', 'Interface packets Out', ['net_dev_index', 'host'])
snmp_interface_in_errors_total = prometheus_client.Gauge('snmp_interface_in_errors_total', 'Interface errors In', ['net_dev_index', 'host'])
snmp_interface_out_errors_total = prometheus_client.Gauge('snmp_interface_out_errors_total', 'Interface errors Out', ['net_dev_index', 'host'])

def get_config():
    '''Parse configuration file'''
    with open(conf['config']) as conf_file:
        conf_yaml = yaml.load(conf_file)
    for key in conf_yaml:
        conf[key] = conf_yaml[key]

def snmp_query(metric):
    '''Run snmp query and write results to data'''
    stdout = dict()
    command_tmp = 'snmpwalk -v{0} -m ALL -u {1} {2} {3}'.format(conf['version'], conf['user'], conf['host'], metric)
    command = command_tmp.split()
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proc_stdout, proc_stderr = proc.communicate()
    proc_stdout = proc_stdout.decode(encoding='utf-8').split('\n')[:-1]
    proc_stderr = proc_stderr.decode(encoding='utf-8')
    for line in proc_stdout:
        log.debug(line)
    if proc.returncode != 0:
        collector_errors.inc()
        log.critical('Command: "{0}" failed with exit code: {1}, Errors: "{2}"'.format(command_tmp, proc.returncode, proc_stderr))
    for line in proc_stdout:
        key = line.split('=')[0].strip()
        val = line.split('=')[1].split(':')[1].strip()
        val_type = line.split('=')[1].split(':')[0].strip()
        stdout[key] = { 'val': val, 'val_type': val_type }
    return stdout

# Decorate function with metric.
@REQUEST_TIME.time()
def get_interfaces_stats():
    '''Get interfaces stats'''
    indexes = snmp_query('IF-MIB::ifIndex')
   #speed = snmp_query('IF-MIB::ifSpeed')
    in_bytes = snmp_query('IF-MIB::ifInOctets')
    out_bytes = snmp_query('IF-MIB::ifOutOctets')
    in_packets = snmp_query('IF-MIB::ifInUcastPkts')
    out_packets = snmp_query('IF-MIB::ifOutUcastPkts')
    in_errors = snmp_query('IF-MIB::ifInErrors')
    out_errors = snmp_query('IF-MIB::ifOutErrors')
    for key in indexes:
        index = indexes[key]['val']
       #speed_val = float(speed['IF-MIB::ifSpeed.' + index]['val'])
       #snmp_interface_speed_bits.labels(index=index).set(speed_val)
        in_bytes_val = float(in_bytes['IF-MIB::ifInOctets.' + index]['val'])
        snmp_interface_in_bytes_total.labels(net_dev_index=index, host=conf['host']).set(in_bytes_val)
        out_bytes_val = float(out_bytes['IF-MIB::ifOutOctets.' + index]['val'])
        snmp_interface_out_bytes_total.labels(net_dev_index=index, host=conf['host']).set(out_bytes_val)
        in_packets_val = float(in_packets['IF-MIB::ifInUcastPkts.' + index]['val'])
        snmp_interface_in_packets_total.labels(net_dev_index=index, host=conf['host']).set(in_packets_val)
        out_packets_val = float(out_packets['IF-MIB::ifOutUcastPkts.' + index]['val'])
        snmp_interface_out_packets_total.labels(net_dev_index=index, host=conf['host']).set(out_packets_val)
        in_errors_val = float(in_errors['IF-MIB::ifInErrors.' + index]['val'])
        snmp_interface_in_errors_total.labels(net_dev_index=index, host=conf['host']).set(in_errors_val)
        out_errors_val = float(out_errors['IF-MIB::ifOutErrors.' + index]['val'])
        snmp_interface_out_errors_total.labels(net_dev_index=index, host=conf['host']).set(out_errors_val)

if __name__ == '__main__':
    get_config()
    prometheus_client.start_http_server(conf['listen_port'])
    try:
        while True:
            get_interfaces_stats()
            time.sleep(conf['check_interval'])
    except:
        trace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
        for line in trace:
            print(line[:-1])
        collector_errors.inc()
        time.sleep(conf['check_interval'])


