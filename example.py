from evillimiter_ng.lib import manager

myeng = manager.CoreLimiter()

myeng.add("192.168.101.73")
myeng.block(0)
input("Press enter to free the host...")
myeng.free("all")
print("Done!")
myeng.interrupt()
