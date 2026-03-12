import cv2
import mediapipe as mp
import pygame
import time
import random
# pip install opencv-python pygame
# pip install mediapipe==0.10.20 --force-reinstall -i https://pypi.tuna.tsinghua.edu.cn/simple/
# ---------------------- 1. 初始化Pygame（纯界面，无音效） ----------------------
pygame.init()
# 界面设置（适配小学电脑）
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("校园体测运动智慧答题-手部版")
clock = pygame.time.Clock()

# 颜色定义（童趣护眼）
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)

# 字体设置（系统自带，中文兼容）
font_big = pygame.font.SysFont("SimHei", 36)  # 题目字体
font_mid = pygame.font.SysFont("SimHei", 28)  # 选项/计时字体
font_small = pygame.font.SysFont("SimHei", 24)  # 得分字体

# ---------------------- 2. 初始化旧版MediaPipe手部检测（抗光+多人） ----------------------
mp_hands = mp.solutions.hands
# 核心抗光配置：max_num_hands=4（多人），min_detection_confidence=0.5（抗光）
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=4,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)
mp_drawing = mp.solutions.drawing_utils  # 绘制手部关键点

# ---------------------- 3. 校园体测题库（可直接修改） ----------------------
QUESTIONS = [
    {
        "question": "小学1分钟跳绳体测，四年级优秀标准约是多少个？",
        "options": ["A.100个", "B.130个", "C.80个"],
        "answer": "B"
    },
    {
        "question": "50米跑前，我们需要做什么准备？",
        "options": ["A.直接跑", "B.热身运动", "C.喝水"],
        "answer": "B"
    },
    {
        "question": "坐位体前屈测试时，身体应该？",
        "options": ["A.弯腰前倾", "B.挺直腰杆", "C.后仰"],
        "answer": "A"
    },
    {
        "question": "跑步时不小心摔倒，第一时间要？",
        "options": ["A.立刻爬起来", "B.检查伤口", "C.大哭"],
        "answer": "B"
    },
    {
        "question": "仰卧起坐1分钟，四年级合格标准约是多少个？",
        "options": ["A.20个", "B.10个", "C.35个"],
        "answer": "A"
    }
]
random.shuffle(QUESTIONS)  # 随机出题

# ---------------------- 4. 答题核心参数 ----------------------
current_question = 0  # 当前题目
score = 0  # 得分
question_time = 20  # 每题答题时间（秒）
start_time = 0  # 计时开始时间
# 选项区域坐标
option_areas = {
    "A": (50, 450, 200, 100),
    "B": (300, 450, 200, 100),
    "C": (550, 450, 200, 100)
}
hand_stay_time = {}  # 手部停留计时
STAY_CONFIRM_TIME = 3  # 3秒确认


# ---------------------- 5. 核心函数 ----------------------
# 绘制答题界面
def draw_interface(question, options, left_time, score):
    screen.fill(WHITE)
    # 绘制题目
    q_text = font_big.render(question, True, BLACK)
    screen.blit(q_text, (50, 50))
    # 绘制选项
    for opt in options:
        key = opt[0]
        x1, y1, w, h = option_areas[key]
        pygame.draw.rect(screen, BLUE, (x1, y1, w, h), 3)
        opt_text = font_mid.render(opt, True, BLACK)
        screen.blit(opt_text, (x1 + 20, y1 + 30))
    # 倒计时（<5秒变红）
    time_color = RED if left_time <= 5 else BLACK
    time_text = font_mid.render(f"剩余时间：{int(left_time)}秒", True, time_color)
    screen.blit(time_text, (600, 50))
    # 得分
    score_text = font_small.render(f"当前得分：{score}", True, GREEN)
    screen.blit(score_text, (50, 150))
    pygame.display.update()


# 检测手指是否在选项区域
def is_hand_in_option(hand_landmarks, option_area):
    x1, y1, w, h = option_area
    # 食指指尖关键点
    finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    # 转换为屏幕坐标
    x = int(finger_tip.x * WIDTH)
    y = int(finger_tip.y * HEIGHT)
    return x1 < x < x1 + w and y1 < y < y1 + h


# 判定答案
def check_answer(select_key, correct_key):
    global score
    if select_key == correct_key:
        score += 1
        return "答对啦！🎉"
    else:
        return f"答错了😟，正确答案是{correct_key}"


# ---------------------- 6. 主程序循环 ----------------------
cap = cv2.VideoCapture(0)  # 打开摄像头
running = True
show_result = False
result_text = ""
result_show_time = 0

while running:
    ret, frame = cap.read()
    if not ret:
        break
    frame = cv2.flip(frame, 1)  # 镜像翻转
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)  # 检测手部

    # 处理Pygame事件
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if not show_result:
        # 计时逻辑
        if start_time == 0:
            start_time = time.time()
        left_time = question_time - (time.time() - start_time)

        # 超时判定
        if left_time <= 0:
            result_text = f"时间到啦😟，正确答案是{QUESTIONS[current_question]['answer']}"
            show_result = True
            result_show_time = time.time()
            start_time = 0

        # 手部检测+停留判定
        current_in_options = []
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # 绘制手部关键点
                mp_drawing.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                # 检测选项区域
                for key, area in option_areas.items():
                    if is_hand_in_option(hand_landmarks, area):
                        current_in_options.append(key)
                        if key not in hand_stay_time:
                            hand_stay_time[key] = time.time()
                        # 3秒确认
                        elif time.time() - hand_stay_time[key] >= STAY_CONFIRM_TIME:
                            result_text = check_answer(key, QUESTIONS[current_question]['answer'])
                            show_result = True
                            result_show_time = time.time()
                            start_time = 0
                            hand_stay_time.clear()
                            break

        # 清空无手部的停留计时
        for key in list(hand_stay_time.keys()):
            if key not in current_in_options:
                del hand_stay_time[key]

        # 绘制界面
        q = QUESTIONS[current_question]
        draw_interface(q["question"], q["options"], left_time, score)
    else:
        # 显示结果
        screen.fill(WHITE)
        res_text = font_big.render(result_text, True, BLACK)
        score_text = font_mid.render(f"当前得分：{score}/{current_question + 1}", True, GREEN)
        screen.blit(res_text, (50, 200))
        screen.blit(score_text, (50, 300))
        pygame.display.update()

        # 3秒后切题
        if time.time() - result_show_time >= 3:
            show_result = False
            current_question += 1
            # 答题结束
            if current_question >= len(QUESTIONS):
                result_text = f"答题结束！最终得分：{score}/{len(QUESTIONS)}"
                screen.fill(WHITE)
                end_text = font_big.render(result_text, True, BLACK)
                tip_text = font_mid.render("你是运动小达人！👍", True, RED)
                screen.blit(end_text, (50, 200))
                screen.blit(tip_text, (50, 300))
                pygame.display.update()
                pygame.time.wait(5000)
                running = False
            hand_stay_time.clear()

    # 显示摄像头窗口
    cv2.imshow("手部检测窗口（按q关闭）", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        running = False

    clock.tick(30)

# 释放资源
cap.release()
cv2.destroyAllWindows()
pygame.quit()