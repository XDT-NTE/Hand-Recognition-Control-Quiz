import cv2
import mediapipe as mp
import pygame
import time
import random
import math

# ---------------------- 初始化全局参数 ----------------------
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("NTE 体测答题系统")
clock = pygame.time.Clock()

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (30, 30, 30)
RED = (220, 0, 0)
GREEN = (0, 220, 0)
BLUE = (0, 80, 200)
LIGHT_BLUE = (230, 240, 255)
YELLOW = (255, 200, 0)
HAND_DOT_COLOR = (0, 255, 0)
COUNT_COLOR = (255, 100, 0)
CORRECT_BG = (180, 255, 180)
INCORRECT_BG = (255, 180, 180)

# 字体
font_big = pygame.font.SysFont("SimHei", 60, bold=True)
font_title = pygame.font.SysFont("SimHei", 40, bold=True)
font_question = pygame.font.SysFont("SimHei", 32)
font_option = pygame.font.SysFont("SimHei", 30)
font_info = pygame.font.SysFont("SimHei", 26)
font_count = pygame.font.SysFont("SimHei", 28, bold=True)
font_result = pygame.font.SysFont("SimHei", 36, bold=True)

# 状态枚举
STATE_START = 0  # 启动界面
STATE_ANSWER = 1  # 答题界面
STATE_SUMMARY = 2  # 总结界面

current_state = STATE_START

# ---------------------- 启动界面参数 ----------------------
# 功能圆参数 (中心坐标, 半径, 名称, 进度条进度, 是否被触碰)
start_circle = {"pos": (200, 400), "radius": 60, "name": "开始", "progress": 0, "active": False}
record_circle = {"pos": (400, 400), "radius": 60, "name": "记录", "progress": 0, "active": False}
setting_circle = {"pos": (600, 400), "radius": 60, "name": "设置", "progress": 0, "active": False}
function_circles = [start_circle, record_circle, setting_circle]

PROGRESS_FULL = 100
# 🔥 关键：按住 5 秒就满
PROGRESS_SPEED = 20  # 每秒增加 20%，5秒满
PROGRESS_DECAY = 50  # 松开后掉得快一点

# ---------------------- 手部检测 ----------------------
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=4,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)


# ---------------------- 烟花特效 ----------------------
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
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.life > 10]

    def draw(self, surf):
        for p in self.particles:
            p.draw(surf)


fireworks = []

# ---------------------- 答题系统参数 ----------------------
QUESTIONS = [
    {"question": "小学1分钟跳绳体测，四年级优秀标准约是多少个？", "options": ["A.100个", "B.130个", "C.80个"],
     "answer": "B"},
    {"question": "50米跑前，我们需要做什么准备？", "options": ["A.直接跑", "B.热身运动", "C.喝水"], "answer": "B"},
    {"question": "坐位体前屈测试时，身体应该？", "options": ["A.弯腰前倾", "B.挺直腰杆", "C.后仰"], "answer": "A"},
    {"question": "跑步时不小心摔倒，第一时间要？", "options": ["A.立刻爬起来", "B.检查伤口", "C.大哭"], "answer": "B"},
    {"question": "仰卧起坐1分钟，四年级合格标准约是多少个？", "options": ["A.20个", "B.10个", "C.35个"], "answer": "A"}
]
random.shuffle(QUESTIONS)

current_question = 0
score = 0
question_time = 20
start_time = 0
left_time = question_time

option_areas = {
    "A": (80, 400, 200, 80),
    "B": (300, 400, 200, 80),
    "C": (520, 400, 200, 80)
}
hand_stay_time = {}
STAY_CONFIRM_TIME = 3

option_hand_count = {"A": 0, "B": 0, "C": 0}
answer_history = []
show_result = False
result_text = ""
result_show_time = 0
current_is_correct = False


# ---------------------- 工具函数 ----------------------
def get_palm_center(hand_landmarks):
    x_sum = sum(hand_landmarks.landmark[i].x for i in [0, 5, 9, 13, 17])
    y_sum = sum(hand_landmarks.landmark[i].y for i in [0, 5, 9, 13, 17])
    return int(x_sum / 5 * WIDTH), int(y_sum / 5 * HEIGHT)


def draw_palm_center(surf, palm_center):
    x, y = palm_center
    pygame.draw.circle(surf, (255, 255, 255), (x, y), 18)
    pygame.draw.circle(surf, HAND_DOT_COLOR, (x, y), 16)


def is_point_in_circle(point, circle_pos, circle_radius):
    dx = point[0] - circle_pos[0]
    dy = point[1] - circle_pos[1]
    return math.hypot(dx, dy) <= circle_radius


def draw_progress_circle(surf, circle, delta_time):
    pos = circle["pos"]
    radius = circle["radius"]
    name = circle["name"]
    progress = circle["progress"]

    pygame.draw.circle(surf, LIGHT_BLUE, pos, radius)
    pygame.draw.circle(surf, BLUE, pos, radius, 3)

    if progress > 0:
        arc_angle = 2 * math.pi * (progress / PROGRESS_FULL)
        pygame.draw.arc(
            surf, YELLOW,
            (pos[0] - radius - 8, pos[1] - radius - 8, (radius + 8) * 2, (radius + 8) * 2),
            -math.pi / 2, -math.pi / 2 + arc_angle,
            6
        )

    text = font_info.render(name, True, BLACK)
    text_rect = text.get_rect(center=pos)
    surf.blit(text, text_rect)

    progress_text = font_info.render(f"{int(progress)}%", True, RED)
    progress_rect = progress_text.get_rect(center=(pos[0], pos[1] + radius // 2))
    surf.blit(progress_text, progress_rect)


def count_hands_in_options(palm_centers):
    global option_hand_count
    option_hand_count = {"A": 0, "B": 0, "C": 0}
    for (x, y) in palm_centers:
        for k, (x1, y1, w, h) in option_areas.items():
            if x1 < x < x1 + w and y1 < y < y1 + h:
                option_hand_count[k] += 1
                break


def draw_answer_interface(surf, question, options, left_time, score, hand_count):
    surf.fill(WHITE)
    title_text = font_title.render("NTE 体测答题", True, BLUE)
    surf.blit(title_text, title_text.get_rect(center=(WIDTH // 2, 40)))

    q_text = font_question.render(question, True, BLACK)
    surf.blit(q_text, q_text.get_rect(center=(WIDTH // 2, 150)))

    time_color = RED if left_time <= 5 else BLACK
    time_text = font_info.render(f"剩余时间：{int(left_time)}秒", True, time_color)
    surf.blit(time_text, (WIDTH - 250, 90))

    score_text = font_info.render(f"得分：{score}", True, GREEN)
    surf.blit(score_text, (80, 90))

    for opt in options:
        key = opt[0]
        x, y, w, h = option_areas[key]
        pygame.draw.rect(surf, LIGHT_BLUE, (x, y, w, h))
        pygame.draw.rect(surf, BLUE, (x, y, w, h), 3)

        t = font_option.render(opt, True, BLACK)
        surf.blit(t, t.get_rect(center=(x + w // 2, y + h // 2 - 10)))
        cnt = font_count.render(f"人数：{hand_count[key]}", True, COUNT_COLOR)
        surf.blit(cnt, (x + 10, y + 50))


def draw_result_with_box(surf, text, is_correct, pos):
    col = GREEN if is_correct else RED
    bg = CORRECT_BG if is_correct else INCORRECT_BG
    ts = font_result.render(text, True, col)
    tr = ts.get_rect(center=pos)
    bg_rect = pygame.Rect(tr.x - 10, tr.y - 10, tr.width + 20, tr.height + 20)
    pygame.draw.rect(surf, bg, bg_rect, border_radius=8)
    pygame.draw.rect(surf, col, bg_rect, 2, border_radius=8)
    surf.blit(ts, tr)


def draw_summary_interface(surf):
    surf.fill(WHITE)
    title = font_title.render("答题总结", True, BLUE)
    surf.blit(title, title.get_rect(center=(WIDTH // 2, 50)))

    y = 130
    for i in range(len(QUESTIONS)):
        ok = answer_history[i][1]
        s = f"第{i + 1}题：{'正确' if ok else '错误'}"
        draw_result_with_box(surf, s, ok, (WIDTH // 2, y))
        y += 80

    final = font_result.render(f"最终得分：{score}/{len(QUESTIONS)}", True, BLUE)
    surf.blit(final, final.get_rect(center=(WIDTH // 2, y + 40)))


# ---------------------- 主循环 ----------------------
cap = cv2.VideoCapture(0)
running = True
all_palms = []
last_time = time.time()

while running:
    current_time = time.time()
    delta_time = current_time - last_time
    last_time = current_time

    ret, frame = cap.read()
    if not ret: break
    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = hands.process(rgb)

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

    screen.fill(WHITE)

    all_palms = []
    if res.multi_hand_landmarks:
        for lm in res.multi_hand_landmarks:
            all_palms.append(get_palm_center(lm))

    # ---------------------- 启动界面 ----------------------
    if current_state == STATE_START:
        nte_text = font_big.render("NTE", True, BLUE)
        screen.blit(nte_text, nte_text.get_rect(center=(WIDTH // 2, 200)))

        for circle in function_circles:
            touched = False
            if all_palms:
                for palm in all_palms:
                    if is_point_in_circle(palm, circle["pos"], circle["radius"]):
                        touched = True
                        break

            if touched:
                circle["progress"] = min(PROGRESS_FULL, circle["progress"] + PROGRESS_SPEED * delta_time)
            else:
                circle["progress"] = max(0, circle["progress"] - PROGRESS_DECAY * delta_time)

            draw_progress_circle(screen, circle, delta_time)

            if circle["name"] == "开始" and circle["progress"] >= PROGRESS_FULL:
                current_state = STATE_ANSWER
                for c in function_circles:
                    c["progress"] = 0
                start_time = time.time()
                left_time = question_time

    # ---------------------- 答题界面 ----------------------
    elif current_state == STATE_ANSWER:
        count_hands_in_options(all_palms)

        if not show_result:
            if start_time == 0:
                start_time = time.time()
            left_time = max(0, question_time - (current_time - start_time))

            if left_time <= 0:
                current_is_correct = False
                result_text = "时间到！回答错误"
                answer_history.append((current_question, False))
                show_result = True
                result_show_time = current_time
                start_time = 0

            selected_key = None
            if all_palms:
                main_palm = all_palms[0]
                for k in ["A", "B", "C"]:
                    x1, y1, w, h = option_areas[k]
                    x, y = main_palm
                    if x1 < x < x1 + w and y1 < y < y1 + h:
                        selected_key = k
                        break

            if selected_key is not None:
                if selected_key not in hand_stay_time:
                    hand_stay_time[selected_key] = current_time
                else:
                    if current_time - hand_stay_time[selected_key] >= STAY_CONFIRM_TIME:
                        ans = QUESTIONS[current_question]["answer"]
                        current_is_correct = (selected_key == ans)

                        if current_is_correct:
                            score += 1
                            result_text = "回答正确！🎉"
                            x, y, _, _ = option_areas[selected_key]
                            for _ in range(6):
                                fireworks.append(Firework(random.randint(100, WIDTH - 100), random.randint(50, 250)))
                        else:
                            result_text = "回答错误"

                        answer_history.append((current_question, current_is_correct))
                        show_result = True
                        result_show_time = current_time
                        start_time = 0
                        hand_stay_time.clear()
            else:
                hand_stay_time.clear()

        q = QUESTIONS[current_question]
        draw_answer_interface(screen, q["question"], q["options"], left_time, score, option_hand_count)

        if show_result:
            draw_result_with_box(screen, result_text, current_is_correct, (WIDTH // 2, 200))

            if current_time - result_show_time > 2.5:
                show_result = False
                current_question += 1
                if current_question >= len(QUESTIONS):
                    current_state = STATE_SUMMARY
                else:
                    start_time = 0
                    left_time = question_time
                    hand_stay_time.clear()

        for fw in fireworks[:]:
            fw.update()
            fw.draw(screen)
            if not fw.particles:
                fireworks.remove(fw)

    # ---------------------- 总结界面 ----------------------
    elif current_state == STATE_SUMMARY:
        draw_summary_interface(screen)

    for palm in all_palms:
        draw_palm_center(screen, palm)

    pygame.display.update()
    clock.tick(120)

cap.release()
pygame.quit()