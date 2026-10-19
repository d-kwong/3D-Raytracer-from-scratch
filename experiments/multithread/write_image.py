from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import cv2
fig = plt.figure(figsize=(8, 8),facecolor='k')
file_path = Path(__file__).resolve().parent / "output.txt"
folder_path = str(Path(__file__).resolve().parents[1] / "images") + "/"
with open(file_path,"r") as file:
    p = file.readline()

p = p.split(" ")[:-1]
p = [float(x) for x in p]
h = int(np.sqrt(len(p)))#/2))
p = np.array(p).reshape((h,h))#2*h))
cv2.imwrite(folder_path+"output.png",p*255)
ax = fig.add_subplot()
ax.set_xticks([])
ax.set_yticks([])
ax.imshow(p,cmap=cm.gray)
plt.show()
