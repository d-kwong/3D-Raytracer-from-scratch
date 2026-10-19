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
def rotate_point(v,k,theta):
    return v*np.cos(theta) + np.cross(k,v)*np.sin(theta) + k * np.dot(k,v)*(1-np.cos(theta))

fig = plt.figure(figsize=(8, 8),facecolor='k')
ax = fig.add_subplot(111, projection='3d')
ax.set_box_aspect((1,1,1))
ax.set_xlim([-3,3])
ax.set_ylim([-3,3])
ax.set_zlim([-3,3])



n = 15
domain = [-1,1]
x,y = np.meshgrid(np.linspace(domain[0],domain[1],n+1),np.linspace(domain[0],domain[1],n+1))
z = np.cos(x*np.pi/2)*np.cos(y*np.pi/2)
points = np.stack([x,y,z],axis=-1)
faces = []
normals = []
brightness = []
light_pos = np.array([4,4,1])
for i in range(n):
    for j in range(n):
        face = [points[i,j],points[i,j+1],points[i+1,j]]
        normal = compute_normal(face)
        brightness.append(max(np.dot(normal,normalize(light_pos-points[i,j])),0))
        face = [points[i,j+1],points[i+1,j+1],points[i+1,j]]
        normal = compute_normal(face)
        #brightness.append(max(np.dot(normal,normalize(light_pos-points[i,j])),0))

facecolors = np.ones((n+1,n+1,4))
facecolors[:n,:n,:3] = np.array(brightness).reshape((n,n,1))

ax.plot_surface(x,y,z,facecolors=facecolors,shade=False)

n = 15
domain = [-1.5,1.5]
y,z = np.meshgrid(np.linspace(domain[0],domain[1],n+1),np.linspace(domain[0],domain[1],n+1))
x = np.zeros_like(y)
pixels = np.stack([x,y,z],axis = -1)
pixels = pixels.reshape((pixels.size//3,3))
pixels += np.array([2,0,0])
yaxis = np.array([0,-1,0])
zaxis = np.array([0,0,1])
elev = 30
azim = 45
pixels = np.apply_along_axis(lambda v: rotate_point(v,yaxis,np.deg2rad(elev)),-1,pixels)
pixels = np.apply_along_axis(lambda v: rotate_point(v,zaxis,np.deg2rad(azim)),-1,pixels)
x = pixels[:,0]
y = pixels[:,1]
z = pixels[:,2]
ax.scatter(x,y,z)

plt.show()