import network
import urequests
import dht

from machine import Pin
from time import sleep

# ===================================
# WIFI
# ===================================

SSID = "WIFI"
PASSWORD = ""

wifi = network.WLAN(network.STA_IF)
wifi.active(True)

# ===================================
# CONNECT WIFI
# ===================================

def connect_wifi():

    if not wifi.isconnected():

        print("Connecting WiFi...")

        wifi.connect(SSID, PASSWORD)

        timeout = 0

        while not wifi.isconnected():

            sleep(1)

            timeout += 1

            if timeout > 20:
                print("WiFi Failed")
                return False

        print("WiFi Connected")
        print(wifi.ifconfig())

    return True

connect_wifi()

# ===================================
# RELAY
# ===================================

relay = Pin(2, Pin.OUT)

# ===================================
# DHT11
# ===================================

dht_sensor = dht.DHT11(Pin(4))

# ===================================
# SERVER
# ===================================

GET_SERVER = "http://10.15.1.250:5008/esp32"
POST_SERVER = "http://10.15.1.250:5008/update"

# ===================================
# STATUS
# ===================================

relay_status = 0

# ===================================
# READ SENSOR
# ===================================

def read_sensor():

    try:

        dht_sensor.measure()

        suhu = dht_sensor.temperature()
        kelembaban = dht_sensor.humidity()

        # ==========================
        # VALIDASI DATA
        # ==========================

        if suhu is None or kelembaban is None:
            return None, None

        if suhu < 0 or suhu > 80:
            return None, None

        if kelembaban < 0 or kelembaban > 100:
            return None, None

        return suhu, kelembaban

    except Exception as e:

        print("Sensor Error:", e)

        return None, None

# ===================================
# LOOP
# ===================================

while True:

    try:

        # ==========================
        # CHECK WIFI
        # ==========================

        connect_wifi()

        # ==========================
        # SENSOR RETRY
        # ==========================

        suhu = None
        kelembaban = None

        retry = 0

        while retry < 3:

            suhu, kelembaban = read_sensor()

            if suhu is not None:
                break

            retry += 1

            print("Retry Sensor:", retry)

            sleep(1)

        # ==========================
        # SENSOR RUSAK
        # ==========================

        if suhu is None:

            print("========================")
            print("DHT11 SENSOR FAILED")
            print("========================")

            # MATIKAN RELAY UNTUK KEAMANAN
            relay.value(0)
            relay_status = 0

            payload = {

                "temperature": -1,
                "humidity": -1,
                "relay": relay_status,
                "sensor_status": "ERROR"

            }

            try:

                response = urequests.post(
                    POST_SERVER,
                    json=payload
                )

                response.close()

            except Exception as e:
                print("POST Error:", e)

            sleep(5)

            continue

        # ==========================
        # SENSOR NORMAL
        # ==========================

        print("========================")
        print("Suhu:", suhu)
        print("Kelembaban:", kelembaban)
        print("========================")

        # ==========================
        # AUTO CONTROL
        # ==========================

        if suhu >= 32:

            relay.value(0)
            relay_status = 0

            print("Lampu OFF")

        elif suhu <= 30:

            relay.value(1)
            relay_status = 1

            print("Lampu ON")

        else:

            # ==========================
            # SERVER CONTROL
            # ==========================

            try:

                response = urequests.get(GET_SERVER)

                data = response.json()

                response.close()

                if data["relay"] == 1:

                    relay.value(1)
                    relay_status = 1

                else:

                    relay.value(0)
                    relay_status = 0

            except Exception as e:

                print("GET Error:", e)

        # ==========================
        # SEND DATA
        # ==========================

        payload = {

            "temperature": suhu,
            "humidity": kelembaban,
            "relay": relay_status,
            "sensor_status": "OK"

        }

        try:

            response = urequests.post(
                POST_SERVER,
                json=payload
            )

            print("Data Sent")
            print(payload)

            response.close()

        except Exception as e:

            print("POST Error:", e)

    except Exception as e:

        print("Main Loop Error:", e)

    sleep(2)