#Program do stworzenia maski, która będzie niwelowała fakt, że fragmenty obrazu bliższe środka mają większy wpływ na pomiar na fotorezystorze niż te najdalej od środka
#Program wyświetla po kolei każdy piksel obrazu i zapisuje te wartości do tablicy 2D (po zastosowaniu Nadaraya-Watosna na podstawie wartości z calibrate_grey.csv)
#Następnie znajduje z tych wartości najmniejszą ("smallest") i każdą wartość w tablicy ("x") podmienia na smallest/x
#Oznacza to, że piksel który podczas kalibracji był najciemniejszy będzie miał w masce wartość 1, a pozostałe pewną wartość z zakresu [0,1] w zależności od względnej jasności

from matplotlib import pyplot as plt
from time import sleep
import paho.mqtt.client as mqtt
import csv

#Zmienne i funkcje do Nadaraya-Watsona:
h = 50
X = []
X_est = []
Y = []

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

#Parametry wyświetlania obrazów:
size = 16       #Rozmiar kalibrowanego obrazu (musi być taki sam jak finalnie rekonstruowany obraz)
plt.ion()
M = [[0 for j in range(size)] for i in range(size)]
values = [[0 for j in range(size)] for i in range(size)]
fig = plt.figure(facecolor='black')
ax = plt.subplot(111)
im = ax.imshow(M, cmap='gray', vmin=0, vmax=1)
plt.axis('off')
n = 0
mng = plt.get_current_fig_manager()
#mng.full_screen_toggle()
smallest = 999999.0

#Kilkusekundowe opóźnienie, podczas którego wyświetlamy jedynie pierwszy piksel
for i in range(3):
    M = [[(i * size + j == 0) * 1 for j in range(size)] for i in range(size)]
    im.set_array(M)
    fig.canvas.flush_events()
    sleep(0.5)

#Funkcja wywoływana po otrzymaniu wiadomości z mikrokontrolera                                                           
def on_message(mosq, obj, msg):
    global n
    global smallest

    #Po zakończeniu kalibracji: przekonwertowanie tablicy i zapis do csv
    if n>=size*size: 
        with open('.\\csv\\calibrate_pixel.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',',
                                    quotechar=' ', quoting=csv.QUOTE_MINIMAL)
            smallest = NadarayWatson(smallest)
            for row in values:
                write_row = []
                for item in row:
                    write_row.append(smallest/item)
                writer.writerow(write_row)
        exit()
    
    #Wyświetlanie obrazu, wpisanie pomiarów do dobrego miejsca w tablicy i szukanie najmniejszej wartości
    M = [[(i * size + j == n) * 1 for j in range(size)] for i in range(size)]
    im.set_array(M)
    fig.canvas.flush_events()
    values[int(n/size)][n%size] = NadarayWatson(float(msg.payload))
    if float(msg.payload) < smallest:
        smallest = float(msg.payload)
    mqttc.publish(Topic_Ping,1)
    n += 1

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


#Wysłanie pinga do mikrokontrolera (rozpoczęcie kalibracji)
mqttc.publish(Topic_Ping,1)



while mqttc.loop() == 0:
    pass