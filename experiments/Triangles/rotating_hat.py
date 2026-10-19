import numpy as np
import matplotlib.pyplot as plt
n = 15
domain = [-1,1]
x,y = np.meshgrid(np.linspace(domain[0],domain[1],n+1),np.linspace(domain[0],domain[1],n+1))
z = np.cos(x*np.pi/2)*np.cos(y*np.pi/2)
points = np.stack([x,y,z],axis=-1)

def normalize(v):
    return v/np.linalg.norm(v)

def compute_normal(face):
    return normalize(np.cross(face[1]-face[0],face[2]-face[0]))

def rotate_point(v,k,theta):
    return v*np.cos(theta) + np.cross(k,v)*np.sin(theta) + k * np.dot(k,v)*(1-np.cos(theta))

points = points.reshape((points.size//3,3))
points = np.apply_along_axis(lambda v:rotate_point(v,np.array([0,0,1]),np.pi/4),-1,points)
points = points.reshape((n+1,n+1,3))
x = points[:,:,0]
y = points[:,:,1]
z = points[:,:,2]
faces = []
normals = []
brightness = []
light_pos = np.array([4,4,1])
for i in range(n):
    for j in range(n):
        face = [points[i,j],points[i,j+1],points[i+1,j]]
        #face = [points[i,j+1],points[i+1,j+1],points[i+1,j]]
        normal = compute_normal(face)
        normals.append(normal)
        brightness.append(max(np.dot(normal,normalize(light_pos-points[i,j])),0))

brightness = np.array(brightness).reshape(n,n,1)
normals = np.array(normals).reshape(n,n,3)
facecolors = np.ones((n+1,n+1,4))
facecolors[:n,:n,:3] = brightness

fig = plt.figure(figsize=(8, 8),facecolor='k')
ax = fig.add_subplot(111, projection='3d')
ax.set_box_aspect((1,1,1))
ax.set_xlim([-1.5,1.5])
ax.set_ylim([-1.5,1.5])
ax.set_zlim([0,3])
# ax.scatter(light_pos[0],light_pos[1],light_pos[2])
ax.plot_surface(x,y,z,facecolors=facecolors,shade=False)
centers = (points[:n,:n,:]+points[1:,1:,:])/2
for i in range(n):
    for j in range(n):
        ax.quiver(centers[i,j,0],centers[i,j,1],centers[i,j,2],normals[i,j,0],normals[i,j,1],normals[i,j,2],color=[0,0.3,0,1])

plt.show()