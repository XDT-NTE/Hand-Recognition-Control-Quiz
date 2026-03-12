import cv2
import mediapipe as mp
import pygame
import time
import random
import math

# ---------------------- 初始化 ----------------------
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("校园体测智慧答题")
clock = pygame.time.Clock()

transparent_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
effect_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

TRANSPARENCY = 255
WHITE = (255, 255, 255, TRANSPARENCY)
BLACK = (30, 30, 30, TRANSPARENCY)
RED = (220, 0, 0, TRANSPARENCY)
GREEN = (0, 220, 0, TRANSPARENCY)
BLUE = (0, 80, 200, TRANSPARENCY)
LIGHT_BLUE = (230, 240, 255, TRANSPARENCY)
HAND_DOT_COLOR = (0, 255, 0)
COUNT_COLOR = (255, 100, 0, TRANSPARENCY)

CORRECT_BG = (180, 255, 180, 220)
INCORRECT_BG = (255, 180, 180, 220)

# 字体
font_title = pygame.font.SysFont("SimHei", 40, bold=True)
font_question = pygame.font.SysFont("SimHei", 32)
font_option = pygame.font.SysFont("SimHei", 30)
font_info = pygame.font.SysFont("SimHei", 26)
font_count = pygame.font.SysFont("SimHei", 28, bold=True)
font_result = pygame.font.SysFont("SimHei", 36, bold=True)


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


class FailEffect:
    def __init__(self, duration=1):
        self.start = time.time()
        self.duration = duration
        self.active = False

    def trigger(self):
        self.active = True
        self.start = time.time()

    def update(self):
        if self.active and time.time() - self.start > self.duration:
            self.active = False
        return self.active


fireworks = []
fail_effect = FailEffect()

# ---------------------- 手部检测 ----------------------
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=4,
                       min_detection_confidence=0.5, min_tracking_confidence=0.5)

# ---------------------- 题库 ----------------------
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
question_count_history = []
answer_history = []


# ---------------------- 函数 ----------------------
def get_palm_center(hand_landmarks):
    x_sum = sum(hand_landmarks.landmark[i].x for i in [0, 5, 9, 13, 17])
    y_sum = sum(hand_landmarks.landmark[i].y for i in [0, 5, 9, 13, 17])
    return int(x_sum / 5 * WIDTH), int(y_sum / 5 * HEIGHT)


def draw_palm_center(surf, palm_center):
    x, y = palm_center
    pygame.draw.circle(surf, (255, 255, 255), (x, y), 18)
    pygame.draw.circle(surf, HAND_DOT_COLOR, (x, y), 16)


def count_hands_in_options(palm_centers):
    global option_hand_count
    option_hand_count = {"A": 0, "B": 0, "C": 0}
    for (x, y) in palm_centers:
        for k, (x1, y1, w, h) in option_areas.items():
            if x1 < x < x1 + w and y1 < y < y1 + h:
                option_hand_count[k] += 1
                break


def draw_interface(transparent_surf, question, options, left_time, score, hand_count):
    transparent_surf.fill((0, 0, 0, 0))
    pygame.draw.rect(transparent_surf, WHITE, (0, 0, WIDTH, HEIGHT))

    title_text = font_title.render("校园体测智慧答题", True, BLUE)
    transparent_surf.blit(title_text, title_text.get_rect(center=(WIDTH // 2, 40)))

    q_text = font_question.render(question, True, BLACK)
    transparent_surf.blit(q_text, q_text.get_rect(center=(WIDTH // 2, 150)))

    time_color = RED if left_time <= 5 else BLACK
    time_text = font_info.render(f"剩余时间：{int(left_time)}秒", True, time_color)
    transparent_surf.blit(time_text, (WIDTH - 250, 90))

    score_text = font_info.render(f"得分：{score}", True, GREEN)
    transparent_surf.blit(score_text, (80, 90))

    for opt in options:
        key = opt[0]
        x, y, w, h = option_areas[key]
        pygame.draw.rect(transparent_surf, LIGHT_BLUE, (x, y, w, h))
        pygame.draw.rect(transparent_surf, BLUE, (x, y, w, h), 3)

        t = font_option.render(opt, True, BLACK)
        transparent_surf.blit(t, t.get_rect(center=(x + w // 2, y + h // 2 - 10)))
        cnt = font_count.render(f"人数：{hand_count[key]}", True, COUNT_COLOR)
        transparent_surf.blit(cnt, (x + 10, y + 50))


def is_palm_in_option(palm, key):
    x1, y1, w, h = option_areas[key]
    x, y = palm
    return x1 < x < x1 + w and y1 < y < y1 + h


def draw_result_with_box(surf, text, is_correct, pos):
    col = GREEN if is_correct else RED
    bg = CORRECT_BG if is_correct else INCORRECT_BG
    ts = font_result.render(text, True, col)
    tr = ts.get_rect(center=pos)
    bg_rect = pygame.Rect(tr.x - 10, tr.y - 10, tr.width + 20, tr.height + 20)
    pygame.draw.rect(surf, bg, bg_rect, border_radius=8)
    pygame.draw.rect(surf, col, bg_rect, 2, border_radius=8)
    surf.blit(ts, tr)


# ====================== 修复：答题总结排版，不重叠 ======================
def draw_final_summary(transparent_surf, count_history, answer_history):
    transparent_surf.fill((0, 0, 0, 0))
    transparent_surf.fill(WHITE)
    title = font_title.render("答题总结", True, BLUE)
    transparent_surf.blit(title, title.get_rect(center=(WIDTH // 2, 50)))

    y = 130
    for i in range(len(QUESTIONS)):
        ok = answer_history[i][1]
        s = f"第{i + 1}题：{'正确' if ok else '错误'}"
        draw_result_with_box(transparent_surf, s, ok, (WIDTH // 2, y))
        y += 80  # 行距加大，完全不重叠

    final = font_result.render(f"最终得分：{score}/{len(QUESTIONS)}", True, BLUE)
    transparent_surf.blit(final, final.get_rect(center=(WIDTH // 2, y + 40)))


# ---------------------- 主循环 ----------------------
cap = cv2.VideoCapture(0)
running = True
show_result = False
result_text = ""
result_show_time = 0
all_palms = []
current_is_correct = False

while running:
    ret, frame = cap.read()
    if not ret: break
    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = hands.process(rgb)

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

    screen.fill((245, 245, 245))
    transparent_surface.fill((0, 0, 0, 0))
    effect_surface.fill((0, 0, 0, 0))

    all_palms = []
    if res.multi_hand_landmarks:
        for lm in res.multi_hand_landmarks:
            all_palms.append(get_palm_center(lm))
    count_hands_in_options(all_palms)

    if not show_result:
        if start_time == 0:
            start_time = time.time()
        left_time = max(0, question_time - (time.time() - start_time))

        if left_time <= 0:
            current_is_correct = False
            result_text = "时间到！回答错误"
            answer_history.append((current_question, False))
            fail_effect.trigger()
            show_result = True
            result_show_time = time.time()
            start_time = 0

        selected_key = None
        if all_palms:
            main_palm = all_palms[0]
            for k in ["A", "B", "C"]:
                if is_palm_in_option(main_palm, k):
                    selected_key = k
                    break

        if selected_key is not None:
            if selected_key not in hand_stay_time:
                hand_stay_time[selected_key] = time.time()
            else:
                if time.time() - hand_stay_time[selected_key] >= STAY_CONFIRM_TIME:
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
                        fail_effect.trigger()

                    answer_history.append((current_question, current_is_correct))
                    show_result = True
                    result_show_time = time.time()
                    start_time = 0
                    hand_stay_time.clear()
        else:
            hand_stay_time.clear()

    q = QUESTIONS[current_question]
    if not show_result:
        draw_interface(transparent_surface, q["question"], q["options"], left_time, score, option_hand_count)
    else:
        # ====================== 修复：结果提示放在屏幕中间偏上，不挡选项 ======================
        draw_result_with_box(transparent_surface, result_text, current_is_correct, (WIDTH // 2, 200))

    for p in all_palms:
        draw_palm_center(screen, p)

    for fw in fireworks[:]:
        fw.update()
        fw.draw(effect_surface)
        if not fw.particles:
            fireworks.remove(fw)
    fail_effect.update()

    screen.blit(transparent_surface, (0, 0))
    screen.blit(effect_surface, (0, 0))
    for p in all_palms:
        draw_palm_center(screen, p)

    if show_result and time.time() - result_show_time > 2.5:
        show_result = False
        current_question += 1
        if current_question >= len(QUESTIONS):
            draw_final_summary(transparent_surface, question_count_history, answer_history)
            screen.blit(transparent_surface, (0, 0))
            pygame.display.update()
            pygame.time.wait(10000)
            running = False
        start_time = 0
        left_time = question_time
        hand_stay_time.clear()

    pygame.display.update()
    clock.tick(30)

cap.release()
pygame.quit()