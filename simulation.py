#program symulujący działanie algorytmu - pomiar fotorezystorem zastąpiony jest obliczeniem średniej jasności wyświetlanego obrazu
#Służy do sprawdzenia poprawności algorytmu i łatwiejszej wizualizacji działania programu

from matplotlib import pyplot as plt
from time import sleep
import paho.mqtt.client as mqtt
import numpy as np
from scipy.linalg import hadamard
from skimage.transform import resize
from PIL import Image

#Rozmiar finalnego obrazu
size = 8 

#Wczytanie i przeskalowanie obrazu
base_image = np.asarray(Image.open("./objects/ghost.png").convert('L'))
resized_image = resize(base_image,(size,size))
values = []

#Wyświetlenie wstępnych obrazów
plt.ioff()
plt.figure()
plt.imshow(base_image,cmap='gray', vmin=0, vmax=1)
plt.title('Base image')
plt.show()

plt.figure()
plt.imshow(resized_image,cmap='gray', vmin=0, vmax=1)
plt.title('Resized image')
plt.show()

#Maski hadamardowe
hadamard_matrix = (hadamard(size**2)+1)/2

#Parametry wyświetlania obrazów
plt.ion()
image_show = np.multiply(hadamard_matrix[0].reshape(size,size),resized_image)
fig = plt.figure(facecolor='black')
ax = plt.subplot(111)
im = ax.imshow(image_show, cmap='gray', vmin=0, vmax=1)
plt.axis('off')
n = 0
mng = plt.get_current_fig_manager()
mng.full_screen_toggle()

#Wyświetlanie kolejnych obrazów, obliczanie średniej jasności obrazu, zapisanie tej wartości
for n in range(size*size):
    image_show = np.multiply(hadamard_matrix[n].reshape(size,size),resized_image)
    im.set_array(image_show)
    fig.canvas.flush_events()
    values.append(sum([sum(i) for i in image_show])/(size*size))
    sleep(0.1)

#Przemnożenie wartości przez liczbę pikseli (by się układ równań zgadzał)
scaled_values = [i*size*size for i in values]
scaled_values_t = np.array(scaled_values).T.tolist()

#Rekontrukcja obrazu poprzez obliczanie układu równań
recovered_image = np.multiply(hadamard_matrix,scaled_values_t)
recovered_image = np.abs(np.linalg.solve(hadamard_matrix,scaled_values))
recovered_image = recovered_image.reshape(size,size)

#Wyświetlenie finalnego obrazu
plt.ioff()
plt.figure()
plt.imshow(recovered_image,cmap='gray', vmin=0, vmax=1)
plt.title('Recovered image')
plt.show()



