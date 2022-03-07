import os
import os.path
from dotenv import load_dotenv
from cryptography.fernet import Fernet

load_dotenv()

LOG_DIR = os.getenv("LOG_DIR", "logs")
LOG_EXT = os.getenv("LOG_DIR", ".logz")
CRYPT_KEY = os.getenv("CRYPT_KEY", "")

fernet = Fernet(CRYPT_KEY)

for item in os.listdir(LOG_DIR):
    if item.endswith(LOG_EXT):
        path = os.path.join(LOG_DIR, item)
        data = None
        with open(path, mode="rb") as f:
            data = f.read()
        try:
            fernet.decrypt(data)
            print(f"{item} already encrypted")
        except:
            with open(path, mode="wb") as f:
                f.write(fernet.encrypt(data))
            print(f"{item} was encrypted")