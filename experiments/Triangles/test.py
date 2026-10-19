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

faces = []
normals = []
brightness = []
light_pos = np.array([4,4,1])
for i in range(n):
    for j in range(n):
        face = [points[i,j],points[i,j+1],points[i+1,j]]
        normal = compute_normal(face)
        brightness.append(max(np.dot(normal,normalize(light_pos-points[i,j])),0))

brightness = np.array(brightness).reshape(n,n,1)
facecolors = np.ones((n+1,n+1,4))
facecolors[:n,:n,:3] = brightness

fig = plt.figure(figsize=(8, 8),facecolor='k')
ax = fig.add_subplot(111, projection='3d')
ax.set_box_aspect((1,1,1))
ax.set_xlim(domain)
ax.set_ylim(domain)
ax.set_zlim([-1,1])
# ax.grid(False)
# ax.set_facecolor('k')
# ax.set_xticks([])
# ax.set_yticks([])
# ax.set_zticks([])
# for pane in (ax.xaxis.pane, ax.yaxis.pane, ax.zaxis.pane):
#     pane.set_visible(False)
# for line in (ax.xaxis.line, ax.yaxis.line, ax.zaxis.line):
#     line.set_linewidth(0)
# for attr in ('_draw_pane', '_draw_gridlines'):
#     setattr(ax.xaxis, attr, lambda *args, **kwargs: None)
#     setattr(ax.yaxis, attr, lambda *args, **kwargs: None)
#     setattr(ax.zaxis, attr, lambda *args, **kwargs: None)
# ax.scatter(light_pos[0],light_pos[1],light_pos[2])
ax.plot_surface(x,y,z,facecolors=facecolors,shade=False)
ax.view_init(elev=30,azim=45)
plt.show()