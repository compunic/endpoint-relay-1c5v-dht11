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
# WIFI LED (GPIO 2)
# ===================================

wifi_led = Pin(2, Pin.OUT)
wifi_led.value(0)

# ===================================
# RELAY (GPIO 5)
# ===================================

relay = Pin(5, Pin.OUT)
relay.value(0)

# ===================================
# BUZZER (GPIO 19)
# ===================================

buzzer = Pin(19, Pin.OUT)
buzzer.value(0)

# ===================================
# DHT11 (GPIO 4)
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
# BUZZER BEEP 2X
# ===================================

def beep_success():

    try:

        for i in range(2):

            buzzer.value(1)
            sleep(0.15)

            buzzer.value(0)
            sleep(0.15)

    except Exception as e:

        print("Buzzer Error:", e)

# ===================================
# CONNECT WIFI
# ===================================

def connect_wifi():

    if not wifi.isconnected():

        wifi_led.value(0)

        print("================================")
        print("Connecting WiFi...")
        print("================================")

        wifi.connect(SSID, PASSWORD)

        timeout = 0

        while not wifi.isconnected():

            sleep(1)

            timeout += 1

            print("Waiting...", timeout)

            if timeout > 20:

                print("WiFi Failed")

                wifi_led.value(0)

                return False

        print("================================")
        print("WiFi Connected")
        print(wifi.ifconfig())
        print("================================")

        wifi_led.value(1)

    else:

        wifi_led.value(1)

    return True

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
# START WIFI
# ===================================

connect_wifi()

# ===================================
# MAIN LOOP
# ===================================

while True:

    try:

        # ==========================
        # CHECK WIFI
        # ==========================

        if not connect_wifi():

            sleep(5)
            continue

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
        # SENSOR ERROR
        # ==========================

        if suhu is None:

            print("========================")
            print("DHT11 SENSOR FAILED")
            print("========================")

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

                print("Error Status Sent")

                beep_success()

            except Exception as e:

                print("POST Error:", e)

            sleep(5)

            continue

        # ==========================
        # SENSOR NORMAL
        # ==========================

        print("========================")
        print("Suhu       :", suhu, "°C")
        print("Kelembaban :", kelembaban, "%")
        print("========================")

        # ==========================
        # AUTO CONTROL
        # ==========================

        if suhu >= 32:

            relay.value(0)
            relay_status = 0

            print("Lampu OFF (AUTO)")

        elif suhu <= 30:

            relay.value(1)
            relay_status = 1

            print("Lampu ON (AUTO)")

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

                    print("Lampu ON (SERVER)")

                else:

                    relay.value(0)
                    relay_status = 0

                    print("Lampu OFF (SERVER)")

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

            print("========================")
            print("DATA SENT")
            print(payload)
            print("========================")

            response.close()

            # BEEP 2X JIKA BERHASIL
            beep_success()

        except Exception as e:

            print("POST Error:", e)

    except Exception as e:

        print("Main Loop Error:", e)

    sleep(2)
