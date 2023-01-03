class RoiCapture:
    """Задаёт параметры необходимой области в окне главного родительского приложения по входным координатам."""

    # constructor
    def __init__(self, parent_window_width, parent_window_height, x0_coords, y0_coords, x_coords, y_coords):
        """Конструктор принимает длину и ширину родительского окна, а также относительные координаты нужной области
        на этом окне. Относительные координаты - это процентное выражение параметров главного родительского окна /1000.
        Словарь относительных координат хранится в файле coords_dict.json и доступен пользователю из папки проекта."""
        self.x0 = int(parent_window_width * x0_coords / 1000)
        self.y0 = int(parent_window_height * y0_coords / 1000)
        self.x = int(parent_window_width * x_coords / 1000)
        self.y = int(parent_window_height * y_coords / 1000)
        self.width = self.x - self.x0 - 1  # -1 для корректн. отображ. рамок обрамления при исп. метода cv2.Rectangle().
        self.height = self.y - self.y0 - 1

    def get_roi_data(self, parent_window):
        """Возвращает данные искомой области родительского окна"""
        return parent_window[self.y0: self.y, self.x0: self.x]
