
import pyautogui
import time

time.sleep(5)

pyautogui.keyDown("right")
time.sleep(0.05)
pyautogui.keyUp("right")

print("Pulsacion enviada.")
