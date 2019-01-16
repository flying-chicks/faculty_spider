# encoding: utf-8

from base.settings import SLAVES, USER_NAME, PACKAGE_HOME
from base.monitor.command_by_ssh import CommandBySSH

for slave in SLAVES:
    command_by_ssh = CommandBySSH(slave, USER_NAME)
    command = ('export PYTHONPATH="PYTHONPATH:{0}" && '
               'nohup {0}/py32/bin/python {0}/bin/start.py &> /dev/null &').format(PACKAGE_HOME)
    command_by_ssh.exec_command(command)
    command_by_ssh.close()