from pathlib import Path
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
def check_intercept(face,P,D):
    N = compute_normal(face)

    I,t = compute_intercept(face,N,P,D)

    return check_inside(face,N,I), t

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
        faces.append(face)
        normal = compute_normal(face)
        brightness.append(max(np.dot(normal,normalize(light_pos-points[i,j])),0))
        face = [points[i,j+1],points[i+1,j+1],points[i+1,j]]
        faces.append(face)
        normal = compute_normal(face)
        brightness.append(max(np.dot(normal,normalize(light_pos-points[i,j])),0))
folder_path = str(Path(__file__).resolve().parent / "video_frames") + "/"
Path(folder_path).mkdir(exist_ok=True)
fig = plt.figure(figsize=(8, 8),facecolor='k')
for frame in range(24):
    print(f'processing frame {frame+1}/24')
    n = 40
    domain = [-1.2,1.2]
    y,z = np.meshgrid(np.linspace(domain[0],domain[1],n),np.linspace(domain[0],domain[1],n))
    x = np.zeros_like(y)
    pixels = np.stack([x,y,z],axis = -1)
    pixels = pixels.reshape((pixels.size//3,3))
    pixels += np.array([2,0,0])
    yaxis = np.array([0,-1,0])
    zaxis = np.array([0,0,1])
    elev = 30
    azim = frame*7.5
    pixels = np.apply_along_axis(lambda v: rotate_point(v,yaxis,np.deg2rad(elev)),-1,pixels)
    pixels = np.apply_along_axis(lambda v: rotate_point(v,zaxis,np.deg2rad(azim)),-1,pixels)

    D = -normalize(compute_normal([pixels[0],pixels[20],pixels[50]]))
    pixel_brightness = []
    for pixel_n,P in enumerate(pixels):
        #print(pixel_n)
        face_intercepts = [[10,0]]
        for i in range(len(faces)):
            hit,t = check_intercept(faces[i],P,D)
            if hit:
                face_intercepts.append([t,brightness[i]])
        pixel_brightness.append(sorted(face_intercepts,key=lambda x: x[0])[0][1])

    pixel_brightness = np.array(pixel_brightness).reshape((n,n))

    board = np.ones((n,n,4))
    board[:,:,:3] *= pixel_brightness.reshape((n,n,1))

    ax = fig.add_subplot()
    ax.grid(False)
    ax.set_facecolor('k')
    ax.set_xticks([])
    ax.set_yticks([])
    ax.imshow(board[::-1,:,:])
    plt.savefig(folder_path+f'frame{frame}.png')
    #plt.show()


