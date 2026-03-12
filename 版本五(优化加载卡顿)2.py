import cv2
import mediapipe as mp
import pygame
import time
import random
import math
import csv
import os
from datetime import datetime
import threading
import queue

# ---------------------- 题库（已替换为计算机基础） ----------------------
QUESTIONS_ZH = [
    {"question": "使用电脑时，不小心打翻水杯洒到键盘上，第一时间应该？",
     "options": ["A.继续用电脑", "B.立刻拔掉电源", "C.用纸巾擦"], "answer": "B"},
    {"question": "下列哪个是计算机的输入设备？", "options": ["A.显示器", "B.键盘", "C.音箱"], "answer": "B"},
    {"question": "在电脑上画图画时，想要撤销上一步操作，通常按哪个快捷键？",
     "options": ["A.Ctrl+Z", "B.Ctrl+C", "C.Ctrl+V"], "answer": "A"},
    {"question": "小学生使用电脑时，连续看屏幕最好不超过多久休息一次？", "options": ["A.2小时", "B.20分钟", "C.1小时"],
     "answer": "B"},
    {"question": "下列哪种行为符合网络安全规范？",
     "options": ["A.随便点开陌生链接", "B.设置复杂的密码", "C.把密码告诉同学"], "answer": "B"}
]
QUESTIONS_ENG = [
    {"question": "If water spills on the keyboard while using the computer, what should you do first?",
     "options": ["A.Keep using the computer", "B.Unplug the power immediately", "C.Wipe with tissue"], "answer": "B"},
    {"question": "Which of the following is an input device of a computer?",
     "options": ["A.Monitor", "B.Keyboard", "C.Speaker"], "answer": "B"},
    {"question": "When drawing on the computer, which shortcut key is usually used to undo the last operation?",
     "options": ["A.Ctrl+Z", "B.Ctrl+C", "C.Ctrl+V"], "answer": "A"},
    {
        "question": "When primary school students use computers, how often should they rest after looking at the screen continuously?",
        "options": ["A.2 hours", "B.20 minutes", "C.1 hour"], "answer": "B"},
    {"question": "Which behavior complies with network security norms?",
     "options": ["A.Click on unfamiliar links casually", "B.Set a complex password", "C.Tell classmates your password"],
     "answer": "B"}
]

# ---------------------- 初始化全局参数 ----------------------
pygame.init()
pygame.mixer.init()
pygame.font.init()

# 线程通信
camera_queue = queue.Queue()
camera_ready = False
camera_init_error = None

# 多语言文本配置（核心修复：全量英文文本）
lang_text = {
    "zh": {
        "window_title": "手势交互答题系统",
        "loading_init_camera": "系统加载中...（正在初始化摄像头）",
        "camera_ready": "摄像头已就绪，即将进入系统...",
        "camera_error": "摄像头初始化失败：{}",
        "version": "手势交互答题系统 v1.0",
        "start_btn": "开始",
        "record_btn": "记录",
        "setting_btn": "设置",
        "back_btn": "返回",
        "quiz_title": "计算机基础答题",
        "score": "分数：{}",
        "time_up_wrong": "时间到！回答错误",
        "correct": "回答正确！🎉",
        "wrong": "回答错误",
        "summary_title": "答题总结",
        "final_score": "最终得分：{}/{}",
        "q_num": "第{}题：{}",
        "q_num_short": "Q{}: {}",
        "correct_text": "正确",
        "wrong_text": "错误",
        "no_record": "暂无答题记录",
        "load_record_error": "读取记录失败: {}",
        "setting_title": "系统设置",
        "window_label": "窗口",
        "color_label": "圆色",
        "lang_label": "语言",
        "small_window": "小屏",
        "mid_window": "中屏",
        "full_window": "全屏",
        "blue_color": "蓝",
        "green_color": "绿",
        "red_color": "红",
        "chinese_lang": "中文",
        "english_lang": "英文",
        "people_count": "人数：{}",
        "correct_rate": "正确率",
        "wrong_questions": "错题序号"
    },
    "eng": {
        "window_title": "Gesture Interactive Quiz System",
        "loading_init_camera": "System loading... (Initializing camera)",
        "camera_ready": "Camera is ready, entering system soon...",
        "camera_error": "Camera init failed: {}",
        "version": "Gesture Interactive Quiz System v1.0",
        "start_btn": "Start",
        "record_btn": "Records",
        "setting_btn": "Settings",
        "back_btn": "Back",
        "quiz_title": "Computer Basics Quiz",
        "score": "Score: {}",
        "time_up_wrong": "Time up! Wrong answer",
        "correct": "Correct! 🎉",
        "wrong": "Wrong",
        "summary_title": "Quiz Summary",
        "final_score": "Final Score: {}/{}",
        "q_num": "Question {}: {}",
        "q_num_short": "Q{}: {}",
        "correct_text": "Correct",
        "wrong_text": "Wrong",
        "no_record": "No records yet",
        "load_record_error": "Load records failed: {}",
        "setting_title": "System Settings",
        "window_label": "Window",
        "color_label": "Palm Color",
        "lang_label": "Language",
        "small_window": "Small",
        "mid_window": "Medium",
        "full_window": "Full",
        "blue_color": "Blue",
        "green_color": "Green",
        "red_color": "Red",
        "chinese_lang": "Chinese",
        "english_lang": "English",
        "people_count": "People: {}",
        "correct_rate": "Accuracy",
        "wrong_questions": "Wrong Qs"
    }
}


def init_camera_background():
    """后台初始化摄像头"""
    global camera_ready, camera_init_error
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            raise Exception("Cannot open camera")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        camera_queue.put(cap)
        camera_ready = True
        camera_init_error = None
    except Exception as e:
        camera_init_error = str(e)
        camera_ready = False


def load_sound(file_path, volume=0.7):
    """加载音效"""
    try:
        sound = pygame.mixer.Sound(file_path)
        sound.set_volume(volume)
        return sound
    except:
        print(f"Tip: Sound file {file_path} not found, skip loading")
        return None


def load_bg_music(file_path, volume=0.5):
    """加载背景音乐"""
    try:
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(-1)
        return True
    except:
        print(f"Tip: BGM file {file_path} not found, skip playing")
        return False


# 加载音效
SOUND_CORRECT = load_sound("sounds/correct.mp3")
SOUND_WRONG = load_sound("sounds/wrong.mp3")
SOUND_PROGRESS = load_sound("sounds/progress.mp3")
SOUND_TIME_OUT = load_sound("sounds/timeout.wav")
SOUND_VICTORY = load_sound("sounds/victory.mp3", 0.8)
SOUND_DEFEAT = load_sound("sounds/defeat.mp3", 0.8)
load_bg_music("bg_music.mp3")

# 加载界面参数
loading_screen = True
loading_angle = 0
loading_radius = 30
loading_center = (400, 300)
loading_color = (0, 80, 200)
loading_thickness = 5

# 窗口初始化
screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
pygame.display.set_caption(lang_text["zh"]["window_title"])  # 初始标题
clock = pygame.time.Clock()
screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE | pygame.HWSURFACE)
desktop_w, desktop_h = pygame.display.Info().current_w, pygame.display.Info().current_h

# 全局设置
settings = {
    "window_mode": "中屏",
    "window_size": (800, 600),
    "hand_color": (0, 255, 0),
    "hand_color_name": "绿",
    "language": "zh",
    "font_scale": 1.0,
    "progress_speed": 33,
    "question_time": 20
}

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (30, 30, 30)
RED = (220, 0, 0)
GREEN = (0, 220, 0)
BLUE = (0, 80, 200)
LIGHT_BLUE = (230, 240, 255)
YELLOW = (255, 200, 0)
ORANGE = (255, 165, 0)
SELECTED_BORDER = ORANGE
BACK_CIRCLE_COLOR = (200, 50, 50)

# 状态定义
STATE_START = 0
STATE_ANSWER = 1
STATE_SUMMARY = 2
STATE_RECORD = 3
STATE_SETTING = 4
current_state = STATE_START

# 功能按钮
start_circle = {"pos": (200, 400), "radius": 60, "progress": 0}
record_circle = {"pos": (400, 400), "radius": 60, "progress": 0}
setting_circle = {"pos": (600, 400), "radius": 60, "progress": 0}
function_circles = [start_circle, record_circle, setting_circle]

# 返回按钮
back_circle = {
    "radius": 50,
    "progress": 0
}

PROGRESS_FULL = 100
PROGRESS_DECAY = 50

# 音效标记
progress_sound_played = False
victory_defeat_played = False

# 手部检测初始化
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=4,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)


def draw_loading_screen():
    """绘制加载界面（多语言适配）"""
    global loading_angle
    screen.fill(WHITE)

    # 字体适配
    try:
        font = pygame.font.SysFont(["Microsoft YaHei", "SimHei", "Arial"], 24)
        small_font = pygame.font.SysFont(["Microsoft YaHei", "SimHei", "Arial"], 18)
    except:
        font = pygame.font.Font(None, 24)
        small_font = pygame.font.Font(None, 18)

    # 加载文本（多语言）
    if camera_init_error:
        loading_text = font.render(lang_text[settings["language"]]["camera_error"].format(camera_init_error), True, RED)
    elif camera_ready:
        loading_text = font.render(lang_text[settings["language"]]["camera_ready"], True, GREEN)
    else:
        loading_text = font.render(lang_text[settings["language"]]["loading_init_camera"], True, BLUE)

    # 文本位置优化（避免遮挡）
    text_rect = loading_text.get_rect(center=(loading_center[0], loading_center[1] + 50))
    screen.blit(loading_text, text_rect)

    # 版本信息
    hint_text = small_font.render(lang_text[settings["language"]]["version"], True, BLACK)
    hint_rect = hint_text.get_rect(center=(loading_center[0], 550))
    screen.blit(hint_text, hint_rect)

    # 加载动画
    start_angle = loading_angle
    end_angle = loading_angle + 270
    loading_angle = (loading_angle + 5) % 360
    pygame.draw.arc(
        screen,
        loading_color,
        (
            loading_center[0] - loading_radius,
            loading_center[1] - loading_radius,
            loading_radius * 2,
            loading_radius * 2
        ),
        math.radians(start_angle),
        math.radians(end_angle),
        loading_thickness
    )

    pygame.display.update()


# 启动摄像头线程
camera_thread = threading.Thread(target=init_camera_background, daemon=True)
camera_thread.start()

# 加载界面循环
start_time = time.time()
while loading_screen:
    time_elapsed = time.time() - start_time
    if time_elapsed > 1.5 and (camera_ready or camera_init_error):
        loading_screen = False

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

    draw_loading_screen()
    clock.tick(60)

# 检查摄像头初始化
if camera_init_error:
    print(f"Error: {camera_init_error}")
    pygame.quit()
    exit()
else:
    cap = camera_queue.get()
    print("Camera initialized successfully!")


# 烟花特效类
class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.radius = random.randint(2, 5)
        self.speed = random.uniform(2, 6)
        self.angle = random.uniform(0, math.pi * 2)
        self.vx = math.cos(self.angle) * self.speed
        self.vy = math.sin(self.angle) * self.speed
        self.life = 100
        self.decay = 0.92

    def update(self):
        self.vy += 0.05
        self.x += self.vx
        self.y += self.vy
        self.life *= self.decay
        self.radius = max(1, self.radius * self.decay)

    def draw(self, surf):
        alpha = int(self.life * 2.55)
        if alpha > 0:
            pygame.draw.circle(surf, (*self.color, alpha), (int(self.x), int(self.y)), int(self.radius))


class Firework:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.color = random.choice([(255, 0, 0), (255, 165, 0), (255, 255, 0), (0, 255, 0), (0, 0, 255), (128, 0, 128)])
        self.particles = [Particle(x, y, self.color) for _ in range(80)]

    def update(self):
        for p in self.particles: p.update()
        self.particles = [p for p in self.particles if p.life > 10]

    def draw(self, surf):
        for p in self.particles: p.draw(surf)


fireworks = []

# 初始化题库
QUESTIONS = QUESTIONS_ZH if settings["language"] == "zh" else QUESTIONS_ENG
random.shuffle(QUESTIONS)

current_question = 0
score = 0
start_time = 0
left_time = settings["question_time"]


def get_option_areas():
    """获取选项区域（适配窗口大小）"""
    w, h = settings["window_size"]
    return {
        "A": (int(w * 0.1), int(h * 0.70), int(w * 0.25), int(h * 0.18)),
        "B": (int(w * 0.38), int(h * 0.70), int(w * 0.25), int(h * 0.18)),
        "C": (int(w * 0.65), int(h * 0.70), int(w * 0.25), int(h * 0.18)),
    }


option_areas = get_option_areas()

# 答题状态变量
hand_stay_time = {}
STAY_CONFIRM_TIME = 3
option_hand_count = {"A": 0, "B": 0, "C": 0}
answer_history = []
show_result = False
result_text = ""
result_show_time = 0
current_is_correct = False

# 记录文件配置
RECORD_FILE = "nte_answer_records.csv"
if not os.path.exists(RECORD_FILE):
    with open(RECORD_FILE, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(["时间", "总分", "答题数", "正确率", "错题序号"])


def get_font_sizes():
    """获取字体大小（适配缩放）"""
    scale = settings["font_scale"]
    return {
        "big": int(60 * scale),
        "title": int(40 * scale),
        "question": int(26 * scale),  # 英文适配：缩小字体
        "option": int(22 * scale),  # 英文适配：缩小字体
        "info": int(26 * scale),
        "count": int(24 * scale),
        "result": int(36 * scale),
        "mini": int(20 * scale)  # 英文适配：缩小记录字体
    }


def get_fonts():
    """获取字体（多语言适配）"""
    sizes = get_font_sizes()
    font_names = ["Microsoft YaHei", "SimHei", "Arial", "Helvetica"]
    font_name = None
    for name in font_names:
        if pygame.font.match_font(name):
            font_name = name
            break
    if font_name is None:
        font_name = pygame.font.get_default_font()

    return {
        "big": pygame.font.SysFont(font_name, sizes["big"], bold=True),
        "title": pygame.font.SysFont(font_name, sizes["title"], bold=True),
        "question": pygame.font.SysFont(font_name, sizes["question"]),
        "option": pygame.font.SysFont(font_name, sizes["option"]),
        "info": pygame.font.SysFont(font_name, sizes["info"]),
        "count": pygame.font.SysFont(font_name, sizes["count"], bold=True),
        "result": pygame.font.SysFont(font_name, sizes["result"], bold=True),
        "mini": pygame.font.SysFont(font_name, sizes["mini"])
    }


def get_palm_center(landmarks):
    """获取手掌中心"""
    x = sum(landmarks.landmark[i].x for i in [0, 5, 9, 13, 17]) / 5
    y = sum(landmarks.landmark[i].y for i in [0, 5, 9, 13, 17]) / 5
    w, h = settings["window_size"]
    return int(x * w), int(y * h)


def draw_palm_center(surf, center):
    """绘制手掌中心"""
    x, y = center
    r = int(18 * settings["font_scale"])
    pygame.draw.circle(surf, WHITE, (x, y), r)
    pygame.draw.circle(surf, settings["hand_color"], (x, y), r - 2)


def is_in_circle(pt, center, r):
    """判断点是否在圆内"""
    dx = pt[0] - center[0]
    dy = pt[1] - center[1]
    return math.hypot(dx, dy) <= r


def draw_circle_option(surf, center, r, text, progress, is_selected, color=BLUE):
    """绘制圆形按钮（多语言适配）"""
    global progress_sound_played
    pygame.draw.circle(surf, LIGHT_BLUE, center, r)
    if is_selected:
        pygame.draw.circle(surf, SELECTED_BORDER, center, r + 4, 4)
    pygame.draw.circle(surf, color, center, r, 2)

    # 进度条音效
    if progress >= 50 and not progress_sound_played and SOUND_PROGRESS:
        SOUND_PROGRESS.play()
        progress_sound_played = True
    elif progress < 50:
        progress_sound_played = False

    # 进度条绘制
    if progress > 0:
        angle = 2 * math.pi * (progress / PROGRESS_FULL)
        pygame.draw.arc(surf, YELLOW,
                        (center[0] - r - 5, center[1] - r - 5, (r + 5) * 2, (r + 5) * 2),
                        -math.pi / 2, -math.pi / 2 + angle, 4)

    # 文本绘制（适配英文）
    fonts = get_fonts()["info"]
    txt = fonts.render(text, True, BLACK)
    # 文本居中优化
    txt_rect = txt.get_rect(center=center)
    # 防止文本超出按钮
    if txt_rect.width > r * 1.8:
        # 缩小字体适配
        small_font = pygame.font.SysFont(fonts.name, int(fonts.get_height() * 0.8))
        txt = small_font.render(text, True, BLACK)
        txt_rect = txt.get_rect(center=center)
    surf.blit(txt, txt_rect)


def draw_back_circle(surf, delta_time, palms):
    """绘制返回按钮（多语言+位置优化）"""
    global progress_sound_played
    fonts = get_fonts()
    w, h = settings["window_size"]
    # 位置优化：避免遮挡其他元素
    back_center = (w - back_circle["radius"] - 30, h - back_circle["radius"] - 30)
    r = back_circle["radius"]

    # 检测手势
    touched = any(is_in_circle(p, back_center, r) for p in palms)
    if touched:
        back_circle["progress"] = min(PROGRESS_FULL, back_circle["progress"] + settings["progress_speed"] * delta_time)
        if back_circle["progress"] >= 50 and not progress_sound_played and SOUND_PROGRESS:
            SOUND_PROGRESS.play()
            progress_sound_played = True
    else:
        back_circle["progress"] = max(0, back_circle["progress"] - PROGRESS_DECAY * delta_time)
        progress_sound_played = False

    # 绘制按钮
    pygame.draw.circle(surf, BACK_CIRCLE_COLOR, back_center, r)
    pygame.draw.circle(surf, WHITE, back_center, r, 3)

    # 进度条
    if back_circle["progress"] > 0:
        angle = 2 * math.pi * (back_circle["progress"] / PROGRESS_FULL)
        pygame.draw.arc(surf, YELLOW,
                        (back_center[0] - r - 5, back_center[1] - r - 5, (r + 5) * 2, (r + 5) * 2),
                        -math.pi / 2, -math.pi / 2 + angle, 5)

    # 文本（多语言）
    text = lang_text[settings["language"]]["back_btn"]
    txt = fonts["info"].render(text, True, WHITE)
    # 文本适配
    if txt.get_width() > r * 1.5:
        small_font = pygame.font.SysFont(fonts["info"].name, int(fonts["info"].get_height() * 0.8))
        txt = small_font.render(text, True, WHITE)
    surf.blit(txt, txt.get_rect(center=back_center))

    # 进度文本
    progress_txt = fonts["info"].render(f"{int(back_circle['progress'])}%", True, YELLOW)
    # 位置上移避免遮挡
    progress_rect = progress_txt.get_rect(center=(back_center[0], back_center[1] + r // 2 - 5))
    surf.blit(progress_txt, progress_rect)

    # 触发返回
    if back_circle["progress"] >= PROGRESS_FULL:
        back_circle["progress"] = 0
        progress_sound_played = False
        return True
    return False


def count_hands_in_options(palms):
    """统计选项区域的手数"""
    global option_hand_count
    option_hand_count = {"A": 0, "B": 0, "C": 0}
    areas = get_option_areas()
    for (x, y) in palms:
        for k, (x1, y1, w, h) in areas.items():
            if x1 < x < x1 + w and y1 < y < y1 + h:
                option_hand_count[k] += 1
                break


def draw_answer_interface(surf):
    """绘制答题界面（英文适配核心修复）"""
    fonts = get_fonts()
    w, h = settings["window_size"]
    surf.fill(WHITE)
    q = QUESTIONS[current_question]

    # 标题（多语言）
    title = fonts["title"].render(lang_text[settings["language"]]["quiz_title"], True, BLUE)
    surf.blit(title, title.get_rect(center=(w // 2, int(h * 0.08))))

    # 分数卡片
    score_w = 160
    score_h = 50
    score_x = 25
    score_y = 25
    pygame.draw.rect(surf, (240, 245, 255), (score_x, score_y, score_w, score_h), border_radius=12)
    pygame.draw.rect(surf, BLUE, (score_x, score_y, score_w, score_h), 2, border_radius=12)
    # 分数文本（多语言）
    score_txt = fonts["info"].render(lang_text[settings["language"]]["score"].format(score), True, BLUE)
    surf.blit(score_txt, score_txt.get_rect(center=(score_x + score_w // 2, score_y + score_h // 2)))

    # 倒计时
    max_time = settings["question_time"]
    ratio = left_time / max_time if max_time > 0 else 0
    circle_r = 50
    cx = w - circle_r - 30
    cy = circle_r + 25

    pygame.draw.circle(surf, (240, 245, 255), (cx, cy), circle_r)
    pygame.draw.circle(surf, BLUE, (cx, cy), circle_r, 2)

    angle = 2 * math.pi * ratio
    pygame.draw.arc(surf, RED if left_time <= 5 else BLUE,
                    (cx - circle_r, cy - circle_r, circle_r * 2, circle_r * 2),
                    -math.pi / 2, -math.pi / 2 + angle, 6)

    time_txt = fonts["info"].render(f"{int(left_time)}", True, BLACK)
    surf.blit(time_txt, time_txt.get_rect(center=(cx, cy)))

    # 题目（自动换行优化：适配英文单词）
    question_text = q["question"]
    max_q_w = int(w * 0.8)  # 英文适配：缩小宽度
    q_lines = []

    # 英文单词拆分换行（核心修复）
    if settings["language"] == "eng":
        words = question_text.split()
        current_line = ""
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if fonts["question"].render(test_line, True, BLACK).get_width() > max_q_w:
                q_lines.append(current_line)
                current_line = word
            else:
                current_line = test_line
        if current_line:
            q_lines.append(current_line)
    else:
        # 中文按字符换行
        current_line = ""
        for c in question_text:
            test_line = current_line + c
            if fonts["question"].render(test_line, True, BLACK).get_width() > max_q_w:
                q_lines.append(current_line)
                current_line = c
            else:
                current_line = test_line
        if current_line:
            q_lines.append(current_line)

    # 题目位置上移，避免遮挡
    y_pos = int(h * 0.18)
    line_height = fonts["question"].get_height() + 6
    # 限制最大行数，防止超出屏幕
    max_lines = int((h * 0.4) / line_height)
    display_lines = q_lines[:max_lines]

    for l in display_lines:
        s = fonts["question"].render(l, True, BLACK)
        surf.blit(s, s.get_rect(center=(w // 2, y_pos)))
        y_pos += line_height

    # 选项区域（位置优化）
    option_y_start = int(h * 0.65)  # 英文适配：上移选项区域
    option_height = int(h * 0.20)  # 增加选项高度
    areas = {
        "A": (int(w * 0.1), option_y_start, int(w * 0.25), option_height),
        "B": (int(w * 0.38), option_y_start, int(w * 0.25), option_height),
        "C": (int(w * 0.65), option_y_start, int(w * 0.25), option_height),
    }

    for opt in q["options"]:
        k = opt[0]
        x, y, bw, bh = areas[k]
        pygame.draw.rect(surf, (235, 245, 255), (x, y, bw, bh), border_radius=10)
        pygame.draw.rect(surf, BLUE, (x, y, bw, bh), 3, border_radius=10)

        # 选项文本换行（英文适配）
        opt_text = opt
        opt_w = bw - 20
        opt_lines = []

        if settings["language"] == "eng":
            words = opt_text.split()
            current_line = ""
            for word in words:
                test_line = current_line + " " + word if current_line else word
                if fonts["option"].render(test_line, True, BLACK).get_width() > opt_w:
                    opt_lines.append(current_line)
                    current_line = word
                else:
                    current_line = test_line
            if current_line:
                opt_lines.append(current_line)
        else:
            current_line = ""
            for c in opt_text:
                test_line = current_line + c
                if fonts["option"].render(test_line, True, BLACK).get_width() > opt_w:
                    opt_lines.append(current_line)
                    current_line = c
                else:
                    current_line = test_line
            if current_line:
                opt_lines.append(current_line)

        # 选项文本居中
        lh = fonts["option"].get_height()
        total_h = len(opt_lines) * lh
        # 垂直居中优化
        sy = y + (bh - total_h) // 2
        for ll in opt_lines:
            ts = fonts["option"].render(ll, True, BLACK)
            surf.blit(ts, ts.get_rect(center=(x + bw // 2, sy)))
            sy += lh

        # 人数文本（多语言）
        cnt = fonts["count"].render(lang_text[settings["language"]]["people_count"].format(option_hand_count[k]), True,
                                    ORANGE)
        # 位置优化：左移+上移
        surf.blit(cnt, (x + 12, y + bh - 35))


def draw_result_box(surf, text, ok, pos):
    """绘制结果框（适配英文）"""
    fonts = get_fonts()
    c = GREEN if ok else RED
    bg = (180, 255, 180) if ok else (255, 180, 180)
    t = fonts["result"].render(text, True, c)
    # 适配英文文本宽度
    box_width = max(t.get_width() + 20, 150)
    box_height = t.get_height() + 20
    tr = pygame.Rect(pos[0] - box_width // 2, pos[1] - box_height // 2, box_width, box_height)
    pygame.draw.rect(surf, bg, tr, border_radius=8)
    pygame.draw.rect(surf, c, tr, 2, border_radius=8)
    surf.blit(t, t.get_rect(center=pos))


def draw_summary(surf):
    """绘制总结界面（多语言+布局优化）"""
    global victory_defeat_played
    fonts = get_fonts()
    w, h = settings["window_size"]
    surf.fill(WHITE)

    # 标题（多语言）
    title = fonts["title"].render(lang_text[settings["language"]]["summary_title"], True, BLUE)
    surf.blit(title, title.get_rect(center=(w // 2, int(h * 0.07))))
    save_record()

    # 音效播放
    total_questions = len(QUESTIONS)
    correct_count = score
    if not victory_defeat_played:
        if correct_count == total_questions and SOUND_VICTORY:
            SOUND_VICTORY.play()
        elif correct_count / total_questions < 0.6 and SOUND_DEFEAT:
            SOUND_DEFEAT.play()
        victory_defeat_played = True

    # 答题结果（位置优化）
    y = int(h * 0.18)
    line_spacing = int(h * 0.12)  # 增加行距避免遮挡
    max_y = h * 0.8  # 限制最大高度

    for i in range(min(len(QUESTIONS), int((max_y - y) / line_spacing))):
        ok = answer_history[i][1]
        # 多语言文本
        if settings["language"] == "zh":
            s = lang_text["zh"]["q_num"].format(i + 1, lang_text["zh"]["correct_text"] if ok else lang_text["zh"][
                "wrong_text"])
        else:
            s = lang_text["eng"]["q_num_short"].format(i + 1,
                                                       lang_text["eng"]["correct_text"] if ok else lang_text["eng"][
                                                           "wrong_text"])
        draw_result_box(surf, s, ok, (w // 2, y))
        y += line_spacing

    # 最终得分（多语言）
    final_text = lang_text[settings["language"]]["final_score"].format(score, len(QUESTIONS))
    final = fonts["result"].render(final_text, True, BLUE)
    # 位置优化
    final_pos = (w // 2, min(y + int(h * 0.05), h * 0.9))
    surf.blit(final, final.get_rect(center=final_pos))


def draw_record(surf):
    """绘制记录界面（英文适配）"""
    fonts = get_fonts()
    w, h = settings["window_size"]
    surf.fill(WHITE)

    # 标题（多语言）
    title_text = lang_text[settings["language"]]["summary_title"].replace("Summary", "Records") if settings[
                                                                                                       "language"] == "eng" else \
    lang_text[settings["language"]]["summary_title"].replace("总结", "记录")
    title = fonts["title"].render(title_text, True, BLUE)
    surf.blit(title, title.get_rect(center=(w // 2, int(h * 0.07))))

    # 列名（多语言）
    if settings["language"] == "zh":
        columns = ["时间", "总分", "答题数", "正确率", "错题序号"]
    else:
        columns = ["Time", "Score", "Total", lang_text[settings["language"]]["correct_rate"],
                   lang_text[settings["language"]]["wrong_questions"]]

    # 表格布局优化（适配英文）
    table_x = int(w * 0.05)  # 增加左边距
    table_y = int(h * 0.15)
    table_width = int(w * 0.9)  # 增加表格宽度
    row_height = int(h * 0.08)  # 增加行高
    col_widths = [
        int(table_width * 0.28),  # 时间列加宽
        int(table_width * 0.12),
        int(table_width * 0.12),
        int(table_width * 0.18),  # 正确率列加宽
        int(table_width * 0.30)
    ]

    try:
        if os.path.exists(RECORD_FILE):
            with open(RECORD_FILE, "r", encoding="utf-8") as file:
                reader = csv.reader(file)
                header = next(reader)
                records = list(reader)

                if not records:
                    no_record_text = lang_text[settings["language"]]["no_record"]
                    no_record = fonts["info"].render(no_record_text, True, BLACK)
                    surf.blit(no_record, no_record.get_rect(center=(w // 2, h // 2)))
                    return

                # 绘制表头
                current_x = table_x
                pygame.draw.rect(surf, BLUE, (table_x, table_y, table_width, row_height))
                for i, col_name in enumerate(columns):
                    # 表头字体适配
                    header_font = pygame.font.SysFont(fonts["info"].name, int(fonts["info"].get_height() * 0.9))
                    txt = header_font.render(col_name, True, WHITE)
                    # 文本居中
                    txt_rect = txt.get_rect(center=(current_x + col_widths[i] // 2, table_y + row_height // 2))
                    surf.blit(txt, txt_rect)
                    current_x += col_widths[i]

                # 绘制数据行（最多6行，避免超出屏幕）
                display_records = records[-6:]
                for row_idx, row in enumerate(display_records):
                    while len(row) < 5:
                        row.append("")

                    row_y = table_y + (row_idx + 1) * row_height
                    if row_idx % 2 == 0:
                        pygame.draw.rect(surf, LIGHT_BLUE, (table_x, row_y, table_width, row_height))

                    current_x = table_x
                    for col_idx, cell_data in enumerate(row[:5]):
                        # 文本长度限制
                        if len(cell_data) > 18:
                            cell_data = cell_data[:15] + "..."

                        # 适配英文字体大小
                        cell_font = fonts["mini"]
                        if settings["language"] == "eng" and col_idx == 0:
                            cell_font = pygame.font.SysFont(fonts["mini"].name, int(fonts["mini"].get_height() * 0.85))

                        txt = cell_font.render(cell_data, True, BLACK)
                        txt_rect = txt.get_rect(center=(current_x + col_widths[col_idx] // 2, row_y + row_height // 2))
                        surf.blit(txt, txt_rect)
                        current_x += col_widths[col_idx]

                    # 行分隔线
                    pygame.draw.line(surf, (200, 200, 200), (table_x, row_y + row_height),
                                     (table_x + table_width, row_y + row_height), 1)

                # 表格边框
                pygame.draw.rect(surf, BLACK, (table_x, table_y, table_width, row_height * (len(display_records) + 1)),
                                 2)

                # 列分隔线
                current_x = table_x
                for col_width in col_widths[:-1]:
                    current_x += col_width
                    pygame.draw.line(surf, (200, 200, 200), (current_x, table_y),
                                     (current_x, table_y + row_height * (len(display_records) + 1)), 1)

    except Exception as e:
        error_text = lang_text[settings["language"]]["load_record_error"].format(str(e))
        error_txt = fonts["info"].render(error_text, True, RED)
        surf.blit(error_txt, error_txt.get_rect(center=(w // 2, h // 2)))


def save_record():
    """保存答题记录"""
    try:
        total = len(QUESTIONS)
        correct = score
        acc = f"{(correct / total) * 100:.1f}%" if total > 0 else "0.0%"
        wrong = [str(i + 1) for i, (idx, ok) in enumerate(answer_history) if not ok]
        wrong_str = ",".join(wrong) if wrong else "无" if settings["language"] == "zh" else "None"
        row = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), str(correct), str(total), acc, wrong_str]
        with open(RECORD_FILE, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(row)
    except Exception as e:
        print(f"Save record failed: {e}")


# 设置界面进度
setting_progress = {
    "window_small": 0, "window_mid": 0, "window_full": 0,
    "color_blue": 0, "color_green": 0, "color_red": 0,
    "lang_zh": 0, "lang_eng": 0
}


def draw_setting_interface(surf, palms, delta_time):
    """绘制设置界面（多语言+布局优化）"""
    global progress_sound_played
    fonts = get_fonts()
    w, h = settings["window_size"]
    surf.fill(WHITE)

    # 标题（多语言）
    title = fonts["title"].render(lang_text[settings["language"]]["setting_title"], True, BLUE)
    surf.blit(title, title.get_rect(center=(w // 2, int(h * 0.07))))

    # 布局优化：增加间距，适配英文
    r = 40  # 缩小按钮半径
    spacing = 110  # 减小按钮间距
    start_x = int(w * 0.25)  # 右移起始位置

    # 窗口设置
    y1 = int(h * 0.22)
    # 标签（多语言）
    lbl = fonts["info"].render(lang_text[settings["language"]]["window_label"], True, BLACK)
    surf.blit(lbl, (int(w * 0.12), y1 - r - 10))

    # 窗口大小按钮（多语言）
    c1 = (start_x, y1)
    c2 = (start_x + spacing, y1)
    c3 = (start_x + spacing * 2, y1)

    sel_win_small = (settings["window_mode"] == "小屏")
    touched = any(is_in_circle(p, c1, r) for p in palms)
    if touched:
        setting_progress["window_small"] = min(PROGRESS_FULL, setting_progress["window_small"] + settings[
            "progress_speed"] * delta_time)
        if setting_progress["window_small"] >= 50 and not progress_sound_played and SOUND_PROGRESS:
            SOUND_PROGRESS.play()
            progress_sound_played = True
        if setting_progress["window_small"] >= PROGRESS_FULL:
            settings["window_mode"] = "小屏"
            settings["window_size"] = (800, 600)
            global screen
            screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
            for k in setting_progress: setting_progress[k] = 0
            progress_sound_played = False
    else:
        setting_progress["window_small"] = max(0, setting_progress["window_small"] - PROGRESS_DECAY * delta_time)
        progress_sound_played = False
    # 多语言按钮文本
    draw_circle_option(screen, c1, r, lang_text[settings["language"]]["small_window"], setting_progress["window_small"],
                       sel_win_small)

    sel_win_mid = (settings["window_mode"] == "中屏")
    touched = any(is_in_circle(p, c2, r) for p in palms)
    if touched:
        setting_progress["window_mid"] = min(PROGRESS_FULL,
                                             setting_progress["window_mid"] + settings["progress_speed"] * delta_time)
        if setting_progress["window_mid"] >= 50 and not progress_sound_played and SOUND_PROGRESS:
            SOUND_PROGRESS.play()
            progress_sound_played = True
        if setting_progress["window_mid"] >= PROGRESS_FULL:
            settings["window_mode"] = "中屏"
            settings["window_size"] = (1024, 768)
            screen = pygame.display.set_mode((1024, 768), pygame.RESIZABLE)
            for k in setting_progress: setting_progress[k] = 0
            progress_sound_played = False
    else:
        setting_progress["window_mid"] = max(0, setting_progress["window_mid"] - PROGRESS_DECAY * delta_time)
        progress_sound_played = False
    draw_circle_option(screen, c2, r, lang_text[settings["language"]]["mid_window"], setting_progress["window_mid"],
                       sel_win_mid)

    sel_win_full = (settings["window_mode"] == "全屏")
    touched = any(is_in_circle(p, c3, r) for p in palms)
    if touched:
        setting_progress["window_full"] = min(PROGRESS_FULL,
                                              setting_progress["window_full"] + settings["progress_speed"] * delta_time)
        if setting_progress["window_full"] >= 50 and not progress_sound_played and SOUND_PROGRESS:
            SOUND_PROGRESS.play()
            progress_sound_played = True
        if setting_progress["window_full"] >= PROGRESS_FULL:
            settings["window_mode"] = "全屏"
            sw, sh = pygame.display.Info().current_w, pygame.display.Info().current_h
            settings["window_size"] = (sw, sh)
            screen = pygame.display.set_mode((sw, sh), pygame.FULLSCREEN)
            for k in setting_progress: setting_progress[k] = 0
            progress_sound_played = False
    else:
        setting_progress["window_full"] = max(0, setting_progress["window_full"] - PROGRESS_DECAY * delta_time)
        progress_sound_played = False
    draw_circle_option(screen, c3, r, lang_text[settings["language"]]["full_window"], setting_progress["window_full"],
                       sel_win_full)

    # 颜色设置
    y2 = y1 + 140  # 增加间距
    lbl = fonts["info"].render(lang_text[settings["language"]]["color_label"], True, BLACK)
    surf.blit(lbl, (int(w * 0.12), y2 - r - 10))
    c4 = (start_x, y2)
    c5 = (start_x + spacing, y2)
    c6 = (start_x + spacing * 2, y2)

    sel_blue = (settings["hand_color_name"] == "蓝")
    touched = any(is_in_circle(p, c4, r) for p in palms)
    if touched:
        setting_progress["color_blue"] = min(PROGRESS_FULL,
                                             setting_progress["color_blue"] + settings["progress_speed"] * delta_time)
        if setting_progress["color_blue"] >= 50 and not progress_sound_played and SOUND_PROGRESS:
            SOUND_PROGRESS.play()
            progress_sound_played = True
        if setting_progress["color_blue"] >= PROGRESS_FULL:
            settings["hand_color"] = BLUE
            settings["hand_color_name"] = "蓝"
            for k in setting_progress: setting_progress[k] = 0
            progress_sound_played = False
    else:
        setting_progress["color_blue"] = max(0, setting_progress["color_blue"] - PROGRESS_DECAY * delta_time)
        progress_sound_played = False
    draw_circle_option(screen, c4, r, lang_text[settings["language"]]["blue_color"], setting_progress["color_blue"],
                       sel_blue, BLUE)

    sel_green = (settings["hand_color_name"] == "绿")
    touched = any(is_in_circle(p, c5, r) for p in palms)
    if touched:
        setting_progress["color_green"] = min(PROGRESS_FULL,
                                              setting_progress["color_green"] + settings["progress_speed"] * delta_time)
        if setting_progress["color_green"] >= 50 and not progress_sound_played and SOUND_PROGRESS:
            SOUND_PROGRESS.play()
            progress_sound_played = True
        if setting_progress["color_green"] >= PROGRESS_FULL:
            settings["hand_color"] = GREEN
            settings["hand_color_name"] = "绿"
            for k in setting_progress: setting_progress[k] = 0
            progress_sound_played = False
    else:
        setting_progress["color_green"] = max(0, setting_progress["color_green"] - PROGRESS_DECAY * delta_time)
        progress_sound_played = False
    draw_circle_option(screen, c5, r, lang_text[settings["language"]]["green_color"], setting_progress["color_green"],
                       sel_green, GREEN)

    sel_red = (settings["hand_color_name"] == "红")
    touched = any(is_in_circle(p, c6, r) for p in palms)
    if touched:
        setting_progress["color_red"] = min(PROGRESS_FULL,
                                            setting_progress["color_red"] + settings["progress_speed"] * delta_time)
        if setting_progress["color_red"] >= 50 and not progress_sound_played and SOUND_PROGRESS:
            SOUND_PROGRESS.play()
            progress_sound_played = True
        if setting_progress["color_red"] >= PROGRESS_FULL:
            settings["hand_color"] = RED
            settings["hand_color_name"] = "红"
            for k in setting_progress: setting_progress[k] = 0
            progress_sound_played = False
    else:
        setting_progress["color_red"] = max(0, setting_progress["color_red"] - PROGRESS_DECAY * delta_time)
        progress_sound_played = False
    draw_circle_option(screen, c6, r, lang_text[settings["language"]]["red_color"], setting_progress["color_red"],
                       sel_red, RED)

    # 语言设置
    y3 = y2 + 140  # 增加间距
    lbl = fonts["info"].render(lang_text[settings["language"]]["lang_label"], True, BLACK)
    surf.blit(lbl, (int(w * 0.12), y3 - r - 10))
    c7 = (start_x + spacing // 2, y3)  # 居中显示
    c8 = (start_x + spacing * 1.5, y3)

    sel_zh = (settings["language"] == "zh")
    touched = any(is_in_circle(p, c7, r) for p in palms)
    if touched:
        setting_progress["lang_zh"] = min(PROGRESS_FULL,
                                          setting_progress["lang_zh"] + settings["progress_speed"] * delta_time)
        if setting_progress["lang_zh"] >= 50 and not progress_sound_played and SOUND_PROGRESS:
            SOUND_PROGRESS.play()
            progress_sound_played = True
        if setting_progress["lang_zh"] >= PROGRESS_FULL:
            settings["language"] = "zh"
            global QUESTIONS
            QUESTIONS = QUESTIONS_ZH
            random.shuffle(QUESTIONS)
            # 更新窗口标题
            pygame.display.set_caption(lang_text["zh"]["window_title"])
            for k in setting_progress: setting_progress[k] = 0
            progress_sound_played = False
    else:
        setting_progress["lang_zh"] = max(0, setting_progress["lang_zh"] - PROGRESS_DECAY * delta_time)
        progress_sound_played = False
    draw_circle_option(screen, c7, r, lang_text[settings["language"]]["chinese_lang"], setting_progress["lang_zh"],
                       sel_zh)

    sel_eng = (settings["language"] == "eng")
    touched = any(is_in_circle(p, c8, r) for p in palms)
    if touched:
        setting_progress["lang_eng"] = min(PROGRESS_FULL,
                                           setting_progress["lang_eng"] + settings["progress_speed"] * delta_time)
        if setting_progress["lang_eng"] >= 50 and not progress_sound_played and SOUND_PROGRESS:
            SOUND_PROGRESS.play()
            progress_sound_played = True
        if setting_progress["lang_eng"] >= PROGRESS_FULL:
            settings["language"] = "eng"
            QUESTIONS = QUESTIONS_ENG
            random.shuffle(QUESTIONS)
            # 更新窗口标题
            pygame.display.set_caption(lang_text["eng"]["window_title"])
            for k in setting_progress: setting_progress[k] = 0
            progress_sound_played = False
    else:
        setting_progress["lang_eng"] = max(0, setting_progress["lang_eng"] - PROGRESS_DECAY * delta_time)
        progress_sound_played = False
    draw_circle_option(screen, c8, r, lang_text[settings["language"]]["english_lang"], setting_progress["lang_eng"],
                       sel_eng)


# 主循环
running = True
all_palms = []
last_time = time.time()

while running:
    now = time.time()
    delta = now - last_time
    last_time = now

    # 摄像头读取
    ret, frame = cap.read()
    if not ret:
        frame = None
        print("Warning: Cannot read camera frame")

    # 事件处理
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            if settings["window_mode"] == "全屏":
                settings["window_mode"] = "中屏"
                settings["window_size"] = (1024, 768)
                screen = pygame.display.set_mode((1024, 768), pygame.RESIZABLE)

    screen.fill(WHITE)
    all_palms = []

    # 手部检测
    if frame is not None:
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = hands.process(rgb)

        if res.multi_hand_landmarks:
            for lm in res.multi_hand_landmarks:
                all_palms.append(get_palm_center(lm))

    # 状态机
    if current_state == STATE_START:
        victory_defeat_played = False
        fonts = get_fonts()
        w, h = settings["window_size"]
        # 标题（多语言）
        nte = fonts["big"].render(lang_text[settings["language"]]["window_title"], True, BLUE)
        # 标题适配：缩小字体避免超出
        if nte.get_width() > w * 0.8:
            big_font = pygame.font.SysFont(fonts["big"].name, int(fonts["big"].get_height() * 0.8))
            nte = big_font.render(lang_text[settings["language"]]["window_title"], True, BLUE)
        # 修复：将 surf 改为 screen
        screen.blit(nte, nte.get_rect(center=(w // 2, int(h * 0.33))))

        # 功能按钮位置优化
        start_circle["pos"] = (int(w * 0.25), int(h * 0.67))
        record_circle["pos"] = (int(w * 0.5), int(h * 0.67))
        setting_circle["pos"] = (int(w * 0.75), int(h * 0.67))

        # 绘制功能按钮（多语言）
        btn_texts = [
            lang_text[settings["language"]]["start_btn"],
            lang_text[settings["language"]]["record_btn"],
            lang_text[settings["language"]]["setting_btn"]
        ]

        for i, c in enumerate(function_circles):
            touched = any(is_in_circle(p, c["pos"], c["radius"] * settings["font_scale"]) for p in all_palms)
            if touched:
                c["progress"] = min(PROGRESS_FULL, c["progress"] + settings["progress_speed"] * delta)
            else:
                c["progress"] = max(0, c["progress"] - PROGRESS_DECAY * delta)

            draw_circle_option(screen, c["pos"], int(c["radius"] * settings["font_scale"]),
                               btn_texts[i], c["progress"], False)

            if c["progress"] >= PROGRESS_FULL:
                if i == 0:  # 开始
                    current_state = STATE_ANSWER
                    start_time = now
                    left_time = settings["question_time"]
                elif i == 1:  # 记录
                    current_state = STATE_RECORD
                elif i == 2:  # 设置
                    current_state = STATE_SETTING
                for cc in function_circles: cc["progress"] = 0
                progress_sound_played = False

    elif current_state == STATE_ANSWER:
        count_hands_in_options(all_palms)
        if not show_result:
            if start_time == 0: start_time = now
            left_time = max(0, settings["question_time"] - (now - start_time))
            if left_time <= 0:
                current_is_correct = False
                result_text = lang_text[settings["language"]]["time_up_wrong"]
                answer_history.append((current_question, False))
                show_result = True
                result_show_time = now
                start_time = 0
                if SOUND_TIME_OUT:
                    SOUND_TIME_OUT.play()
            sel = None
            if all_palms:
                main = all_palms[0]
                areas = get_option_areas()
                for k in ["A", "B", "C"]:
                    x1, y1, w_opt, h_opt = areas[k]
                    if x1 < main[0] < x1 + w_opt and y1 < main[1] < y1 + h_opt:
                        sel = k
                        break
            if sel:
                if sel not in hand_stay_time:
                    hand_stay_time[sel] = now
                else:
                    if now - hand_stay_time[sel] >= STAY_CONFIRM_TIME:
                        ans = QUESTIONS[current_question]["answer"]
                        current_is_correct = (sel == ans)
                        if current_is_correct:
                            score += 1
                            result_text = lang_text[settings["language"]]["correct"]
                            w, h = settings["window_size"]
                            for _ in range(6):
                                fireworks.append(Firework(random.randint(100, w - 100), random.randint(50, h - 50)))
                            if SOUND_CORRECT:
                                SOUND_CORRECT.play()
                        else:
                            result_text = lang_text[settings["language"]]["wrong"]
                            if SOUND_WRONG:
                                SOUND_WRONG.play()
                        answer_history.append((current_question, current_is_correct))
                        show_result = True
                        result_show_time = now
                        start_time = 0
                        hand_stay_time.clear()
            else:
                hand_stay_time.clear()
        draw_answer_interface(screen)
        if show_result:
            w, h = settings["window_size"]
            draw_result_box(screen, result_text, current_is_correct, (w // 2, int(h * 0.4)))
            if now - result_show_time > 2.5:
                show_result = False
                current_question += 1
                if current_question >= len(QUESTIONS):
                    current_state = STATE_SUMMARY
                else:
                    start_time = 0
                    left_time = settings["question_time"]
                    hand_stay_time.clear()
        # 烟花特效
        for fw in fireworks[:]:
            fw.update()
            fw.draw(screen)
            if not fw.particles: fireworks.remove(fw)

    elif current_state == STATE_SUMMARY:
        draw_summary(screen)
        if now - result_show_time > 10:
            current_state = STATE_START
            current_question = 0
            score = 0
            answer_history = []
            show_result = False
            victory_defeat_played = False

    elif current_state == STATE_RECORD:
        draw_record(screen)
        if draw_back_circle(screen, delta, all_palms):
            current_state = STATE_START
            progress_sound_played = False

    elif current_state == STATE_SETTING:
        draw_setting_interface(screen, all_palms, delta)
        if draw_back_circle(screen, delta, all_palms):
            current_state = STATE_START
            progress_sound_played = False

    # 绘制手掌中心
    for p in all_palms:
        draw_palm_center(screen, p)

    pygame.display.update()
    clock.tick(120)

# 资源释放
cap.release()
pygame.quit()