import pygetwindow as pgw
import win32ui
import win32con
import win32gui
import numpy as np


class AppCapture:
    """Создаёт объект окна захватываемого приложения."""

    # constructor
    def __init__(self, title_marker):
        self.app_title = None
        self.title_marker = title_marker

        # Получаем идентификатор окна, который мы хотим захватить, по наличию маркера в его названии.
        for title in pgw.getAllTitles():
            if self.title_marker in title:
                self.app_title = title
                break
        if not self.app_title:
            # Генерит исключение, если идентификатор окна не найден.
            raise AttributeError('Окно приложения закрыто или не читается!')

        # Получаем параметры окна захваченного приложения.
        self.hwnd = win32gui.FindWindow(None, self.app_title)
        self.window_rect = win32gui.GetWindowRect(self.hwnd)
        self.x0 = self.window_rect[0]
        self.y0 = self.window_rect[1]
        self.x = self.window_rect[2]
        self.y = self.window_rect[3]
        self.width = self.x - self.x0
        self.height = self.y - self.y0

    def get_screenshot(self):
        """Возвращает скриншот(данные картинки) окна захваченного приложения."""
        if self.window_rect != win32gui.GetWindowRect(self.hwnd) or self.app_title not in pgw.getAllTitles():
            raise Exception  # Генерит исключение, если захватываемое приложение выключено или его рамки изменились.

        # Получаем данные изображения окна захватываемого приложения.
        wDC = win32gui.GetWindowDC(self.hwnd)
        dcObj = win32ui.CreateDCFromHandle(wDC)
        cDC = dcObj.CreateCompatibleDC()
        dataBitMap = win32ui.CreateBitmap()
        dataBitMap.CreateCompatibleBitmap(dcObj, self.width, self.height)
        cDC.SelectObject(dataBitMap)
        cDC.BitBlt((0, 0), (self.width, self.height), dcObj, (0, 0), win32con.SRCCOPY)

        # Конвертируем полученные данные в формат, читаемый библиотекой opencv-python.
        signedIntsArray = dataBitMap.GetBitmapBits(True)
        img = np.fromstring(signedIntsArray, dtype='uint8')
        img.shape = (self.height, self.width, 4)

        # Освобождаем ненужные ресурсы.
        dcObj.DeleteDC()
        cDC.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, wDC)
        win32gui.DeleteObject(dataBitMap.GetHandle())

        # Избавляемся от альфа-канала, чтобы не получать ошибки типа:
        #   error: (-215:Assertion failed) (depth == CV_8U || depth == CV_32F) && type == _templ.type() && _img.dims()
        #   <= 2 in function 'cv::matchTemplate'
        img = img[..., :3]

        # Делаем картинку C_CONTIGUOUS, чтобы избежать ошибок типа:
        #   File ... in draw_rectangles
        #   TypeError: an integer is required (got type tuple)
        # Подробнее здесь: https://github.com/opencv/opencv/issues/14866#issuecomment-580207109
        img = np.ascontiguousarray(img)

        return img
