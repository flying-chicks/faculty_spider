# encoding: utf-8


from base.settings import SLAVES, USER_NAME
from base.monitor.command_by_ssh import CommandBySSH

for slave in SLAVES:
    command_by_ssh = CommandBySSH(slave, USER_NAME)
    command = 'kill -9 `pgrep python`'
    command_by_ssh.exec_command(command)
    command_by_ssh.close()