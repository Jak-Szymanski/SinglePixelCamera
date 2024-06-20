#Program do kalibracji fotorezystora (zależność pomiędzy jasnością ekranu - wartościami na fotorezystorze)
#Zapisuje w pliku calibrate_gray.csv dwie kolumny: jasność ekranu (0-255) i wartość przesłana przez mikrokontroler
#Wyświetla na ekranie obrazy o jednolitym kolorze (od 0 do 255)

from matplotlib import pyplot as plt
from time import sleep
import paho.mqtt.client as mqtt
import csv

plt.ion()
size = 8
M = [[0 for j in range(size)] for i in range(size)]
fig = plt.figure(facecolor='black')
ax  = plt.subplot(111)
im  = ax.imshow(M,cmap='gray', vmin=0, vmax=1)
plt.axis('off')
n = 0.0
avg_values = []
meas_values = []
mng = plt.get_current_fig_manager()
mng.full_screen_toggle()

#Kilkusekundowe opóźnienie, podczas którego wyświetlamy czarny ekran
for k in range(3):
    M = [[0 for j in range(size)] for i in range(size)]
    im.set_array(M)
    fig.canvas.flush_events()
    sleep(1)


#Funkcja wywoływana po otrzymaniu wiadomości z mikrokontrolera
def on_message(mosq, obj, msg):
    global n

    #Po zakończeniu kalibracji: zapis do csv i wyświetlenie wykresu
    if n>=256: 
        with open('calibrate_gray.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',',
                                    quotechar=' ', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(['avg_values', 'meas_values'])
            for avg, meas in zip(avg_values,meas_values):
                writer.writerow([avg, meas])
        plt.ioff()
        plt.figure(2)
        plt.plot(avg_values,meas_values)
        plt.title("Obraz złożony z szarych pikseli")
        plt.xlabel("Średnia jasność obrazu")
        plt.ylabel("Zmierzona wartość")
        plt.show()
       
        exit()
        return
    
    #Wyświetlanie kolejnego obrazu, wpisanie pomiarów do tablicy, odesłanie wiadomości do mikrokontrolera
    M = [[n/255 for j in range(size)] for i in range(size)]
    avg_value = n/255
    print(str(n)+". avg value: "+str(avg_value)+", meas. value "+str(float(msg.payload)))
    avg_values.append(avg_value)
    meas_values.append(float(msg.payload))
    n = n + 1
    
    im.set_array(M)
    fig.canvas.flush_events() 
    mqttc.publish(Topic_Ping,1)


#Połączenie poprzez MQTT
MQTT_Broker = '192.168.0.115'
MQTT_Port = 1883
Keep_Alive_Interval = 45
Topic_Ping = 'PING'
Topic_Data = 'DATA'
mqttc = mqtt.Client()
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