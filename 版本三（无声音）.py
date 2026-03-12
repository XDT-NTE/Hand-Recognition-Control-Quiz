import cv2
import mediapipe as mp
import pygame
import time
import random
import math
import csv
import os
from datetime import datetime

# ---------------------- 初始化全局参数 ----------------------
pygame.init()
# 设置字体（提前初始化避免加载时出错）
pygame.font.init()

# 加载界面相关参数
loading_screen = True
loading_angle = 0
loading_radius = 30
loading_center = (400, 300)
loading_color = (0, 80, 200)  # 蓝色
loading_thickness = 5

# 创建初始窗口
screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
pygame.display.set_caption("NTE 体测答题系统")
clock = pygame.time.Clock()

# 启用高清渲染（抗锯齿）
pygame.display.set_mode((800, 600), pygame.RESIZABLE | pygame.HWSURFACE)
# 获取真实屏幕分辨率
desktop_w, desktop_h = pygame.display.Info().current_w, pygame.display.Info().current_h

WINDOW_WIDTH, WINDOW_HEIGHT = 800, 600

# 全局设置
settings = {
    "window_mode": "中屏",
    "window_size": (800, 600),
    "hand_color": (0, 255, 0),
    "hand_color_name": "绿",
    "language": "zh",
    "font_scale": 1.0,
    "progress_speed": 33,  # 3秒填满进度条
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

# 状态
STATE_START = 0
STATE_ANSWER = 1
STATE_SUMMARY = 2
STATE_RECORD = 3
STATE_SETTING = 4
current_state = STATE_START

# 启动界面功能圆
start_circle = {"pos": (200, 400), "radius": 60, "name": "开始", "progress": 0}
record_circle = {"pos": (400, 400), "radius": 60, "name": "记录", "progress": 0}
setting_circle = {"pos": (600, 400), "radius": 60, "name": "设置", "progress": 0}
function_circles = [start_circle, record_circle, setting_circle]

# 返回圆（独立，右下角）
back_circle = {
    "radius": 50,
    "progress": 0,
    "name_zh": "返回",
    "name_eng": "Back"
}

PROGRESS_FULL = 100
PROGRESS_DECAY = 50

# 手部检测
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=4,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)


# 显示加载界面
def draw_loading_screen():
    global loading_angle

    # 填充白色背景
    screen.fill(WHITE)

    # 获取字体
    try:
        # 尝试加载系统字体
        font = pygame.font.SysFont(["Microsoft YaHei", "SimHei", "Arial"], 24)
        small_font = pygame.font.SysFont(["Microsoft YaHei", "SimHei", "Arial"], 18)
    except:
        # 备用默认字体
        font = pygame.font.Font(None, 24)
        small_font = pygame.font.Font(None, 18)

    # 绘制加载文字
    loading_text = font.render("系统加载中...", True, BLUE)
    text_rect = loading_text.get_rect(center=(loading_center[0], loading_center[1] + 50))
    screen.blit(loading_text, text_rect)

    # 绘制版权/提示文字
    hint_text = small_font.render("NTE 体测答题系统 v1.0", True, BLACK)
    hint_rect = hint_text.get_rect(center=(loading_center[0], 550))
    screen.blit(hint_text, hint_rect)

    # 计算加载圆弧的起始和结束角度
    start_angle = loading_angle
    end_angle = loading_angle + 270  # 270度的圆弧
    loading_angle = (loading_angle + 5) % 360  # 旋转速度

    # 绘制加载圆弧
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

    # 更新显示
    pygame.display.update()


# 显示加载界面直到初始化完成
start_time = time.time()
while loading_screen:
    # 控制加载界面显示至少1.5秒，避免闪一下就消失
    if time.time() - start_time > 1.5:
        loading_screen = False

    # 处理退出事件
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

    # 绘制加载界面
    draw_loading_screen()
    clock.tick(60)


# 烟花
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

# 题库
QUESTIONS_ZH = [
    {"question": "小学1分钟跳绳体测，四年级优秀标准约是多少个？", "options": ["A.100个", "B.130个", "C.80个"],
     "answer": "B"},
    {"question": "50米跑前，我们需要做什么准备？", "options": ["A.直接跑", "B.热身运动", "C.喝水"], "answer": "B"},
    {"question": "坐位体前屈测试时，身体应该？", "options": ["A.弯腰前倾", "B.挺直腰杆", "C.后仰"], "answer": "A"},
    {"question": "跑步时不小心摔倒，第一时间要？", "options": ["A.立刻爬起来", "B.检查伤口", "C.大哭"], "answer": "B"},
    {"question": "仰卧起坐1分钟，四年级合格标准约是多少个？", "options": ["A.20个", "B.10个", "C.35个"], "answer": "A"}
]
QUESTIONS_ENG = [
    {"question": "What is the excellent standard of 1-minute rope skipping for 4th grade?",
     "options": ["A.100", "B.130", "C.80"], "answer": "B"},
    {"question": "What preparation should we do before 50m run?",
     "options": ["A.Run directly", "B.Warm-up", "C.Drink water"], "answer": "B"},
    {"question": "What should you do during sit-and-reach test?",
     "options": ["A.Bend forward", "B.Keep straight", "C.Lean back"], "answer": "A"},
    {"question": "What to do first if you fall while running?",
     "options": ["A.Stand up immediately", "B.Check wounds", "C.Cry"], "answer": "B"},
    {"question": "What is the passing standard of sit-ups for 4th grade (1min)?", "options": ["A.20", "B.10", "C.35"],
     "answer": "A"}
]
QUESTIONS = QUESTIONS_ZH if settings["language"] == "zh" else QUESTIONS_ENG
random.shuffle(QUESTIONS)

current_question = 0
score = 0
start_time = 0
left_time = settings["question_time"]


# 选项区域（扩大选项框高度，避免文字超出）
def get_option_areas():
    w, h = settings["window_size"]
    return {
        "A": (int(w * 0.1), int(h * 0.70), int(w * 0.25), int(h * 0.18)),
        "B": (int(w * 0.38), int(h * 0.70), int(w * 0.25), int(h * 0.18)),
        "C": (int(w * 0.65), int(h * 0.70), int(w * 0.25), int(h * 0.18)),
    }


option_areas = get_option_areas()

hand_stay_time = {}
STAY_CONFIRM_TIME = 3
option_hand_count = {"A": 0, "B": 0, "C": 0}
answer_history = []
show_result = False
result_text = ""
result_show_time = 0
current_is_correct = False

# 记录
RECORD_FILE = "nte_answer_records.csv"
if not os.path.exists(RECORD_FILE):
    with open(RECORD_FILE, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(["时间", "总分", "答题数", "正确率", "错题序号"])


# ---------------------- 工具函数 ----------------------
def get_font_sizes():
    scale = settings["font_scale"]
    return {
        "big": int(60 * scale), "title": int(40 * scale), "question": int(28 * scale),  # 题目字体从32→28
        "option": int(24 * scale),  # 选项字体从30→24（核心修改：缩小字体避免超出）
        "info": int(26 * scale), "count": int(24 * scale), "result": int(36 * scale)
    }


# 字体适配所有分辨率，避免英文方框
def get_fonts():
    sizes = get_font_sizes()
    # 优先使用系统通用字体，同时支持中英文
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
        "mini": pygame.font.SysFont(font_name, int(22 * settings["font_scale"]))  # 新增小字体用于记录
    }


def get_palm_center(landmarks):
    x = sum(landmarks.landmark[i].x for i in [0, 5, 9, 13, 17]) / 5
    y = sum(landmarks.landmark[i].y for i in [0, 5, 9, 13, 17]) / 5
    w, h = settings["window_size"]
    return int(x * w), int(y * h)


def draw_palm_center(surf, center):
    x, y = center
    r = int(18 * settings["font_scale"])
    pygame.draw.circle(surf, WHITE, (x, y), r)
    pygame.draw.circle(surf, settings["hand_color"], (x, y), r - 2)


def is_in_circle(pt, center, r):
    dx = pt[0] - center[0]
    dy = pt[1] - center[1]
    return math.hypot(dx, dy) <= r


# 绘制圆形进度按钮
def draw_circle_option(surf, center, r, text, progress, is_selected, color=BLUE):
    pygame.draw.circle(surf, LIGHT_BLUE, center, r)
    if is_selected:
        pygame.draw.circle(surf, SELECTED_BORDER, center, r + 4, 4)
    pygame.draw.circle(surf, color, center, r, 2)
    if progress > 0:
        angle = 2 * math.pi * (progress / PROGRESS_FULL)
        pygame.draw.arc(surf, YELLOW,
                        (center[0] - r - 5, center[1] - r - 5, (r + 5) * 2, (r + 5) * 2),
                        -math.pi / 2, -math.pi / 2 + angle, 4)
    fonts = get_fonts()["info"]
    txt = fonts.render(text, True, BLACK)
    surf.blit(txt, txt.get_rect(center=center))


# 绘制右下角返回圆
def draw_back_circle(surf, delta_time, palms):
    fonts = get_fonts()
    w, h = settings["window_size"]
    back_center = (w - back_circle["radius"] - 30, h - back_circle["radius"] - 30)
    r = back_circle["radius"]

    touched = any(is_in_circle(p, back_center, r) for p in palms)
    if touched:
        back_circle["progress"] = min(PROGRESS_FULL, back_circle["progress"] + settings["progress_speed"] * delta_time)
    else:
        back_circle["progress"] = max(0, back_circle["progress"] - PROGRESS_DECAY * delta_time)

    pygame.draw.circle(surf, BACK_CIRCLE_COLOR, back_center, r)
    pygame.draw.circle(surf, WHITE, back_center, r, 3)
    if back_circle["progress"] > 0:
        angle = 2 * math.pi * (back_circle["progress"] / PROGRESS_FULL)
        pygame.draw.arc(surf, YELLOW,
                        (back_center[0] - r - 5, back_center[1] - r - 5, (r + 5) * 2, (r + 5) * 2),
                        -math.pi / 2, -math.pi / 2 + angle, 5)
    text = back_circle["name_zh"] if settings["language"] == "zh" else back_circle["name_eng"]
    txt = fonts["info"].render(text, True, WHITE)
    surf.blit(txt, txt.get_rect(center=back_center))

    progress_txt = fonts["info"].render(f"{int(back_circle['progress'])}%", True, YELLOW)
    surf.blit(progress_txt, progress_txt.get_rect(center=(back_center[0], back_center[1] + r // 2)))

    if back_circle["progress"] >= PROGRESS_FULL:
        back_circle["progress"] = 0
        return True
    return False


def count_hands_in_options(palms):
    global option_hand_count
    option_hand_count = {"A": 0, "B": 0, "C": 0}
    areas = get_option_areas()
    for (x, y) in palms:
        for k, (x1, y1, w, h) in areas.items():
            if x1 < x < x1 + w and y1 < y < y1 + h:
                option_hand_count[k] += 1
                break


# 核心修改：重写draw_answer_interface，支持文字自动换行+居中
def draw_answer_interface(surf):
    fonts = get_fonts()
    w, h = settings["window_size"]
    surf.fill(WHITE)
    q = QUESTIONS[current_question]

    # ====================== 标题 ======================
    title = fonts["title"].render("NTE 体测答题", True, BLUE)
    surf.blit(title, title.get_rect(center=(w//2, int(h*0.08))))

    # ====================== 左上角：分数卡片（好看版） ======================
    score_w = 160
    score_h = 50
    score_x = 25
    score_y = 25
    pygame.draw.rect(surf, (240,245,255), (score_x, score_y, score_w, score_h), border_radius=12)
    pygame.draw.rect(surf, BLUE, (score_x, score_y, score_w, score_h), 2, border_radius=12)
    score_txt = fonts["info"].render(f"分数：{score}", True, BLUE)
    surf.blit(score_txt, score_txt.get_rect(center=(score_x + score_w//2, score_y + score_h//2)))

    # ====================== 右上角：圆形倒计时圈 ======================
    max_time = settings["question_time"]
    ratio = left_time / max_time if max_time > 0 else 0
    circle_r = 50
    cx = w - circle_r - 30
    cy = circle_r + 25

    # 外圈
    pygame.draw.circle(surf, (240,245,255), (cx, cy), circle_r)
    pygame.draw.circle(surf, BLUE, (cx, cy), circle_r, 2)

    # 倒计时圆弧
    angle = 2 * math.pi * ratio
    pygame.draw.arc(surf, RED if left_time <= 5 else BLUE,
                    (cx - circle_r, cy - circle_r, circle_r*2, circle_r*2),
                    -math.pi/2, -math.pi/2 + angle, 6)

    # 中间数字
    time_txt = fonts["info"].render(f"{int(left_time)}", True, BLACK)
    surf.blit(time_txt, time_txt.get_rect(center=(cx, cy)))

    # ====================== 题目（自动换行） ======================
    question_text = q["question"]
    max_q_w = int(w * 0.85)
    q_lines = []
    line = ""
    for c in question_text:
        test = line + c
        if fonts["question"].render(test, True, BLACK).get_width() > max_q_w:
            q_lines.append(line)
            line = c
        else:
            line = test
    if line:
        q_lines.append(line)

    y_pos = int(h * 0.22)
    for l in q_lines:
        s = fonts["question"].render(l, True, BLACK)
        surf.blit(s, s.get_rect(center=(w//2, y_pos)))
        y_pos += s.get_height() + 6

    # ====================== 选项框 ======================
    areas = get_option_areas()
    for opt in q["options"]:
        k = opt[0]
        x, y, bw, bh = areas[k]
        pygame.draw.rect(surf, (235,245,255), (x, y, bw, bh), border_radius=10)
        pygame.draw.rect(surf, BLUE, (x, y, bw, bh), 3, border_radius=10)

        # 选项文字自动换行 + 居中
        opt_w = bw - 20
        opt_lines = []
        ol = ""
        for c in opt:
            test = ol + c
            if fonts["option"].render(test, True, BLACK).get_width() > opt_w:
                opt_lines.append(ol)
                ol = c
            else:
                ol = test
        if ol:
            opt_lines.append(ol)

        lh = fonts["option"].get_height()
        total_h = len(opt_lines) * lh
        sy = y + (bh - total_h) // 2
        for ll in opt_lines:
            ts = fonts["option"].render(ll, True, BLACK)
            surf.blit(ts, ts.get_rect(center=(x + bw//2, sy)))
            sy += lh

        # 人数
        cnt = fonts["count"].render(f"人数：{option_hand_count[k]}", True, ORANGE)
        surf.blit(cnt, (x + 12, y + bh - 32))

def draw_result_box(surf, text, ok, pos):
    fonts = get_fonts()
    c = GREEN if ok else RED
    bg = (180, 255, 180) if ok else (255, 180, 180)
    t = fonts["result"].render(text, True, c)
    tr = t.get_rect(center=pos)
    pygame.draw.rect(surf, bg, (tr.x - 10, tr.y - 10, tr.width + 20, tr.height + 20), border_radius=8)
    pygame.draw.rect(surf, c, (tr.x - 10, tr.y - 10, tr.width + 20, tr.height + 20), 2, border_radius=8)
    surf.blit(t, tr)


def draw_summary(surf):
    fonts = get_fonts()
    w, h = settings["window_size"]
    surf.fill(WHITE)
    title = fonts["title"].render("答题总结" if settings["language"] == "zh" else "Quiz Summary", True, BLUE)
    surf.blit(title, title.get_rect(center=(w // 2, int(h * 0.07))))
    save_record()
    y = int(h * 0.2)
    for i in range(len(QUESTIONS)):
        ok = answer_history[i][1]
        s = f"第{i + 1}题：{'正确' if ok else '错误'}" if settings[
                                                             "language"] == "zh" else f"Q{i + 1}: {'Correct' if ok else 'Wrong'}"
        draw_result_box(surf, s, ok, (w // 2, y))
        y += int(h * 0.13)
    final = fonts["result"].render(f"最终得分：{score}/{len(QUESTIONS)}" if settings[
                                                                               "language"] == "zh" else f"Final Score: {score}/{len(QUESTIONS)}",
                                   True, BLUE)
    surf.blit(final, final.get_rect(center=(w // 2, y + int(h * 0.05))))


# ---------------------- 重点优化：记录界面 ----------------------
def draw_record(surf):
    fonts = get_fonts()
    w, h = settings["window_size"]
    surf.fill(WHITE)

    # 标题
    title_text = "答题记录" if settings["language"] == "zh" else "Answer Records"
    title = fonts["title"].render(title_text, True, BLUE)
    surf.blit(title, title.get_rect(center=(w // 2, int(h * 0.07))))

    # 定义列宽和列名（中英文适配）
    if settings["language"] == "zh":
        columns = ["时间", "总分", "答题数", "正确率", "错题序号"]
    else:
        columns = ["Time", "Score", "Total", "Accuracy", "Wrong Qs"]

    # 计算表格区域（居中，留边距）
    table_x = int(w * 0.08)  # 左间距8%
    table_y = int(h * 0.15)  # 上间距15%
    table_width = int(w * 0.84)  # 表格宽度84%
    row_height = int(h * 0.07)  # 行高7%
    col_widths = [
        int(table_width * 0.25),  # 时间列 25%
        int(table_width * 0.15),  # 总分列 15%
        int(table_width * 0.15),  # 答题数列 15%
        int(table_width * 0.15),  # 正确率列 15%
        int(table_width * 0.30)  # 错题序号列 30%
    ]

    try:
        if os.path.exists(RECORD_FILE):
            with open(RECORD_FILE, "r", encoding="utf-8") as file:
                reader = csv.reader(file)
                header = next(reader)  # 读取表头
                records = list(reader)  # 读取数据行

                # 无记录时显示提示
                if not records:
                    no_record_text = "暂无答题记录" if settings["language"] == "zh" else "No records yet"
                    no_record = fonts["info"].render(no_record_text, True, BLACK)
                    surf.blit(no_record, no_record.get_rect(center=(w // 2, h // 2)))
                    return

                # 绘制表头行（带背景色）
                current_x = table_x
                pygame.draw.rect(surf, BLUE, (table_x, table_y, table_width, row_height))
                for i, col_name in enumerate(columns):
                    txt = fonts["info"].render(col_name, True, WHITE)
                    # 文字居中显示在列内
                    txt_rect = txt.get_rect(center=(current_x + col_widths[i] // 2, table_y + row_height // 2))
                    surf.blit(txt, txt_rect)
                    current_x += col_widths[i]

                # 绘制数据行（最多显示8行，倒序）
                display_records = records[-8:]  # 只显示最后8条
                for row_idx, row in enumerate(display_records):
                    # 补全不足5列的数据
                    while len(row) < 5:
                        row.append("")

                    # 交替行背景色
                    row_y = table_y + (row_idx + 1) * row_height
                    if row_idx % 2 == 0:
                        pygame.draw.rect(surf, LIGHT_BLUE, (table_x, row_y, table_width, row_height))

                    # 绘制每行的列数据
                    current_x = table_x
                    for col_idx, cell_data in enumerate(row[:5]):
                        # 控制文字长度，超长时省略
                        if len(cell_data) > 15:
                            cell_data = cell_data[:12] + "..."

                        txt = fonts["mini"].render(cell_data, True, BLACK)
                        # 文字居中显示在列内
                        txt_rect = txt.get_rect(center=(current_x + col_widths[col_idx] // 2, row_y + row_height // 2))
                        surf.blit(txt, txt_rect)
                        current_x += col_widths[col_idx]

                    # 绘制行分隔线
                    pygame.draw.line(surf, (200, 200, 200), (table_x, row_y + row_height),
                                     (table_x + table_width, row_y + row_height), 1)

                # 绘制表格边框
                pygame.draw.rect(surf, BLACK, (table_x, table_y, table_width, row_height * (len(display_records) + 1)),
                                 2)

                # 绘制列分隔线
                current_x = table_x
                for col_width in col_widths[:-1]:
                    current_x += col_width
                    pygame.draw.line(surf, (200, 200, 200), (current_x, table_y),
                                     (current_x, table_y + row_height * (len(display_records) + 1)), 1)

    except Exception as e:
        error_text = f"读取记录失败: {str(e)}" if settings["language"] == "zh" else f"Load records failed: {str(e)}"
        error_txt = fonts["info"].render(error_text, True, RED)
        surf.blit(error_txt, error_txt.get_rect(center=(w // 2, h // 2)))


def save_record():
    try:
        total = len(QUESTIONS)
        correct = score
        acc = f"{(correct / total) * 100:.1f}%" if total > 0 else "0.0%"
        wrong = [str(i + 1) for i, (idx, ok) in enumerate(answer_history) if not ok]
        wrong_str = ",".join(wrong) if wrong else "无"
        row = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), str(correct), str(total), acc, wrong_str]
        with open(RECORD_FILE, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(row)
    except Exception as e:
        print(f"保存记录失败: {e}")


# ---------------------- 设置界面 ----------------------
setting_progress = {
    "window_small": 0, "window_mid": 0, "window_full": 0,
    "color_blue": 0, "color_green": 0, "color_red": 0,
    "lang_zh": 0, "lang_eng": 0
}


def draw_setting_interface(surf, palms, delta_time):
    fonts = get_fonts()
    w, h = settings["window_size"]
    surf.fill(WHITE)
    title = fonts["title"].render("系统设置" if settings["language"] == "zh" else "Settings", True, BLUE)
    surf.blit(title, title.get_rect(center=(w // 2, int(h * 0.07))))
    r = 45
    spacing = 120

    # 窗口
    y1 = int(h * 0.25)
    lbl = fonts["info"].render("窗口" if settings["language"] == "zh" else "Window", True, BLACK)
    surf.blit(lbl, (int(w * 0.15), y1 - r - 10))
    c1 = (int(w * 0.3), y1)
    c2 = (int(w * 0.3) + spacing, y1)
    c3 = (int(w * 0.3) + spacing * 2, y1)

    sel_win_small = (settings["window_mode"] == "小屏")
    touched = any(is_in_circle(p, c1, r) for p in palms)
    if touched:
        setting_progress["window_small"] = min(PROGRESS_FULL, setting_progress["window_small"] + settings[
            "progress_speed"] * delta_time)
        if setting_progress["window_small"] >= PROGRESS_FULL:
            settings["window_mode"] = "小屏"
            settings["window_size"] = (800, 600)
            global screen
            # 小屏启用高清渲染（移除SCALED避免冲突）
            screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
            for k in setting_progress: setting_progress[k] = 0
    else:
        setting_progress["window_small"] = max(0, setting_progress["window_small"] - PROGRESS_DECAY * delta_time)
    draw_circle_option(surf, c1, r, "小屏", setting_progress["window_small"], sel_win_small)

    sel_win_mid = (settings["window_mode"] == "中屏")
    touched = any(is_in_circle(p, c2, r) for p in palms)
    if touched:
        setting_progress["window_mid"] = min(PROGRESS_FULL,
                                             setting_progress["window_mid"] + settings["progress_speed"] * delta_time)
        if setting_progress["window_mid"] >= PROGRESS_FULL:
            settings["window_mode"] = "中屏"
            settings["window_size"] = (1024, 768)
            # 中屏启用高清渲染（移除SCALED避免冲突）
            screen = pygame.display.set_mode((1024, 768), pygame.RESIZABLE)
            for k in setting_progress: setting_progress[k] = 0
    else:
        setting_progress["window_mid"] = max(0, setting_progress["window_mid"] - PROGRESS_DECAY * delta_time)
    draw_circle_option(surf, c2, r, "中屏", setting_progress["window_mid"], sel_win_mid)

    sel_win_full = (settings["window_mode"] == "全屏")
    touched = any(is_in_circle(p, c3, r) for p in palms)
    if touched:
        setting_progress["window_full"] = min(PROGRESS_FULL,
                                              setting_progress["window_full"] + settings["progress_speed"] * delta_time)
        if setting_progress["window_full"] >= PROGRESS_FULL:
            settings["window_mode"] = "全屏"
            sw, sh = pygame.display.Info().current_w, pygame.display.Info().current_h
            settings["window_size"] = (sw, sh)
            # 修复：全屏模式移除SCALED标志，只保留FULLSCREEN
            screen = pygame.display.set_mode((sw, sh), pygame.FULLSCREEN)
            for k in setting_progress: setting_progress[k] = 0
    else:
        setting_progress["window_full"] = max(0, setting_progress["window_full"] - PROGRESS_DECAY * delta_time)
    draw_circle_option(surf, c3, r, "全屏", setting_progress["window_full"], sel_win_full)

    # 颜色
    y2 = y1 + 150
    lbl = fonts["info"].render("圆色" if settings["language"] == "zh" else "Palm Color", True, BLACK)
    surf.blit(lbl, (int(w * 0.15), y2 - r - 10))
    c4 = (int(w * 0.3), y2)
    c5 = (int(w * 0.3) + spacing, y2)
    c6 = (int(w * 0.3) + spacing * 2, y2)

    sel_blue = (settings["hand_color_name"] == "蓝")
    touched = any(is_in_circle(p, c4, r) for p in palms)
    if touched:
        setting_progress["color_blue"] = min(PROGRESS_FULL,
                                             setting_progress["color_blue"] + settings["progress_speed"] * delta_time)
        if setting_progress["color_blue"] >= PROGRESS_FULL:
            settings["hand_color"] = BLUE
            settings["hand_color_name"] = "蓝"
            for k in setting_progress: setting_progress[k] = 0
    else:
        setting_progress["color_blue"] = max(0, setting_progress["color_blue"] - PROGRESS_DECAY * delta_time)
    draw_circle_option(surf, c4, r, "蓝", setting_progress["color_blue"], sel_blue, BLUE)

    sel_green = (settings["hand_color_name"] == "绿")
    touched = any(is_in_circle(p, c5, r) for p in palms)
    if touched:
        setting_progress["color_green"] = min(PROGRESS_FULL,
                                              setting_progress["color_green"] + settings["progress_speed"] * delta_time)
        if setting_progress["color_green"] >= PROGRESS_FULL:
            settings["hand_color"] = GREEN
            settings["hand_color_name"] = "绿"
            for k in setting_progress: setting_progress[k] = 0
    else:
        setting_progress["color_green"] = max(0, setting_progress["color_green"] - PROGRESS_DECAY * delta_time)
    draw_circle_option(surf, c5, r, "绿", setting_progress["color_green"], sel_green, GREEN)

    sel_red = (settings["hand_color_name"] == "红")
    touched = any(is_in_circle(p, c6, r) for p in palms)
    if touched:
        setting_progress["color_red"] = min(PROGRESS_FULL,
                                            setting_progress["color_red"] + settings["progress_speed"] * delta_time)
        if setting_progress["color_red"] >= PROGRESS_FULL:
            settings["hand_color"] = RED
            settings["hand_color_name"] = "红"
            for k in setting_progress: setting_progress[k] = 0
    else:
        setting_progress["color_red"] = max(0, setting_progress["color_red"] - PROGRESS_DECAY * delta_time)
    draw_circle_option(surf, c6, r, "红", setting_progress["color_red"], sel_red, RED)

    # 语言
    y3 = y2 + 150
    lbl = fonts["info"].render("语言" if settings["language"] == "zh" else "Language", True, BLACK)
    surf.blit(lbl, (int(w * 0.15), y3 - r - 10))
    c7 = (int(w * 0.3), y3)
    c8 = (int(w * 0.3) + spacing, y3)

    sel_zh = (settings["language"] == "zh")
    touched = any(is_in_circle(p, c7, r) for p in palms)
    if touched:
        setting_progress["lang_zh"] = min(PROGRESS_FULL,
                                          setting_progress["lang_zh"] + settings["progress_speed"] * delta_time)
        if setting_progress["lang_zh"] >= PROGRESS_FULL:
            settings["language"] = "zh"
            global QUESTIONS
            QUESTIONS = QUESTIONS_ZH
            random.shuffle(QUESTIONS)
            for k in setting_progress: setting_progress[k] = 0
    else:
        setting_progress["lang_zh"] = max(0, setting_progress["lang_zh"] - PROGRESS_DECAY * delta_time)
    draw_circle_option(surf, c7, r, "中文", setting_progress["lang_zh"], sel_zh)

    sel_eng = (settings["language"] == "eng")
    touched = any(is_in_circle(p, c8, r) for p in palms)
    if touched:
        setting_progress["lang_eng"] = min(PROGRESS_FULL,
                                           setting_progress["lang_eng"] + settings["progress_speed"] * delta_time)
        if setting_progress["lang_eng"] >= PROGRESS_FULL:
            settings["language"] = "eng"
            QUESTIONS = QUESTIONS_ENG
            random.shuffle(QUESTIONS)
            for k in setting_progress: setting_progress[k] = 0
    else:
        setting_progress["lang_eng"] = max(0, setting_progress["lang_eng"] - PROGRESS_DECAY * delta_time)
    draw_circle_option(surf, c8, r, "英文", setting_progress["lang_eng"], sel_eng)


# ---------------------- 主循环 ----------------------
cap = cv2.VideoCapture(0)
running = True
all_palms = []
last_time = time.time()

while running:
    now = time.time()
    delta = now - last_time
    last_time = now

    ret, frame = cap.read()
    if not ret: break
    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = hands.process(rgb)

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            if settings["window_mode"] == "全屏":
                settings["window_mode"] = "中屏"
                settings["window_size"] = (1024, 768)
                # 退出全屏时也移除SCALED标志
                screen = pygame.display.set_mode((1024, 768), pygame.RESIZABLE)

    screen.fill(WHITE)
    all_palms = []
    if res.multi_hand_landmarks:
        for lm in res.multi_hand_landmarks:
            all_palms.append(get_palm_center(lm))

    if current_state == STATE_START:
        fonts = get_fonts()
        w, h = settings["window_size"]
        nte = fonts["big"].render("NTE", True, BLUE)
        screen.blit(nte, nte.get_rect(center=(w // 2, int(h * 0.33))))
        start_circle["pos"] = (int(w * 0.25), int(h * 0.67))
        record_circle["pos"] = (int(w * 0.5), int(h * 0.67))
        setting_circle["pos"] = (int(w * 0.75), int(h * 0.67))
        for c in function_circles:
            touched = any(is_in_circle(p, c["pos"], c["radius"] * settings["font_scale"]) for p in all_palms)
            if touched:
                c["progress"] = min(PROGRESS_FULL, c["progress"] + settings["progress_speed"] * delta)
            else:
                c["progress"] = max(0, c["progress"] - PROGRESS_DECAY * delta)
            draw_circle_option(screen, c["pos"], int(c["radius"] * settings["font_scale"]), c["name"], c["progress"],
                               False)
            if c["progress"] >= PROGRESS_FULL:
                if c["name"] == "开始":
                    current_state = STATE_ANSWER
                    start_time = now
                    left_time = settings["question_time"]
                elif c["name"] == "记录":
                    current_state = STATE_RECORD
                elif c["name"] == "设置":
                    current_state = STATE_SETTING
                for cc in function_circles: cc["progress"] = 0

    elif current_state == STATE_ANSWER:
        count_hands_in_options(all_palms)
        if not show_result:
            if start_time == 0: start_time = now
            left_time = max(0, settings["question_time"] - (now - start_time))
            if left_time <= 0:
                current_is_correct = False
                result_text = "时间到！回答错误" if settings["language"] == "zh" else "Time up! Wrong"
                answer_history.append((current_question, False))
                show_result = True
                result_show_time = now
                start_time = 0
            sel = None
            if all_palms:
                main = all_palms[0]
                areas = get_option_areas()
                for k in ["A", "B", "C"]:
                    x1, y1, w, h = areas[k]
                    if x1 < main[0] < x1 + w and y1 < main[1] < y1 + h:
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
                            result_text = "回答正确！🎉" if settings["language"] == "zh" else "Correct! 🎉"
                            w, h = settings["window_size"]
                            for _ in range(6):
                                fireworks.append(Firework(random.randint(100, w - 100), random.randint(50, h - 50)))
                        else:
                            result_text = "回答错误" if settings["language"] == "zh" else "Wrong"
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

    elif current_state == STATE_RECORD:
        draw_record(screen)
        if draw_back_circle(screen, delta, all_palms):
            current_state = STATE_START

    elif current_state == STATE_SETTING:
        draw_setting_interface(screen, all_palms, delta)
        if draw_back_circle(screen, delta, all_palms):
            current_state = STATE_START

    for p in all_palms:
        draw_palm_center(screen, p)

    pygame.display.update()
    clock.tick(120)

cap.release()
pygame.quit()