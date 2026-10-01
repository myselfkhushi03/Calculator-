from threading import Thread
from keep_alive import run
from bot import run_bot

Thread(target=run).start()
run_bot()
