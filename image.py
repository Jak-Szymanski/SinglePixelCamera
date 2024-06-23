#Program do finalnej rekonstrukcji obrazu
#Musi być najpierw wykonana kalibracja (zapisana w calibrate_grey.csv i calibrate_pixel.csv)
#Możlwość wybierania rodzajów tworzenia masek i metod rekonstrukcji obrazów przez odkomentowanie odpowiednich fragmentów

from matplotlib import pyplot as plt
from time import sleep
import paho.mqtt.client as mqtt
import math
import numpy as np
from scipy.linalg import hadamard
from skimage.transform import resize
from PIL import Image
import csv
import random

#Zmienne i funkcje do Nadaraya-Watsona:
h = 50
X = []
X_est = []
Y = []
mask = []

#Rozmiar rekonstruowanego obrazu (taki sam musiał zostać użyty w calibrate_pixel.py)
size = 16

def K(yn,y):
    return int(abs(yn-y)<0.5*h)

def NadarayWatson(y):
    m = 0.0
    l = 0.0
    for xi,yi in zip(X,Y):
        m += xi*K(yi,y)
        l += K(yi,y)
    return m/l

#Wczytanie pomiarów na potrzeby Nadaraya-Watsona
with open('.\\csv\\calibrate_gray.csv', newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        X.append(float(row['avg_values']))
        Y.append(float(row['meas_values']))

#Wczytanie maski do wyrównania pikseli
with open('.\\csv\\calibrate_pixel.csv', newline='') as csvfile:
    reader = csv.reader(csvfile)
    for read_row in reader:
        row = []
        for item in read_row:
            row.append(float(item))
        mask.append(row)



#Wczytanie obrazu z pliku i dostosowanie rozmiaru
base_image = np.asarray(Image.open(".\\objects\\face.png").convert('L'))
resized_image = resize(base_image,(size,size))

#Trzy rodzaje masek:
""" masks = hadamard(size**2)"""                                #Hadamard 
masks = np.identity(size*size)                                  #"Piksel po pikselu"
""" ratio = 0.5
random_masks = np.random.rand(int(1.5*size*size),size*size)
masks = np.where(random_masks > ratio, 1, 0)"""                 #Losowe

#Zastosowanie maski do wyrównania pikseli
image_scaled = np.multiply(resized_image,mask)


#Wyświetlenie wstępnych obrazów
plt.figure()
plt.imshow(base_image,cmap='gray', vmin=0, vmax=1)
plt.title('Base image')
plt.show()

plt.figure()
plt.imshow(resized_image,cmap='gray', vmin=0, vmax=1)
plt.title('Resized image')
plt.show()

plt.figure()
plt.imshow(image_scaled,cmap='gray', vmin=0, vmax=1)
plt.title('Scaled image')
plt.show()




#Parametry wyświetlania obrazów:
plt.ion()
M = np.multiply(masks[0].reshape(size,size),np.multiply(mask,image_scaled))
fig = plt.figure(facecolor='black')
ax  = plt.subplot(111)
im  = ax.imshow(M,cmap='gray', vmin=0, vmax=1)
plt.axis('off')
n = 0
values = []
count = [[0 for i in range(size)]for j in range(size)]
values_2d = [[0 for i in range(size)]for j in range(size)]
mng = plt.get_current_fig_manager()
#mng.full_screen_toggle()
sleep(1)

#Kilkusekundowe opóźnienie, podczas którego wyświetlamy pierwszy obraz
for i in range(5):
    M = np.multiply(masks[0].reshape(size,size),np.multiply(mask,image_scaled))
    im.set_array(M)
    fig.canvas.flush_events()
    sleep(0.5)


#Funkcja wywoływana po otrzymaniu wiadomości z mikrokontrolera     
def on_message(mosq, obj, msg):
    global n

    #Po zakończeniu eksperymentu: rekonstrukcja obrazu i wyświetlenie
    if n>=(size*size): 

        #Wariant 1. - rozwiązywanie układu równań:
        """ values_scaled = [n*(size*size) for n in values]     #Przemnożenie wartości przez liczbę pikseli (by się układ równań zgadzał)
        recovered_image = np.linalg.solve(masks,values_scaled)    #Rozwiązanie układu równań
        recovered_image = recovered_image.reshape(size,size)                #Złożenie obrazu w odpowiedni rozmiar """

        #Wariant 2. - średnia z pomiarów:
        recovered_image = [[values_2d[i][j] / count[i][j] for j in range(size)] for i in range(size)]       #Dla każdego piksela - suma pomiarów podzielona przez liczbę wyświetleń piksela

        #Postprocessing - zamienienie pierwszej i ostatniej kolumny:
        for i in range(size):
            first_element = recovered_image[i].pop(0)  # Remove the first element
            recovered_image[i].append(first_element)   
        
        #Postprocessing - rozciągnięcie histogramu:
        highest = float(np.max(recovered_image))
        lowest = float(np.min(recovered_image))
        scaled_recovered_image = [[(recovered_image[i][j] - lowest)/(highest-lowest) for j in range(size)] for i in range(size)]


        #Wyświetlenie obrazów
        plt.ioff()
        plt.figure()
        plt.imshow(recovered_image,cmap='gray', vmin=0, vmax=1)
        plt.axis('on')
        plt.title('Recovered image')
        plt.show()

        plt.ioff()
        plt.figure()
        plt.imshow(scaled_recovered_image,cmap='gray', vmin=0, vmax=1)
        plt.axis('on')
        plt.title('Scaled recovered image')
        plt.show()
        return
    
    #Fragment wywoływany w każdej iteracji:

    #Maska nakładana w danym kroku
    mask = masks[n].reshape(size,size)

    #Wyświetlanie obrazu i zapisanie pomiarów
    image_show = np.multiply(mask,resized_image)

    #Wariant 1. - rozwiązywanie układu równań:
    """ values.append(NadarayWatson(float(msg.payload)))  """

    #Wariant 2. - średnia z pomiarów:
    count = count + mask
    values_2d = values_2d + mask*NadarayWatson(float(msg.payload))

    #Wyświetlenie obrazu:
    im.set_array(image_show)
    fig.canvas.flush_events()
    n = n + 1
    sleep(0.5) 
    mqttc.publish(Topic_Ping,1)

#Połączenie poprzez MQTT
MQTT_Broker = '192.168.0.115'
MQTT_Port = 1883
Keep_Alive_Interval = 45
Topic_Ping = 'PING'
Topic_Data = 'DATA'
mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
mqttc.on_message = on_message
try:
    mqttc.connect(MQTT_Broker, int(MQTT_Port), int(Keep_Alive_Interval))
except:
    print("Blad w polaczeniu z brokerem")
    exit()
mqttc.subscribe(Topic_Data,0)


#Wysłanie pinga do mikrokontrolera (rozpoczęcie eksperymentu)
mqttc.publish(Topic_Ping,1)



while mqttc.loop() == 0:
    pass



