import numpy as np
import matplotlib.pyplot as plt
def normalize(v):
    return v/np.linalg.norm(v)
def compute_normal(face):
    return normalize(np.cross(face[1]-face[0],face[2]-face[0]))
def compute_intercept(face,N,P,D):
    ND = np.dot(N,D)
    if ND == 0:
        return None, 0
    t = np.dot(N,face[0]-P)/ND
    return P + t*D, t
def check_inside(face,N,I):
    v1 = face[0]
    v2 = face[1]
    v3 = face[2]
    part_1 = np.dot(N,(np.cross(v2-v1,I-v1)))
    part_2 = np.dot(N,(np.cross(v3-v2,I-v2)))
    part_3 = np.dot(N,(np.cross(v1-v3,I-v3)))
    return (part_1>0 and part_2>0 and part_3>0) or (part_1<0 and part_2<0 and part_3<0)

p1 = np.array([1,1,0])
p2 = np.array([1,-1,1])
p3 = np.array([-1,1,0])
points = np.array([p1,p2,p3,p1])
face = np.array([p1,p2,p3])
center = np.sum(face,axis=0)/3

N = compute_normal(face)

P = np.array([2,2,2])
D = normalize(np.array([-1.2,-1,-1]))

I,t = compute_intercept(face,N,P,D)

print(check_inside(face,N,I))

fig = plt.figure(figsize=(8, 8),facecolor='k')
ax = fig.add_subplot(111, projection='3d')
ax.set_box_aspect((1,1,1))
ax.set_xlim([-2,2])
ax.set_ylim([-2,2])
ax.set_zlim([-2,2])

ax.plot(points[:,0],points[:,1],points[:,2])
ax.scatter(center[0],center[1],center[2])
ax.quiver(center[0],center[1],center[2],N[0],N[1],N[2])

ax.scatter(P[0],P[1],P[2])
ax.quiver(P[0],P[1],P[2],D[0]*t,D[1]*t,D[2]*t)

ax.scatter(I[0],I[1],I[2])
plt.show()