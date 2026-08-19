# ============================
# 导入模块
# ============================

# YOLO 模型
import os

# PyInstaller 成品没有 pip 元数据，禁止 Ultralytics 启动时误触发自动安装。
os.environ.setdefault("ULTRALYTICS_SKIP_REQUIREMENTS_CHECKS", "1")

from ultralytics import YOLO
try:
    import torch
    HAS_CUDA = bool(torch.cuda.is_available())
except Exception:
    HAS_CUDA = False
# 找最近目标的功能
import GetPositionXY
# 延时
import time
from pathlib import Path
# 键盘监听
from pynput import keyboard
# 鼠标控制
from pynput.mouse import Button,Controller
# 虚拟手柄控制
import vgamepad as vg
# 技能和热键控制
import KeyBoard
# 从 KeyBoard 里读取“近距离”距离
from KeyBoard import SKILLS_DISTANCE


# ============================
# 屏幕和人物位置配置
# ============================

# 屏幕宽高
SCREEN_WIDTH=1920
SCREEN_HEIGHT=1080

# 人物位置，默认在屏幕中心
CHARACTER_X=SCREEN_WIDTH//2
CHARACTER_Y=SCREEN_HEIGHT//2


# ============================
# 鼠标移动配置
# ============================

# 每隔多少秒允许点击移动一次
MOVE_CLICK_INTERVAL = 0.15

# YOLO 推理配置。
# 当前使用包含战斗、死亡和主城目标类别的完整模型。
PROJECT_ROOT = Path(__file__).resolve().parent
_MODEL_CANDIDATES = (
    PROJECT_ROOT / "spirt_three.pt",  # 打包版模型位置
    PROJECT_ROOT / "training_data" / "spirt_three.pt",  # 源码版模型位置
    PROJECT_ROOT.parent / "models" / "spirt_three.pt",  # 仓库版模型位置
)
MODEL_PATH = next((path for path in _MODEL_CANDIDATES if path.exists()), _MODEL_CANDIDATES[0])
PREDICT_CONF = 0.30
PREDICT_IMGSZ = 640
PREDICT_DEVICE = 0 if HAS_CUDA else "cpu"
PREDICT_MAX_DET = 20
PREDICT_QUANTIZE = 16 if HAS_CUDA else 32

# 点击位置相对于怪物中心的横向偏移
CLICK_OFFSET_X = -150

# 点击位置相对于怪物中心的纵向偏移
CLICK_OFFSET_Y = 100

# 鼠标控制器
mouse = Controller()

# 虚拟 Xbox 360 手柄
gamepad = vg.VX360Gamepad()

# 上一次移动时间
last_move_time = 0.0

# 如果游戏需要先按下右摇杆 R3 再转动，把这里改成 True
RIGHT_STICK_CLICK = True

# 没有目标超过多少秒后开始用手柄旋转视角
ROTATE_AFTER_SECONDS = 5

# 旋转方向，left 或 right
ROTATE_DIRECTION = "left"

# 每次手柄旋转持续多少秒
ROTATE_DURATION = 0.82

# 死亡 UI 防卡死参数。误识别死亡时，若 UI 内没有 town，就自动关闭 UI。
DEAD_CHECK_INTERVAL = 5.0
DEATH_UI_TIMEOUT = 2.0
DEATH_RETRY_COOLDOWN = 5.0

# 记录上一次没有目标的时间。
last_none_time = time.monotonic()
# 限制状态日志输出频率，避免终端每一帧刷屏。
last_status_log_time = 0.0
STATUS_LOG_INTERVAL = 1.0
# 死亡 UI 状态
death_ui_mode = False
death_ui_started_at = 0.0
last_dead_check_time = 0.0
dead_ignore_until = 0.0
# 手柄函数
def rotate_view_with_gamepad(direction="left", duration=0.8):
    """按住右摇杆指定时长旋转视角，并确保最后回中。"""
    if RIGHT_STICK_CLICK:
        gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB)

    x = -1.0 if direction == "left" else 1.0
    gamepad.right_joystick_float(x_value_float=x, y_value_float=0.0)
    gamepad.update()

    try:
        time.sleep(duration)
    finally:
        gamepad.right_joystick_float(x_value_float=0.0, y_value_float=0.0)
        if RIGHT_STICK_CLICK:
            gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB)
        gamepad.update()


def press_f11():
    """切换游戏 UI 显示状态。"""
    keyboard_controller = keyboard.Controller()
    keyboard_controller.press(keyboard.Key.f11)
    time.sleep(0.1)
    keyboard_controller.release(keyboard.Key.f11)


def handle_death():
    """显示死亡 UI，并启动 town 超时保护。"""
    global death_ui_mode, death_ui_started_at
    print("检测到死亡，按 F11 显示 UI")
    press_f11()
    death_ui_mode = True
    death_ui_started_at = time.monotonic()
    print("F11 已发送，等待 town")


# 加载训练好的模型
yolo = YOLO(str(MODEL_PATH))


def warm_up_model():
    """在等待 F6 时先完成一次推理，减少首次选目标的等待。"""
    # 权重放在脚本旁边或 runs 子目录时都能找到测试图。
    warmup_candidates = (
        Path(__file__).resolve().with_name("test.png"),
        MODEL_PATH.with_name("test.png"),
    )
    warmup_source = next((path for path in warmup_candidates if path.exists()), None)
    if warmup_source is None:
        return

    print("正在预热模型，完成后按 F6 可立即进入选目标")
    yolo.predict(
        source=str(warmup_source),
        conf=PREDICT_CONF,
        imgsz=PREDICT_IMGSZ,
        device=PREDICT_DEVICE,
        max_det=PREDICT_MAX_DET,
        quantize=PREDICT_QUANTIZE,
        verbose=False,
        save=False,
    )
    print("模型预热完成")


# ============================
# 热键监听
# ============================

warm_up_model()
listener = keyboard.Listener(on_press=KeyBoard.on_press)
listener.start()


# ============================
# 主循环
# ============================

try:
    # 只要没有按 F7，就保持外层循环
    while KeyBoard.running:
        # 等待 F6 运行
        while not KeyBoard.active and KeyBoard.running:
            time.sleep(0.05)

        # 如果在等待时按了 F7，就退出
        if not KeyBoard.running:
            break

        print("开始识别，按 F5 暂停，F7 退出")

        # 开始屏幕识别，不保存视频，显示识别窗口。
        results = yolo.predict(
            source="screen",
            save=False,
            show=False,
            stream=True,
            conf=PREDICT_CONF,
            imgsz=PREDICT_IMGSZ,
            device=PREDICT_DEVICE,
            max_det=PREDICT_MAX_DET,
            quantize=PREDICT_QUANTIZE,
            verbose=False,
        )

        # 逐帧处理屏幕识别结果
        for result in results:
            # 如果按了 F7 退出，或 F5 暂停，就停止当前识别循环
            if not KeyBoard.active or not KeyBoard.running:
                break

            now = time.monotonic()

            # F11 后先确认是否真的出现了 town。没有 town 通常是误触发死亡，
            # 到时自动关闭 UI，恢复原来的战斗识别。
            if death_ui_mode:
                town_center = GetPositionXY.find_class_center(
                    result,
                    "town",
                    conf_threshold=0.30,
                )
                if town_center is not None:
                    town_cx, town_cy = town_center
                    mouse.position = (int(town_cx), int(town_cy))
                    mouse.click(Button.left, 1)
                    print("检测到 town，已点击：", int(town_cx), int(town_cy))
                    death_ui_mode = False
                    dead_ignore_until = now + DEATH_RETRY_COOLDOWN
                    continue

                if now - death_ui_started_at >= DEATH_UI_TIMEOUT:
                    print(f"{DEATH_UI_TIMEOUT:.1f} 秒内未找到 town，关闭误触发 UI")
                    press_f11()
                    death_ui_mode = False
                    dead_ignore_until = now + DEATH_RETRY_COOLDOWN
                    last_none_time = now
                else:
                    continue

            # 死亡识别只负责触发一次 F11；短暂忽略 dead，防止关闭误触发 UI
            # 后同一帧再次把 UI 打开。
            if now >= dead_ignore_until and GetPositionXY.has_class(result, "dead"):
                if now - last_dead_check_time >= DEAD_CHECK_INTERVAL:
                    last_dead_check_time = now
                    handle_death()
                    continue

            # 找出离人物最近的怪物
            target = GetPositionXY.get_nearest_target(result)

            # 如果没有目标，继续下一帧
            if target is None:
                now = time.monotonic()
                if now - last_status_log_time >= STATUS_LOG_INTERVAL:
                    print("无目标")
                    last_status_log_time = now

                # 超过设定时间没有目标，就用手柄旋转视角
                if now - last_none_time >= ROTATE_AFTER_SECONDS:
                    print("用手柄旋转视角找怪")
                    rotate_view_with_gamepad(ROTATE_DIRECTION, ROTATE_DURATION)
                    last_none_time = time.monotonic()

                continue

            # 找到目标后重置无目标计时
            now = time.monotonic()
            last_none_time = now

            # 获取目标中心坐标
            target_cx, target_cy = target

            # 计算目标和人物之间的横向距离
            dx = target_cx - CHARACTER_X

            # 计算目标和人物之间的纵向距离
            dy = target_cy - CHARACTER_Y

            # 计算直线距离
            distance = (dx ** 2 + dy ** 2) ** 0.5

            # 限制目标坐标日志频率，避免影响实时控制。
            if now - last_status_log_time >= STATUS_LOG_INTERVAL:
                print(f"目标：({target_cx:.0f}, {target_cy:.0f}) 距离：{distance:.0f}")
                last_status_log_time = now

            # 根据距离释放技能
            KeyBoard.try_cast_skills(distance)

            # 释放技能的同时也继续移动
            if now - last_move_time >= MOVE_CLICK_INTERVAL:
                # 计算实际点击位置
                click_x = max(0, min(SCREEN_WIDTH - 1, int(target_cx + CLICK_OFFSET_X)))
                click_y = max(0, min(SCREEN_HEIGHT - 1, int(target_cy + CLICK_OFFSET_Y)))

                # 移动鼠标到点击位置
                mouse.position=(click_x, click_y)

                # 点击鼠标左键
                mouse.click(Button.left,1)

                # 记录本次移动时间
                last_move_time = time.monotonic()

# 不管怎么结束，最后都会执行清理
finally:
    # 松开一直按住的技能键
    KeyBoard.release_held_skills()

    # 复位虚拟手柄
    gamepad.reset()
    gamepad.update()

    # 关闭键盘监听
    listener.stop()
