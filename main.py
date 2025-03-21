import itertools


class Item:
    def __init__(self, l, w, h, num, is_frozen=False):
        self.l = l
        self.w = w
        self.h = h
        self.num = num
        self.is_frozen = is_frozen

    def generate_rotations(self):
        """生成所有6种可能的尺寸旋转组合"""
        return list(set(itertools.permutations([self.l, self.w, self.h])))


class Box:
    def __init__(self, l, w, h, box_id):
        self.l = l
        self.w = w
        self.h = h
        self.volume = l * w * h
        self.box_id = box_id


def preprocess_order(items, is_frozen):
    """预处理：若为冷冻订单，添加两个冰块"""
    if is_frozen:
        ice = Item(10, 10, 10, 2, is_frozen=True)  # 假设冰块尺寸为10x10x10
        items.append(ice)
    return items

def greedy_pack(items, boxes):
    # 定义一个贪心算法函数，用于将商品尽可能高效地放入包装箱中
    """贪心算法核心逻辑"""

    # 按体积从小到大对包装箱进行排序，以便优先使用体积较小的包装箱
    boxes_sorted = sorted(boxes, key=lambda b: b.volume)

    # 按体积从大到小对商品进行排序，以便优先放入体积较大的商品
    items_sorted = sorted(items, key=lambda x: x.l * x.w * x.h, reverse=True)

    # 遍历排序后的每个包装箱
    for box in boxes_sorted:
        # 初始化候选位置列表，从(0, 0, 0)开始，按(z, y, x)升序排列
        candidate_positions = [(0, 0, 0)]

        # 初始化已放置商品的列表
        placed_items = []

        # 假设当前包装箱可以容纳所有商品，初始状态为可行
        feasible = True

        # 遍历排序后的每个商品
        for item in items_sorted:
            # 对于每个商品，处理其数量，即尝试将该商品的所有实例放入包装箱
            for _ in range(item.num):
                # 初始状态为商品未放置
                placed = False

                # 生成商品的所有旋转方式，并按体积从大到小排序，优先尝试体积较大的旋转方式
                rotations = sorted(item.generate_rotations(),
                                   key=lambda d: d[0] * d[1] * d[2], reverse=True)

                # 遍历所有可能的旋转方式
                for (l, w, h) in rotations:
                    # 遍历所有候选位置
                    for pos in sorted(candidate_positions, key=lambda p: (p[2], p[1], p[0])):
                        # 获取当前候选位置的坐标
                        x, y, z = pos

                        # 检查商品是否超出包装箱边界，如果超出，则跳过该位置
                        if x + l > box.l or y + w > box.w or z + h > box.h:
                            continue

                        # 初始化重叠状态为False
                        overlap = False

                        # 检查商品是否与已放置的商品重叠
                        for placed_item in placed_items:
                            # 获取已放置商品的位置和尺寸
                            px, py, pz = placed_item['pos']
                            pl, pw, ph = placed_item['dims']

                            # 如果商品与已放置的商品不重叠，则继续；否则标记重叠为True，并停止检查
                            if not (x + l <= px or x >= px + pl or
                                    y + w <= py or y >= py + pw or
                                    z + h <= pz or z >= pz + ph):
                                overlap = True
                                break

                        # 如果商品没有重叠，标记为已放置，并记录其位置和尺寸
                        if not overlap:
                            placed_items.append({
                                'pos': (x, y, z),
                                'dims': (l, w, h),
                                'item': item
                            })

                            # 移除当前已使用的候选位置
                            candidate_positions.remove(pos)

                            # 根据商品放置的位置和尺寸，添加新的候选位置
                            new_positions = []
                            if x + l <= box.l: new_positions.append((x + l, y, z))
                            if y + w <= box.w: new_positions.append((x, y + w, z))
                            if z + h <= box.h: new_positions.append((x, y, z + h))

                            # 更新候选位置列表，去除重复位置，并按(z, y, x)升序排列
                            candidate_positions += new_positions
                            candidate_positions = sorted(
                                list(set(candidate_positions)),
                                key=lambda p: (p[2], p[1], p[0])
                            )

                            # 标记当前商品已放置，并停止继续尝试其他旋转方式和位置
                            placed = True
                            break

                    # 如果商品已放置，停止继续尝试其他候选位置
                    if placed: break

                # 如果商品无法放置在当前包装箱中，标记当前包装箱为不可行，并停止继续尝试其他商品
                if not placed:
                    feasible = False
                    break

            # 如果当前包装箱不可行，停止继续尝试其他商品
            if not feasible: break

        # 如果当前包装箱可行，计算并返回空间利用率和商品放置信息
        if feasible:
            used_volume = sum(
                d['dims'][0] * d['dims'][1] * d['dims'][2]
                for d in placed_items
            )

            # 计算空间利用率，保留两位小数
            utilization = used_volume / box.volume * 100

            # 返回结果字典，包含包装箱ID、总体积、空间利用率和商品放置信息
            return {
                'box': box.bo_id,
                'volume': box.volume,
                'utilization': round(utilization, 2),
                'placements': placed_items
            }

    # 如果所有包装箱都无法容纳所有商品，返回None
    return None



# 示例测试
if __name__ == "__main__":
    # 定义商品和包装箱
    items = [
        Item(15, 10, 5, 2),
        Item(8, 8, 8, 3)
    ]
    boxes = [
        Box(20, 20, 20, "S"),
        Box(25, 15, 10, "M"),
        Box(30, 20, 15, "L")
    ]

    # 预处理订单（假设为常温订单）
    items = preprocess_order(items, is_frozen=False)

    # 执行算法
    result = greedy_pack(items, boxes)
    if result:
        print(f"最优包装箱: {result['box']}")
        print(f"箱体体积: {result['volume']} cm³")
        print(f"空间利用率: {result['utilization']}%")
        print("商品放置详情：")
        for idx, placement in enumerate(result['placements'], 1):
            print(f"商品{idx}: 位置{placement['pos']}, 尺寸{placement['dims']}")
    else:
        print("无可行解")
