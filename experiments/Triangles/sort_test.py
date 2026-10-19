import numpy as np

x = np.array([[10, 0], [2.1173580255955384, 0], [1.5064673771823756, 0.0018998301418598558]])
print(np.sort(x,axis=0)[0])
print(sorted(x.tolist(),key = lambda x:x[0]))