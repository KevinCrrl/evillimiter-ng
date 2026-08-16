from evillimiter_ng.lib import envnet, manager

interface = envnet.get_default_interface()
gateway_ip = envnet.get_default_gateway()

envnet.initialize(interface)

myeng = manager.CoreLimiter(interface,
                            gateway_ip,
                            envnet.get_mac_by_ip(interface, gateway_ip),
                            envnet.get_default_netmask())

myeng.scan()

hosts = myeng.get_hosts_by_ids("all")
if hosts is not None:
    for host in hosts:
        print(host.ip)
    hid = input("block host by id: ")
    myeng.block(hid)
    input("Press enter to free host...")
    myeng.free(hid)
myeng.interrupt_handler()
envnet.stop_eng()
