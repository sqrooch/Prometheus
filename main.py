import numpy as np
import json
import cv2
import winsound as sound
from app_capture import AppCapture
from roi_capture import RoiCapture

# Маркер названия окна захватываемого приложения. Передаётся при поиске идентификатора окна.
TITLE_MARKER = 'AFH'

# Диапазоны границ цветов(BGR), которые участвуют в поиске объектов на экране захватываемого изображения.
GOLD_LOW = np.array([85, 182, 231])
GOLD_UP = np.array([107, 186, 240])
WHITE_LOW = np.array([237, 241, 237])
WHITE_UP = np.array([255, 255, 255])

# Распаковываем координаты областей захвата из файла словаря координат.
# Относительные координаты областей - это процентное выражение параметров главного родительского окна /1000.
# Словарь относительных координат хранится в файле coords_dict.json и доступен пользователю из папки проекта.
with open('coords_dict.json', 'r') as cords_input_file:
    cords_dict = json.load(cords_input_file)

# Координаты областей игрового поля, где можно захватить кнопку дилера.
btn1_coordinates = cords_dict['btn1']
btn2_coordinates = cords_dict['btn2']
btn3_coordinates = cords_dict['btn3']
btn4_coordinates = cords_dict['btn4']

# Координаты областей игрового поля, где можно захватить ставки игроков.
bet1_coordinates = cords_dict['bet1']
bet2_coordinates = cords_dict['bet2']
bet3_coordinates = cords_dict['bet3']
bet4_coordinates = cords_dict['bet4']

# Координаты областей игрового поля, где можно захватить сигнал для хода моего игрока.
move_signal_coordinates = cords_dict['move_signal']

# Координаты областей игрового поля, где можно захватить сигнал, который говорит о том, что все карты розданы.
dist_signal_coordinates = cords_dict['dist_signal']

# Координаты областей игрового поля, которые говорят о присутствии игроков за столом.
hand2_coordinates = cords_dict['hand2']
hand3_coordinates = cords_dict['hand3']
hand4_coordinates = cords_dict['hand4']

cards_distributed = False  # Флаг раздачи карт. По умолчанию выключен.

# Глобальные переменные для позиций. Принимают значения от 1 до 4-х и указывают на каких позиция находятся игроки.
# Номера 2, 3 и 4 - номера оппонентов. Номер 1 - Герой, т.е. игрок, за которого мы играем.
# По умолчанию все позиции неактивны.
btn = False
bb = False
sb = False
co = False
# Переменная диспозиции игроков, которая всегда состоит из четырёх маркеров.
# Каждый маркер - это действие оппонентов в раунде, к тому моменту, когда моему игроку надо принять решение:
# p (push) - Оппонент сделал ставку до моего игрока.
# f (fold) - Оппонент сбросил карты до моего игрока.
# x - Оппоненты, которые находятся позади моего игрока. Их действие невозможно спрогнозировать.
# h (hero) - Маркер моего игрока.
# Например: комплект маркеров для диспозиции 'pfhx' будет означать, что герой находится на позиции малого блайнда (sb).
# До него один игрок сделал ставку, второй игрок сбросил карты, и ещё один игрок будет ходить после него.
# Каждый комплект маркеров диспозиции соответствует комплекту рук, с которыми Герой может сделать ход.
# Как только диспозиция в раунде становится ясна, из папки ranges загружается соответственный набор рук.
disposition = 'ppph'  # По умолчанию произвольный набор маркеров, пока раунд не сгенерирует реальную диспозицию.
disposition_completed = True  # Флаг наличия диспозиции в раунде. По умолчанию отключен.


def find_color(roi_img, COLOR_LOW, COLOR_UP):
    """Проверяет наличие цвета в области окна приложения. Возвращает True или False."""
    color_range = cv2.inRange(roi_img, COLOR_LOW, COLOR_UP)
    return True if 255 in color_range else False


def get_btn():
    """Назначает позицию btn конкретному игроку."""
    if find_color(btn1_img, GOLD_LOW, GOLD_UP):
        return 1
    elif find_color(btn2_img, GOLD_LOW, GOLD_UP):
        return 2
    elif find_color(btn3_img, GOLD_LOW, GOLD_UP):
        return 3
    elif find_color(btn4_img, GOLD_LOW, GOLD_UP):
        return 4
    else:
        return False


def get_bb(btn_val):
    """Назначает позицию bb конкретному игроку."""
    img_box = (bet1_img, bet2_img, bet3_img, bet4_img)
    val = btn_val % 4
    while val != (btn_val - 1):
        if find_color(img_box[val], WHITE_LOW, WHITE_UP):
            return val + 1
        val += 1
        val %= 4


def get_sb(bb_val):
    """Назначает позицию sb конкретному игроку."""
    img_box = (bet1_img, bet2_img, bet3_img, bet4_img)
    val = bb_val % 4
    while val != (bb_val - 1):
        if find_color(img_box[val], WHITE_LOW, WHITE_UP):
            return val + 1
        val += 1
        val %= 4


# Основной цикл программы:
while True:
    try:
        btn_old_version = False  # По умолчанию кнопка дилера ещё не инициализирована.

        # Создаём объекты главного окна захватываемого приложения, а затем и всех интересующих нас областей экрана.
        app_capture = AppCapture(TITLE_MARKER)

        btn1_capture = RoiCapture(app_capture.width, app_capture.height, *btn1_coordinates)
        btn2_capture = RoiCapture(app_capture.width, app_capture.height, *btn2_coordinates)
        btn3_capture = RoiCapture(app_capture.width, app_capture.height, *btn3_coordinates)
        btn4_capture = RoiCapture(app_capture.width, app_capture.height, *btn4_coordinates)

        bet1_capture = RoiCapture(app_capture.width, app_capture.height, *bet1_coordinates)
        bet2_capture = RoiCapture(app_capture.width, app_capture.height, *bet2_coordinates)
        bet3_capture = RoiCapture(app_capture.width, app_capture.height, *bet3_coordinates)
        bet4_capture = RoiCapture(app_capture.width, app_capture.height, *bet4_coordinates)

        turn_signal_capture = RoiCapture(app_capture.width, app_capture.height, *move_signal_coordinates)
        dist_signal_capture = RoiCapture(app_capture.width, app_capture.height, *dist_signal_coordinates)

        hand2_capture = RoiCapture(app_capture.width, app_capture.height, *hand2_coordinates)
        hand3_capture = RoiCapture(app_capture.width, app_capture.height, *hand3_coordinates)
        hand4_capture = RoiCapture(app_capture.width, app_capture.height, *hand4_coordinates)

    except (Exception,):
        break  # При закрытии приложении или других ошибках, программа завершает работу.

    # Далее следует цикл раунда:
    while True:
        try:
            # Делаем скриншот главного приложения.
            app_window = app_capture.get_screenshot()

            # Создаём объекты изображений областей скриншота, с которыми будем работать.
            btn1_img = btn1_capture.get_roi_data(app_window)
            btn2_img = btn2_capture.get_roi_data(app_window)
            btn3_img = btn3_capture.get_roi_data(app_window)
            btn4_img = btn4_capture.get_roi_data(app_window)

            bet1_img = bet1_capture.get_roi_data(app_window)
            bet2_img = bet2_capture.get_roi_data(app_window)
            bet3_img = bet3_capture.get_roi_data(app_window)
            bet4_img = bet4_capture.get_roi_data(app_window)

            turn_signal_img = turn_signal_capture.get_roi_data(app_window)
            dist_signal_img = dist_signal_capture.get_roi_data(app_window)

            hand2_img = hand2_capture.get_roi_data(app_window)
            hand3_img = hand3_capture.get_roi_data(app_window)
            hand4_img = hand4_capture.get_roi_data(app_window)

            # Обрамляем их рамками и маркируем по цветам, чтобы пользователь мог их различить.
            cv2.rectangle(btn1_img, (0, 0), (btn1_capture.width, btn1_capture.height), (255, 153, 0), thickness=1)
            cv2.rectangle(btn2_img, (0, 0), (btn2_capture.width, btn2_capture.height), (255, 153, 0), thickness=1)
            cv2.rectangle(btn3_img, (0, 0), (btn3_capture.width, btn3_capture.height), (255, 153, 0), thickness=1)
            cv2.rectangle(btn4_img, (0, 0), (btn4_capture.width, btn4_capture.height), (255, 153, 0), thickness=1)

            cv2.rectangle(bet1_img, (0, 0), (bet1_capture.width, bet1_capture.height), (0, 0, 255), thickness=1)
            cv2.rectangle(bet2_img, (0, 0), (bet2_capture.width, bet2_capture.height), (0, 0, 255), thickness=1)
            cv2.rectangle(bet3_img, (0, 0), (bet3_capture.width, bet3_capture.height), (0, 0, 255), thickness=1)
            cv2.rectangle(bet4_img, (0, 0), (bet4_capture.width, bet4_capture.height), (0, 0, 255), thickness=1)

            cv2.rectangle(turn_signal_img, (0, 0), (turn_signal_capture.width, turn_signal_capture.height),
                          (0, 153, 255), thickness=1)
            cv2.rectangle(dist_signal_img, (0, 0), (dist_signal_capture.width, dist_signal_capture.height),
                          (255, 0, 204), thickness=1)

            cv2.rectangle(hand2_img, (0, 0), (hand2_capture.width, hand2_capture.height), (0, 255, 0), thickness=1)
            cv2.rectangle(hand3_img, (0, 0), (hand3_capture.width, hand3_capture.height), (0, 255, 0), thickness=1)
            cv2.rectangle(hand4_img, (0, 0), (hand4_capture.width, hand4_capture.height), (0, 255, 0), thickness=1)

            # Выводим всё на экран пользователю.
            cv2.imshow('Prometheus', app_window)
            # Если диспозиция сформирована, то выводим на экран диапазон наиболее успешных рук для данной диспозиции.
            if disposition_completed:
                cv2.imshow('Ranges', cv2.imread(fr'ranges\{disposition}.jpg'))
            cv2.waitKey(1)

        except (Exception,):
            break  # При ошибке программы, либо при изменении размеров окна,
            # выходим из цикла раунда и заново создаём все объекты областей захвата.

        # Изменение положения кнопки дилера означает начало нового раунда,
        # поэтому в каждом цикле мы отслеживаем позицию btn и сравниваем её со старой версией.
        btn = get_btn()
        if btn:
            if btn_old_version:
                if btn == btn_old_version:
                    # Если позиция btn равна старой версии, а диспозиция сформирована, то цикл откатывается в начало.
                    if disposition_completed:
                        continue
                    # Если диспозиция игроков не сформирована, то цикл продолжает работу без обнуления раунда.
                else:
                    # Если же позиция btn изменилась, начинается новый раунд, все глобальные переменные пересчитываются.
                    # Начало раунда.
                    # Ждём, когда дилер раздаст карты и выставляем флаг раздачи карт.
                    if not cards_distributed:
                        if not find_color(dist_signal_img, WHITE_LOW, WHITE_UP):
                            continue
                        else:
                            cards_distributed = True

                    # Ищем игрока на позиции большого блайнда.
                    bb = get_bb(btn)
                    if bb is None:
                        continue

                    # Ищем игрока на позиции малого блайнда.
                    sb = get_sb(bb)
                    if sb is None:
                        continue

                    # Ищем игрока на позиции CutOff.
                    if btn != 1 and sb != 1 and bb != 1:
                        co = 1
                    else:
                        co = False

                    # Обнуляем маркеры диспозиции и выставляем флаги в False для корректной работы в следующем раунде.
                    cards_distributed = False
                    disposition = ''
                    disposition_completed = False
                    btn_old_version = btn

                    # Добавляем маркеры игроков, которые сидят после Героя в раунде.
                    if sb == 1 or btn == 1 or co == 1:
                        disposition += 'x'
                        if btn != sb and (btn == 1 or co == 1):
                            disposition += 'x'
                            if co == 1:
                                disposition += 'x'

                    # Добавляем маркер Героя в диспозицию и переворачиваем строку, для корректного отображения.
                    disposition += 'h'
                    if len(disposition) > 1:
                        disposition = disposition[::-1]

                    if co:  # Наличие позиции CutOff будет означать, что диспозиция сформирована.
                        disposition_completed = True
                        continue
            else:  # Если старая версия позиции btn отсутствует, назначаем её и начинаем цикл заново.
                btn_old_version = btn
                continue
        else:  # Если кнопка дилера не найдена, повторяем цикл.
            continue

        # Сигнал в нужной части экрана сигнализирует о том, что сейчас ход Героя.
        if not find_color(turn_signal_img, WHITE_LOW, WHITE_UP):
            continue

        # Самое время посмотреть какие ходы приняли наши оппоненты.
        # Создаём цикл в котором i - это номер игрока,
        # а img_line - это кортеж областей экрана (область наличия ставки, область наличия игрока за столом.)
        for i, img_line in enumerate((None,
                                      None,
                                      (bet2_img, hand2_img),
                                      (bet3_img, hand3_img),
                                      (bet4_img, hand4_img))):
            if img_line is None:
                continue  # Пропускаем ненужные номера игроков.
            if i == bb:
                break  # Как только дойдём до позиции большого блайнда, дальше проверять смысла нет.
            elif i == sb:
                # Если игрок на позиции малого блайнда всё ещё держит карты, значит он принял решение сделать ставку.
                # Маркируем его как 'p' - push.
                if find_color(img_line[1], WHITE_LOW, WHITE_UP):
                    disposition = 'p' + disposition
                else:  # В противном случае маркируем его как 'f' - fold.
                    disposition = 'f' + disposition
            elif i == btn:
                if btn == sb:  # Если значение btn и sb совпадают, то за столом находится всего два игрока.
                    break  # Дальнейшие действия не нужны.
                else:
                    # Если игрок на позиции btn сделал ставку, то маркируем его как 'p' - push.
                    if find_color(img_line[0], WHITE_LOW, WHITE_UP):
                        disposition = 'p' + disposition
                    else:
                        # В противном случае маркируем его как 'f' - fold.
                        disposition = 'f' + disposition
            else:
                # Проверяем также на наличие ставки оставшегося игрока на позиции CutOff.
                # Если он присутствует за столом и сделал ставку, то маркируем его как 'p' - push.
                if find_color(img_line[0], WHITE_LOW, WHITE_UP):
                    disposition = 'p' + disposition

        # Игроков не участвующих в раздаче или не сделавших ставку маркируем как 'f' - fold.
        while len(disposition) < 4:
            disposition = 'f' + disposition

        disposition_completed = True  # Диспозиция сформирована. Цикл раунда начинается заново.

# Завершение работы программы. Уничтожаем все окна.
cv2.destroyAllWindows()
# Звуковой сигнал пользователю о том, что программа закончила свою работу.
sound.Beep(500, 1000)
