import numpy as np
import matplotlib.pyplot as plt

def rotate_point(v,k,theta):
    return v*np.cos(theta) + np.cross(k,v)*np.sin(theta) + k * np.dot(k,v)*(1-np.cos(theta))
n = 15
domain = [-1,1]
y,z = np.meshgrid(np.linspace(domain[0],domain[1],n+1),np.linspace(domain[0],domain[1],n+1))
x = np.zeros_like(y)
points = np.stack([x,y,z],axis = -1)
points = points.reshape((points.size//3,3))

points += np.array([2,0,0])

yaxis = np.array([0,-1,0])
zaxis = np.array([0,0,1])
elev = 30
azim = 45
points = np.apply_along_axis(lambda v: rotate_point(v,yaxis,np.deg2rad(elev)),-1,points)
points = np.apply_along_axis(lambda v: rotate_point(v,zaxis,np.deg2rad(azim)),-1,points)

x = points[:,0]
y = points[:,1]
z = points[:,2]
fig = plt.figure(figsize=(8, 8),facecolor='k')
ax = fig.add_subplot(111, projection='3d')
ax.set_box_aspect((1,1,1))
ax.set_xlim([-3,3])
ax.set_ylim([-3,3])
ax.set_zlim([-3,3])
ax.scatter(x,y,z)
ax.scatter(0,0,0,c='r')
plt.show()