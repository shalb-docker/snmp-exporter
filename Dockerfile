FROM python:3.7.1

RUN apt update && \
apt install -y snmp

RUN pip3 install prometheus_client
RUN pip3 install pyaml

COPY snmp-exporter/snmp/ /opt/snmp/
RUN chmod 755 /opt/snmp/snmp_exporter.py

RUN useradd -m -s /bin/bash my_user
COPY snmp-exporter/mibs/ /home/my_user/.snmp/mibs/
RUN chown -R my_user:my_user /home/my_user/

USER my_user

ENTRYPOINT ["/usr/local/bin/python", "/opt/snmp/snmp_exporter.py"]
