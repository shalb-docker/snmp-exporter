# snmp-exporter
snmp exporter for prometheus monitoring

## build

~~~~
docker login
docker-compose -f docker-compose-build.yml build
docker-compose -f docker-compose-build.yml push
~~~~

## configuration

Add your snmp host name and user name to snmp-exporter/snmp/snmp_exporter.py.yml

## run

Use docker-compose.yml to run container with mounted config snmp-exporter/snmp/snmp_exporter.py.yml
~~~~
docker-compose up
~~~~

