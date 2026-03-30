
import time
def measure_latency(fn,*a,**k):
    s=time.time()
    r=fn(*a,**k)
    return r,time.time()-s
