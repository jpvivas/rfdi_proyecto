import RPi.GPIO as GPIO
from MFRC522python.MFRC522 import MFRC522
import signal
import pymysql
pymysql.install_as_MySQLdb()
import MySQLdb
import sys 
import time
from datetime import datetime,date

continue_reading = True
guardando = False
TRUE = 1
FALSE = 0
gpio_led_red = int(38)
gpio_led_green = int(36)

# GPIO_DOS.setmode(GPIO_DOS.BCM)
#GPIO.setmode(GPIO.BCM)
# mode = GPIO_DOS.getmode()
# GPIO_DOS.cleanup()
# GPIO_DOS.setmode(GPIO_DOS.BCM)
# GPIO_DOS.setup(16, GPIO_DOS.OUT)
# GPIO_DOS.setup(20, GPIO_DOS.OUT)

def end_read(signal,frame):
    global continue_reading
    print ("Ctrl + C capturado, finalizando la lectura.")
    continue_reading = False
    GPIO.cleanup()

# señal de tarjetas
signal.signal(signal.SIGINT, end_read)

# iniciar la clase MFRC522 tarjeta
MIFAREReader = MFRC522()
GPIO.output(gpio_led_green,1)
GPIO.output(gpio_led_red,1)
# Mensaje de inicio
print ("Bienvenido a la lectura de Tarjeta")
print ("Presiona Ctrl-C para terminar la ejecucion.")


# Este lazo sigue buscando chips. Si uno está cerca, obtendrá el UID y se autenticará
while continue_reading:
    if guardando:
        print ("Comprobando permiso...")
        continue

    # Scan for cards    
    (status,TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)

    (status,uid) = MIFAREReader.MFRC522_Anticoll()

    if status == MIFAREReader.MI_OK:
        # El UID de la tarjeta es la concatenacion de todos los string
        cardUID = str(uid[0])+str(uid[1])+str(uid[2])+str(uid[3])

        try:
            # conexion a la base de datos
            conn = MySQLdb.connect(user="admin2", passwd="admin2", host="localhost", db="projecto_ras", port=3306)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM personas_personas WHERE is_active='0' AND tarjeta_uid="+cardUID)
            result = cursor.fetchall()
            auth = []
            for row in result:
                auth = row

            if auth:
                print("autenticacion correcta")
                query_datos_existentes = """
                SELECT
                    datos.* 
                FROM datos_datos as datos 
                    INNER JOIN personas_personas_datos as personas_datos ON (personas_datos.datos_id = datos.id)
                    INNER JOIN personas_personas as personas ON (personas.id = personas_datos.personas_id)
                WHERE 
                    personas.id = {id_persona}
                    AND personas.is_active = '0'
                    AND datos.is_active = '0'

                ORDER by datos.date_creation DESC
                LIMIT 1
                """.format(id_persona=auth[0])
                cursor.execute(query_datos_existentes)
                resultado_datos = cursor.fetchall()
                datos = []
                for row_datos in resultado_datos:
                    datos = row_datos
                if datos:
                    fecha_creacion = datetime.now()
                    hora = datetime.now()
                    print(datos)
                    if datos[2]=="entra":
                        tipo = "sale"                        
                    elif datos[2]=="sale":
                        tipo = "entra"
                    else:
                        tipo = "entra"
                    query_consecutivo_datos = """
                    SELECT id FROM datos_datos  ORDER by date_creation DESC LIMIT 1
                    """
                    cursor.execute(query_consecutivo_datos)                    
                    resulta_conse = cursor.fetchall()
                    consec = 0
                    for row_conse in resulta_conse:
                        consec = int(row_conse[0])
                    consecutivo = consec + 1
                    
                    cursor.execute("""INSERT INTO datos_datos VALUES (%s,%s,%s,%s,%s,%s)""",(consecutivo,fecha_creacion,tipo,hora,'0','1'))
                    conn.commit()
                    cursor.execute("""INSERT INTO personas_personas_datos VALUES (%s,%s,%s)""",(None,auth[0],consecutivo))
                    conn.commit()
                    conn.close()

                    GPIO.output(gpio_led_green,GPIO.LOW)
                    GPIO.output(gpio_led_red,GPIO.HIGH)
            else:
                GPIO.output(gpio_led_green,GPIO.HIGH)
                GPIO.output(gpio_led_red,GPIO.LOW)
                print("No existe registro")

        except  Exception as e:
            print(e)
            conn.close()

        key = [0xFF,0xFF,0xFF,0xFF,0xFF,0xFF]          
        # Select the scanned tag
        MIFAREReader.MFRC522_SelectTag(uid)

        # Authenticate
        status = MIFAREReader.MFRC522_Auth(MIFAREReader.PICC_AUTHENT1A, 8, key, uid)

        # Check if authenticated
        if status == MIFAREReader.MI_OK:
            MIFAREReader.MFRC522_Read(8)
            MIFAREReader.MFRC522_StopCrypto1()
            time.sleep(5)
        else:
            print ("Authentication error")
            time.sleep(5)
        GPIO.output(gpio_led_green,GPIO.HIGH)
        GPIO.output(gpio_led_red,GPIO.HIGH)
