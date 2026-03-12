import cv2
import mediapipe as mp
import pygame
import time
import random

# pip install opencv-python pygame
# pip install mediapipe==0.10.20 --force-reinstall -i https://pypi.tuna.tsinghua.edu.cn/simple/

# ---------------------- 1. 初始化Pygame（带透明层配置） ----------------------
pygame.init()
# 界面设置（适配小学电脑）
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("校园体测运动智慧答题-多手掌计数版")
clock = pygame.time.Clock()

# 创建透明层用于绘制题目界面（核心：带alpha通道的Surface）
transparent_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
# 透明度设置（0=全透，255=不透）
TRANSPARENCY = 230

# 颜色定义（童趣护眼）
WHITE = (255, 255, 255, TRANSPARENCY)  # 背景
BLACK = (30, 30, 30, TRANSPARENCY)  # 常规文字
RED = (220, 0, 0, TRANSPARENCY)  # 倒计时警告/错误
GREEN = (0, 180, 0, TRANSPARENCY)  # 得分/正确
BLUE = (0, 80, 200, TRANSPARENCY)  # 选项边框
LIGHT_BLUE = (230, 240, 255, TRANSPARENCY)  # 选项背景
HAND_DOT_COLOR = (0, 200, 0, 220)  # 手掌中心点颜色
HAND_DOT_SIZE = 12  # 手掌中心点大小
COUNT_COLOR = (255, 100, 0, TRANSPARENCY)  # 计数文字颜色

# 字体设置（系统自带，中文兼容）
font_title = pygame.font.SysFont("SimHei", 40, bold=True)  # 标题字体
font_question = pygame.font.SysFont("SimHei", 32)  # 题目字体
font_option = pygame.font.SysFont("SimHei", 30)  # 选项字体
font_info = pygame.font.SysFont("SimHei", 26)  # 计时/得分字体
font_count = pygame.font.SysFont("SimHei", 28, bold=True)  # 计数字体

# ---------------------- 2. 初始化MediaPipe手部检测 ----------------------
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=4,  # 支持最多4个手掌检测
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# ---------------------- 3. 校园体测题库 ----------------------
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
random.shuffle(QUESTIONS)

# ---------------------- 4. 答题核心参数 ----------------------
current_question = 0
score = 0
question_time = 20  # 每题答题时间（秒）
start_time = 0

# 优化后的选项区域坐标
option_areas = {
    "A": (80, 400, 200, 80),  # x, y, 宽, 高
    "B": (300, 400, 200, 80),
    "C": (520, 400, 200, 80)
}
hand_stay_time = {}
STAY_CONFIRM_TIME = 3  # 3秒确认

# 新增：各选项手掌计数统计
option_hand_count = {
    "A": 0,
    "B": 0,
    "C": 0
}
# 保存每道题的计数结果
question_count_history = []


# ---------------------- 5. 核心函数 ----------------------
# 计算手掌中心点（取手腕和掌心区域的平均坐标）
def get_palm_center(hand_landmarks):
    # 选取手腕(0)、食指根部(5)、中指根部(9)、无名指根部(13)、小指根部(17)计算中心
    landmarks_to_use = [0, 5, 9, 13, 17]
    x_sum = 0
    y_sum = 0
    for idx in landmarks_to_use:
        x_sum += hand_landmarks.landmark[idx].x
        y_sum += hand_landmarks.landmark[idx].y
    # 计算平均值并转换为屏幕坐标
    x = int((x_sum / len(landmarks_to_use)) * WIDTH)
    y = int((y_sum / len(landmarks_to_use)) * HEIGHT)
    return (x, y)


# 绘制手掌中心点
def draw_palm_center(screen, palm_center):
    x, y = palm_center
    # 绘制实心圆点（加外框更醒目）
    pygame.draw.circle(screen, (0, 150, 0, 255), (x, y), HAND_DOT_SIZE + 2)  # 外框
    pygame.draw.circle(screen, HAND_DOT_COLOR, (x, y), HAND_DOT_SIZE)  # 实心圆


# 统计各选项内的手掌数量
def count_hands_in_options(palm_centers):
    global option_hand_count
    # 重置计数
    option_hand_count = {"A": 0, "B": 0, "C": 0}
    # 遍历所有手掌中心点，统计各选项内数量
    for center in palm_centers:
        for key, area in option_areas.items():
            x1, y1, w, h = area
            x, y = center
            if x1 < x < x1 + w and y1 < y < y1 + h:
                option_hand_count[key] += 1
                break  # 一个手掌只算入一个选项


# 绘制优化后的答题界面（包含手掌计数）
def draw_interface(transparent_surf, question, options, left_time, score, hand_count):
    # 清空透明层
    transparent_surf.fill((0, 0, 0, 0))

    # 1. 绘制背景（柔和的半透明白色）
    pygame.draw.rect(transparent_surf, WHITE, (0, 0, WIDTH, HEIGHT))

    # 2. 绘制标题
    title_text = font_title.render("校园体测运动智慧答题", True, BLUE)
    title_rect = title_text.get_rect(center=(WIDTH // 2, 40))
    transparent_surf.blit(title_text, title_rect)

    # 3. 绘制题目（自动换行适配长文本）
    q_text = font_question.render(question, True, BLACK)
    q_rect = q_text.get_rect(center=(WIDTH // 2, 150))
    transparent_surf.blit(q_text, q_rect)

    # 4. 绘制计时和得分（右上角和左上角）
    # 倒计时（<5秒变红）
    time_color = RED if left_time <= 5 else BLACK
    time_text = font_info.render(f"剩余时间：{int(left_time)}秒", True, time_color)
    transparent_surf.blit(time_text, (WIDTH - 250, 90))

    # 得分
    score_text = font_info.render(f"当前得分：{score}", True, GREEN)
    transparent_surf.blit(score_text, (80, 90))

    # 5. 绘制选项（带背景色+实时计数）
    for opt in options:
        key = opt[0]
        x, y, w, h = option_areas[key]

        # 绘制选项背景和边框
        pygame.draw.rect(transparent_surf, LIGHT_BLUE, (x, y, w, h))
        pygame.draw.rect(transparent_surf, BLUE, (x, y, w, h), 3)

        # 绘制选项文字（居中）
        opt_text = font_option.render(opt, True, BLACK)
        opt_rect = opt_text.get_rect(center=(x + w // 2, y + h // 2 - 10))
        transparent_surf.blit(opt_text, opt_rect)

        # 绘制选项内手掌计数（右下角）
        count_text = font_count.render(f"人数：{hand_count[key]}", True, COUNT_COLOR)
        count_rect = count_text.get_rect(bottomright=(x + w - 10, y + h - 5))
        transparent_surf.blit(count_text, count_rect)


# 检测手掌中心点是否在选项区域（用于答题确认）
def is_palm_in_option(palm_center, option_area):
    x1, y1, w, h = option_area
    x, y = palm_center
    return x1 < x < x1 + w and y1 < y < y1 + h


# 判定答案
def check_answer(select_key, correct_key):
    global score
    if select_key == correct_key:
        score += 1
        return "答对啦！🎉"
    else:
        return f"答错了😟，正确答案是{correct_key}"


# 绘制最终计数统计结果
def draw_final_count(transparent_surf, count_history):
    transparent_surf.fill((0, 0, 0, 0))
    # 标题
    title_text = font_title.render("各选项手掌计数统计", True, BLUE)
    title_rect = title_text.get_rect(center=(WIDTH // 2, 60))
    transparent_surf.blit(title_text, title_rect)

    y_offset = 120
    # 遍历每道题的计数结果
    for idx, (q_idx, counts) in enumerate(count_history):
        # 题目编号
        q_text = font_info.render(f"第{q_idx + 1}题：", True, BLACK)
        transparent_surf.blit(q_text, (100, y_offset))

        # 各选项计数
        a_text = font_info.render(f"A：{counts['A']}个", True, COUNT_COLOR)
        b_text = font_info.render(f"B：{counts['B']}个", True, COUNT_COLOR)
        c_text = font_info.render(f"C：{counts['C']}个", True, COUNT_COLOR)

        transparent_surf.blit(a_text, (250, y_offset))
        transparent_surf.blit(b_text, (380, y_offset))
        transparent_surf.blit(c_text, (510, y_offset))

        y_offset += 50

    # 总分
    score_text = font_question.render(f"最终得分：{score}/{len(QUESTIONS)}", True, GREEN)
    score_rect = score_text.get_rect(center=(WIDTH // 2, y_offset + 30))
    transparent_surf.blit(score_text, score_rect)

    return transparent_surf


# ---------------------- 6. 主程序循环 ----------------------
cap = cv2.VideoCapture(0)
running = True
show_result = False
result_text = ""
result_show_time = 0
all_palm_centers = []  # 存储所有检测到的手掌中心点

while running:
    ret, frame = cap.read()
    if not ret:
        break
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    # 处理Pygame事件
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 1. 清空主窗口
    screen.fill((245, 245, 245))  # 浅灰色背景更护眼

    # 2. 检测并绘制所有手掌中心点
    all_palm_centers = []
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            palm_center = get_palm_center(hand_landmarks)
            all_palm_centers.append(palm_center)
            draw_palm_center(screen, palm_center)

    # 3. 统计各选项内的手掌数量
    count_hands_in_options(all_palm_centers)

    if not show_result:
        # 计时逻辑
        if start_time == 0:
            start_time = time.time()
        left_time = max(0, question_time - (time.time() - start_time))

        # 超时判定
        if left_time <= 0:
            # 保存当前题目的计数结果
            question_count_history.append((current_question, option_hand_count.copy()))
            result_text = f"时间到啦😟，正确答案是{QUESTIONS[current_question]['answer']}"
            show_result = True
            result_show_time = time.time()
            start_time = 0

        # 手掌停留判定（取第一个手掌作为答题确认）
        current_in_options = []
        if all_palm_centers:
            # 取第一个检测到的手掌作为答题依据
            main_palm = all_palm_centers[0]
            for key, area in option_areas.items():
                if is_palm_in_option(main_palm, area):
                    current_in_options.append(key)
                    if key not in hand_stay_time:
                        hand_stay_time[key] = time.time()
                    # 3秒确认选择
                    elif time.time() - hand_stay_time[key] >= STAY_CONFIRM_TIME:
                        # 保存当前题目的计数结果
                        question_count_history.append((current_question, option_hand_count.copy()))
                        result_text = check_answer(key, QUESTIONS[current_question]['answer'])
                        show_result = True
                        result_show_time = time.time()
                        start_time = 0
                        hand_stay_time.clear()
                        break

        # 清空无手掌的停留计时
        for key in list(hand_stay_time.keys()):
            if key not in current_in_options:
                del hand_stay_time[key]

        # 4. 绘制答题界面（包含实时计数）
        q = QUESTIONS[current_question]
        draw_interface(transparent_surface, q["question"], q["options"], left_time, score, option_hand_count)
        screen.blit(transparent_surface, (0, 0))
    else:
        # 显示答题结果
        transparent_surface.fill((0, 0, 0, 0))

        # 结果文字居中
        res_text = font_question.render(result_text, True, BLACK)
        res_rect = res_text.get_rect(center=(WIDTH // 2, 250))
        transparent_surface.blit(res_text, res_rect)

        # 得分文字居中
        score_text = font_info.render(f"当前得分：{score}/{current_question + 1}", True, GREEN)
        score_rect = score_text.get_rect(center=(WIDTH // 2, 320))
        transparent_surface.blit(score_text, score_rect)

        screen.blit(transparent_surface, (0, 0))

        # 3秒后切换题目
        if time.time() - result_show_time >= 3:
            show_result = False
            current_question += 1
            # 答题结束 - 显示最终计数统计
            if current_question >= len(QUESTIONS):
                # 绘制最终统计结果
                draw_final_count(transparent_surface, question_count_history)
                screen.blit(transparent_surface, (0, 0))
                pygame.display.update()
                # 显示10秒后退出
                pygame.time.wait(10000)
                running = False
            hand_stay_time.clear()

    # 更新窗口
    pygame.display.update()
    clock.tick(30)

# 释放资源
cap.release()
cv2.destroyAllWindows()
pygame.quit()