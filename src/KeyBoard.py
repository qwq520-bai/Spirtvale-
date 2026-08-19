# ============================
# 导入需要的模块
# ============================

# pynput 用来监听和模拟键盘、鼠标
from pynput import keyboard

# time 用来做延时和冷却时间计算
import time


# ============================
# 启动和停止状态
# ============================

# 程序是否继续运行
running = True

# 是否已经按 F6 运行自动操作
active = False

# 启动阶段的按键间隔。数值越小，初始化越快；保留短暂间隔让游戏识别按键。
STARTUP_STEP_DELAY = 0.05
STARTUP_UI_DELAY = 0.1


# ============================
# 热键处理
# ============================

def start_automation():
    """执行 F6 的启动流程，供热键和复活传送完成后复用。"""
    global active

    # 启动按键完成前暂停识别循环，避免初始化按键和战斗逻辑同时执行。
    active = False
    print("运行")
    cast_skill("8")
    time.sleep(STARTUP_STEP_DELAY)
    cast_skill("r")
    time.sleep(2)
    cast_skill("0")
    time.sleep(2)
    cast_skill("p")

    # 启动时只执行一次 F11。
    time.sleep(STARTUP_UI_DELAY)
    cast_skill(keyboard.Key.f11)
    active = True


def on_press(key):
    global running, active

    # F6 运行
    if key == keyboard.Key.f6:
        start_automation()

        
    # F5 暂停
    elif key == keyboard.Key.f5:
        active = False
        print("暂停")

    # F7 退出程序
    elif key == keyboard.Key.f7:
        active = False
        running = False
        return False



# ============================
# 技能配置
# ============================

# 技能释放顺序
SKILL_KEYS = ["e", "1", "3", "4", "8", "r"]

# 每个技能的释放间隔，单位是秒
SKILL_INTERVAL={
    "e": 3.8,
    "1": 4,
    "3": 20,
    "4": 10,
    "8": 120,
    "r": 60
}

# 当前没有技能需要距离限制
CLOSE_RANGE_SKILLS=set()

# 多少距离以内算“靠近”
SKILLS_DISTANCE=250

# E 技能的前摇时间，前摇期间其他技能可能无效
E_FRONT_SWING = 0.1

# 1 技能连续点击间隔
KEY1_SPAM_INTERVAL = 0.08

# 4 技能连续点击间隔
KEY4_SPAM_INTERVAL = 0.12

# 8 和 R 每 60 秒同时释放一次
LONG_SKILL_INTERVAL = 60

# 记录每个技能上一次释放时间
last_skill_time={key:0.0 for key in SKILL_KEYS}

# 记录 8 和 R 上一次同时释放时间
last_long_skill_time = 0.0

# 用来模拟键盘按键
skill_keyboard = keyboard.Controller()

# E 释放后，下一个技能最早可以释放的时间
next_skill_time = 0.0

# ============================
# 判断技能是否能释放
# ============================

def can_cast_skill(key,distance): #检查近距离释放的技能，是否达到释放条件
    # 近距离技能必须离目标足够近
    if key in CLOSE_RANGE_SKILLS and distance >SKILLS_DISTANCE:
        return False

    # 1 技能如果还在 E 前摇时间内，暂时不能放
    if key == "1" and time.monotonic() < next_skill_time:
        return False

    # 检查技能是否已经过了冷却时间
    return time.monotonic() - last_skill_time[key] >= SKILL_INTERVAL[key]


# ============================
# 释放一个技能
# ============================

def cast_skill(key):  #释放技能
    global next_skill_time
    print("释放技能",key)

    # 按下技能键
    skill_keyboard.press(key)

    # 按住 0.05 秒，让游戏能识别到
    time.sleep(0.1)

    # 松开技能键
    skill_keyboard.release(key)

    # 记录本次释放时间，普通技能才记录
    if key in last_skill_time:
        last_skill_time[key] = time.monotonic()

    # 如果是 E，记录前摇结束时间
    if key == "e":
        next_skill_time = time.monotonic() + E_FRONT_SWING


# ============================
# 释放当前一直按住的技能
# ============================

def release_held_skills():
    try:
        skill_keyboard.release("4")
    except Exception:
        pass


# ============================
# 核心技能循环
# ============================

def try_cast_skills(distance):
    global last_long_skill_time

    # 1 技能一直释放，不检查距离和冷却
    if time.monotonic() - last_skill_time["1"] >= KEY1_SPAM_INTERVAL:
        cast_skill("1")

        # 每次释放 1 后，直接释放 E，不检查距离和冷却
        cast_skill("e")
        time.sleep(0.05)

    # 4 技能也一直释放，不检查距离和冷却
    # 游戏允许技能 1 释放期间继续放其他技能
    if time.monotonic() - last_skill_time["4"] >= KEY4_SPAM_INTERVAL:
        cast_skill("4")
        time.sleep(0.05)

    # 3 技能好了就放，不等其他技能
    if can_cast_skill("3", distance):
        cast_skill("3")
        time.sleep(0.05)

    # 8 和 R 每 60 秒同时释放一次
    if time.monotonic() - last_long_skill_time >= LONG_SKILL_INTERVAL:
        cast_skill("8")
        time.sleep(0.05)
        cast_skill("r")
        last_long_skill_time = time.monotonic()
