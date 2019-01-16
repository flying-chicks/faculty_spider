# encoding: utf-8
"""
remotely govern computers by SSH.
"""

import paramiko
from paramiko import AuthenticationException
from ..settings import PKEY_PATH


class CommandBySSH(object):
    def __int__(self, host, user):
        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        key = paramiko.RSAKey.from_private_key_file(PKEY_PATH)
        try:
            self._client.connect(host, username=user, pkey=key)
        except AuthenticationException:
            AuthenticationException('Please set SSH free-password login: {}'.format(host))

    def exec_command(self, command):
        stdin, stdout, stderr = self._client.exec_command(command)
        result = stdout.read().strip()
        return result

    def close(self):
        self._client.close()
