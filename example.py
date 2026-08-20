from evillimiter_ng.lib import envnet, manager

interface: str = envnet.get_default_interface()

envnet.initialize(interface)

myeng = manager.CoreLimiter()

myeng.scan(intensity=1)

hosts = myeng.get_hosts_by_ids("all")
if hosts is not None:
    for host in hosts:
        print(host.ip)
    hid = input("block host by id: ")
    myeng.block(hid)
    input("Press enter to free host...")
    myeng.free(hid)
myeng.interrupt_handler()
envnet.stop_eng(interface)
