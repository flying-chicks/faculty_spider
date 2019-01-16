# encoding: utf-8
from .command_by_ssh import CommandBySSH


class IntrinsicStatus(CommandBySSH):
    def __init__(self, host, user):
        CommandBySSH.__int__(self, host, user)

    def get_cpu_cores(self):
        return int(self.exec_command('grep "model name" /proc/cpuinfo | wc -l'))

    def get_uptime(self):
        return self.exec_command('uptime -p').decode('utf-8')

    def get_loadavg(self):
        return self.exec_command("cat /proc/loadavg | awk '{print $1, $2, $3}'").decode('utf-8')

    def get_memory_info(self):
        stdout = self.exec_command("cat /proc/meminfo | grep -E 'MemTotal|MemFree|Buffers|Cached' | gawk '{print $2}'")
        total, free, buffers, cached, temp = list(map(lambda x: float(x), stdout.split()))
        return round(total / 1024 ** 2, 2), round((free + buffers + cached + temp) / total * 100, 2)

    def is_alive(self):
        count = int(self.exec_command("pgrep python | wc -l").strip())
        return False if count is 0 else True

    def __call__(self):
        cpu_cores = self.get_cpu_cores()
        uptime = self.get_uptime()
        loadavg = self.get_loadavg()
        total_memory, memory_available_ratio = self.get_memory_info()
        is_alive = self.is_alive()
        self.close()
        return {'cpu_cores': cpu_cores, 'uptime': uptime, 'load_average': loadavg,
                'total_memory': total_memory, 'available_ratio': memory_available_ratio,
                'alive': is_alive
                }