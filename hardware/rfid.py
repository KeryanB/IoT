import mfrc522
import time

reader = mfrc522.MFRC522()

def read_rfid_uid(timeout=10):
    """
    Lit l'UID d'une carte RFID. Retourne None si aucun badge au bout de `timeout` secondes.
    """
    start = time.time()
    while time.time() - start < timeout:
        (status, _) = reader.MFRC522_Request(reader.PICC_REQIDL)
        if status == reader.MI_OK:
            (status, uid) = reader.MFRC522_Anticoll()
            if status == reader.MI_OK:
                return ''.join([str(i) for i in uid])
        time.sleep(0.2)
    return None
