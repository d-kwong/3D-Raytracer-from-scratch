import numpy as np
import matplotlib.pyplot as plt

def rotate_point(v,k,theta):
    return v*np.cos(theta) + np.cross(k,v)*np.sin(theta) + k * np.dot(k,v)*(1-np.cos(theta))

fig = plt.figure(figsize=(8, 8),facecolor='k')
ax = fig.add_subplot(111, projection='3d')
ax.set_box_aspect((1,1,1))

ax.scatter(0,0,0)
ax.set_xlim((-1,1))
ax.set_ylim((-1,1))
ax.set_zlim((-1,1))
n_theta_steps = 10
n_phi_steps = 8
points = np.zeros((n_theta_steps*n_phi_steps,3))
theta_values = np.linspace(-2,0.8,n_theta_steps)
z_values = np.linspace(0,1,n_theta_steps)
phi_values = np.linspace(0,6.282,n_phi_steps)
theta_r = 0.8

for theta_step in range(n_theta_steps):
    for phi_step in range(n_phi_steps):
        i = theta_step*n_phi_steps+phi_step
        theta = theta_values[theta_step]
        phi = phi_values[phi_step]
        phi_r = np.exp(-(2.1*(z_values[theta_step]-0.5))**8) * 0.2
        points[i,0] = np.cos(phi) * phi_r
        points[i,1] = np.sin(phi) * phi_r
        points[i,2] = 0
        points[i,:] = rotate_point(points[i,:],np.array([0,1,0]),-theta)
        points[i,0] += np.cos(theta) * theta_r
        points[i,2] += np.sin(theta) * theta_r


x = points[:,0].reshape((n_theta_steps,n_phi_steps))
y = points[:,1].reshape((n_theta_steps,n_phi_steps))
z = points[:,2].reshape((n_theta_steps,n_phi_steps))
ax.plot_surface(x,y,z)

plt.show()