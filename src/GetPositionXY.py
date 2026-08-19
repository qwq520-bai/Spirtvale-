# ============================
# 屏幕和人物位置配置
# ============================

# 屏幕宽度
SCREEN_WIDTH=1920

# 屏幕高度
SCREEN_HEIGHT=1080

# 人物在屏幕上的 X 坐标，这里假设在屏幕正中间
CHARACTER_X=SCREEN_WIDTH//2

# 人物在屏幕上的 Y 坐标
CHARACTER_Y=SCREEN_HEIGHT//2


# ============================
# 目标类别配置
# ============================

# 需要当作怪物的类别名字
TARGET_NAMES = {
    "Orc Warlock",
    "Orc Crusher",
    "Giant Orc Reaver",
    "Orc Reaver",
    "Giant Orc Warlock",
    "Giant Orc Crusher",
}

# 即使模型识别出来，也不能当作目标的类别
# player 不是怪物，即使模型识别到也直接排除
IGNORE_NAMES = {
    "player",
}


# ============================
# 找最近目标
# ============================

def get_nearest_target(result):
    # 这一帧里识别到的所有目标框
    boxes=result.boxes

    # 如果没有检测框，直接返回 None
    if boxes is None:
        return None

    # 用来保存符合条件的怪物
    candidates=[]

    # 逐个检查识别框
    for box in boxes:
        # 类别编号
        class_id=int(box.cls[0])

        # 置信度
        confidence=float(box.conf[0])

        # 类别名字
        class_name=result.names.get(class_id,"")

        # 排除 player
        if class_name in IGNORE_NAMES:
            continue

        # 只保留目标名单里的怪，并且置信度不能太低
        if class_name not in TARGET_NAMES or confidence<0.45:
            continue

        # 目标框坐标：左上角和右下角
        x1, y1, x2, y2 = box.xyxy[0].tolist()

        # 目标中心 X
        target_cx = (x1 + x2) / 2

        # 目标中心 Y
        target_cy = (y1 + y2) / 2

        # 计算目标中心和人物位置的横向差
        dx = target_cx - CHARACTER_X

        # 计算目标中心和人物位置的纵向差
        dy = target_cy - CHARACTER_Y

        # 使用勾股定理计算直线距离
        distance = (dx ** 2 + dy ** 2) ** 0.5

        # 把距离、目标坐标放进候选列表
        candidates.append((distance, target_cx, target_cy))

    # 如果这帧没有怪物，返回 None
    if not candidates:
        return None

    # 按距离从小到大排序
    candidates.sort(key=lambda item:item[0])

    # 第一个就是最近目标
    nearest = candidates[0]

    # 拆开距离和坐标
    distance, target_cx, target_cy = nearest

    # 返回目标中心坐标
    return target_cx, target_cy
# ============================
# 复活框位置
# ============================
def find_class_center(result, class_name, conf_threshold=0.45):
    boxes = result.boxes
    if boxes is None:
        return None

    best = None
    for box in boxes:
        class_id = int(box.cls[0])
        confidence = float(box.conf[0])
        name = result.names.get(class_id, "")

        if name != class_name or confidence < conf_threshold:
            continue

        x1, y1, x2, y2 = box.xyxy[0].tolist()
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2

        if best is None or confidence > best[0]:
            best = (confidence, cx, cy)

    if best is None:
        return None

    return best[1], best[2]
#检测是否死亡
def has_class(result, class_name, conf_threshold=0.45):
    boxes = result.boxes
    if boxes is None:
        return False

    for box in boxes:
        class_id = int(box.cls[0])
        confidence = float(box.conf[0])
        name = result.names.get(class_id, "")

        if name == class_name and confidence >= conf_threshold:
            return True

    return False
