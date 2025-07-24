import threading
import time
import random
import tkinter as tk
import pyautogui
import keyboard

# ----------------------------
# Настройка pyautogui
# ----------------------------
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

# относительные параметры (базовое 1920×1080)
WATCH_REL    = (291/1920, 447/1080)   # точка для авто-стопа
TARGET_COLOR = (231, 180, 119)       # нужный цвет
COLOR_TOL    = 10                    # погрешность +/-10

def color_match(c1, c2, tol=COLOR_TOL):
    return all(abs(a - b) <= tol for a, b in zip(c1, c2))


class BaseMode:
    def __init__(self):
        self.thread     = None
        self.stop_event = threading.Event()

    def is_running(self):
        return self.thread and self.thread.is_alive()

    def start(self):
        if self.is_running():
            return
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()

    def _pause(self, base=0.1):
        time.sleep(base + random.uniform(0, base))


class AltMode(BaseMode):
    def __init__(self):
        super().__init__()
        self.seq = [
            (118/1920, 270/1080, 'right'),
            (302/1920, 506/1080, 'left'),
            (226/1920, 325/1080, 'right'),
            (302/1920, 506/1080, 'left'),
        ]

    def _run(self):
        sw, sh = pyautogui.size()
        wx = int(sw * WATCH_REL[0])
        wy = int(sh * WATCH_REL[1])

        time.sleep(0.3)
        while not self.stop_event.is_set():
            # перед циклом кликов проверяем цвет пикселя
            time.sleep(0.1)
            pix = pyautogui.screenshot(region=(wx, wy, 1, 1)).getpixel((0, 0))
            if color_match(pix, TARGET_COLOR):
                return

            for xr, yr, btn in self.seq:
                if self.stop_event.is_set():
                    return
                x, y = int(sw * xr), int(sh * yr)
                pyautogui.moveTo(x, y)
                self._pause(0.1)
                pyautogui.click(button=btn)
                self._pause(0.1)
            time.sleep(0.2)


class NoAltMode(BaseMode):
    def __init__(self):
        super().__init__()
        self.init = [(118/1920, 270/1080, 'right')]
        self.loop = [(302/1920, 506/1080, 'left')]

    def _run(self):
        sw, sh = pyautogui.size()
        wx = int(sw * WATCH_REL[0])
        wy = int(sh * WATCH_REL[1])

        pyautogui.keyDown('shift')
        try:
            # один правый клик
            for xr, yr, btn in self.init:
                if self.stop_event.is_set():
                    return
                x, y = int(sw * xr), int(sh * yr)
                pyautogui.moveTo(x, y); self._pause()
                pyautogui.click(button=btn); self._pause()

            # левые клики до совпадения
            lx, ly = int(sw * self.loop[0][0]), int(sh * self.loop[0][1])
            while not self.stop_event.is_set():
                time.sleep(0.1)
                pix = pyautogui.screenshot(region=(wx, wy, 1, 1)).getpixel((0, 0))
                if color_match(pix, TARGET_COLOR):
                    return
                pyautogui.moveTo(lx, ly); self._pause()
                pyautogui.click(button='left'); self._pause()
        finally:
            pyautogui.keyUp('shift')
            self.stop_event.set()


class RegalMode(BaseMode):
    def __init__(self):
        super().__init__()
        self.init = [(118/1920, 270/1080, 'right')]
        self.loop = [(302/1920, 506/1080, 'left')]
        self.post = [
            (226/1920, 325/1080, 'right'),
            (302/1920, 506/1080, 'left'),
        ]
        self.match = [
            (432/1920, 267/1080, 'right'),
            (302/1920, 506/1080, 'left'),
        ]

    def _run(self):
        sw, sh = pyautogui.size()
        wx = int(sw * WATCH_REL[0])
        wy = int(sh * WATCH_REL[1])

        pyautogui.keyDown('shift')
        try:
            # init right-click
            for xr, yr, btn in self.init:
                if self.stop_event.is_set(): return
                x, y = int(sw * xr), int(sh * yr)
                pyautogui.moveTo(x, y); self._pause()
                pyautogui.click(button=btn); self._pause()

            # loop left-click until match
            lx, ly = int(sw * self.loop[0][0]), int(sh * self.loop[0][1])
            while not self.stop_event.is_set():
                time.sleep(0.1)
                pix = pyautogui.screenshot(region=(wx, wy, 1, 1)).getpixel((0, 0))
                if color_match(pix, TARGET_COLOR):
                    pyautogui.keyUp('shift')
                    break
                pyautogui.moveTo(lx, ly); self._pause()
                pyautogui.click(button='left'); self._pause()

            # post-shift clicks
            for xr, yr, btn in self.post:
                if self.stop_event.is_set(): return
                x, y = int(sw * xr), int(sh * yr)
                self._pause(); pyautogui.moveTo(x, y); self._pause()
                pyautogui.click(button=btn); self._pause()

            # final on-match clicks with extra delay
            for xr, yr, btn in self.match:
                if self.stop_event.is_set(): return
                x, y = int(sw * xr), int(sh * yr)
                time.sleep(0.2); pyautogui.moveTo(x, y); time.sleep(0.2)
                pyautogui.click(button=btn); time.sleep(0.2)
        finally:
            pyautogui.keyUp('shift')
            self.stop_event.set()


class App(tk.Tk):
    MODES = [
        ("Aug", "aug"),
        ("Alt+Aug", "altaug"),
        ("Alt+aug+Regal", "regal"),
    ]
    MODE_ATTRS = {
        "aug": "aug",
        "altaug": "altaug",
        "regal": "regal",
    }

    def __init__(self):
        super().__init__()
        self.title("Multi-Mode Automator")
        self.geometry("400x230")
        self.resizable(False, False)
        self.attributes('-topmost', True)

        self.aug    = AltMode()
        self.altaug = NoAltMode()
        self.regal  = RegalMode()
        self.mode   = tk.StringVar(value="aug")
        self.status = tk.StringVar(value="Ожидание")

        self._build_ui()
        keyboard.on_press_key("f3", lambda _: self._toggle())  # F3 только старт/стоп
        # keyboard.on_press_key("f4", lambda _: self.start())   # F4 убрана
        # keyboard.on_press_key("f5", lambda _: self.stop())

    def _build_ui(self):
        tk.Label(self, text="Выберите режим работы:", font=("Arial", 11, "bold")).pack(pady=(10, 0))

        frm = tk.Frame(self); frm.pack(pady=5)
        for txt, val in self.MODES:
            tk.Radiobutton(frm, text=txt, variable=self.mode, value=val, font=("Arial", 10))\
              .pack(side="left", padx=8)

        tk.Label(self, text="-------------------------------------------", justify="center").pack(pady=5)

        btns = tk.Frame(self); btns.pack(pady=5)
        self.toggle_btn = tk.Button(btns, text="Запустить (F3)", width=20, command=self._toggle)
        self.toggle_btn.pack(side="left", padx=8)

        tk.Label(self, text="Горячая клавиша F3 — запуск/остановка режима", font=("Arial", 9, "italic"), fg="gray")\
            .pack(pady=(5, 0))

        status_frm = tk.Frame(self); status_frm.pack(pady=8)
        tk.Label(status_frm, text="Текущий режим:", font=("Arial", 10)).pack(side="left")
        self.mode_lbl = tk.Label(status_frm, textvariable=self.mode, font=("Arial", 10, "bold"), fg="blue")
        self.mode_lbl.pack(side="left", padx=5)
        tk.Label(status_frm, text="Статус:", font=("Arial", 10)).pack(side="left", padx=(20,0))
        self.status_lbl = tk.Label(status_frm, textvariable=self.status, font=("Arial", 10, "bold"), fg="green")
        self.status_lbl.pack(side="left", padx=5)

        self.after(300, self._update_toggle_btn)

    def _update_toggle_btn(self):
        m = self.get_mode_instance()
        if m.is_running():
            self.toggle_btn.config(text="Остановить (F3)")
        else:
            self.toggle_btn.config(text="Запустить (F3)")
        self.after(300, self._update_toggle_btn)

    def get_mode_instance(self):
        attr = self.MODE_ATTRS.get(self.mode.get())
        return getattr(self, attr)

    def start(self):
        m = self.get_mode_instance()
        if m.is_running():
            self.status.set("Уже запущено")
            return
        try:
            m.start()
            self.status.set("Запущено")
        except Exception as e:
            self.status.set(f"Ошибка: {e}")

    def stop(self):
        m = self.get_mode_instance()
        if not m.is_running():
            self.status.set("Не запущено")
            return
        try:
            m.stop()
            self.status.set("Остановлено")
        except Exception as e:
            self.status.set(f"Ошибка: {e}")

    def _toggle(self):
        m = self.get_mode_instance()
        if m.is_running():
            self.stop()
        else:
            m.start()


if __name__ == "__main__":
    app = App()
    app.mainloop()
