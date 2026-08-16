from evillimiter_ng.lib import envnet, manager

interface = envnet.get_default_interface()
gateway_ip = envnet.get_default_gateway()

envnet.initialize(interface)

myeng = manager.CoreLimiter(interface,
                            gateway_ip,
                            envnet.get_mac_by_ip(interface, gateway_ip),
                            envnet.get_default_netmask())

hosts = myeng.scan()
for host in hosts:
    print(host.ip)
myeng.interrupt_handler()
envnet.stop_eng()
