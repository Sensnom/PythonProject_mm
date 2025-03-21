import csv
import random
import copy
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor


# ----------------------
# 基础数据结构定义
# ----------------------
class Item:
    def __init__(self, item_code: str, l: float, w: float, h: float, num: int, is_frozen: bool = False):
        self.item_code = item_code
        self.l = l
        self.w = w
        self.h = h
        self.num = num
        self.is_frozen = is_frozen
        self.volume = l * w * h

    def generate_rotations(self) -> list:
        """生成优化的三维旋转方向（3种主方向）"""
        base_rotations = [
            (self.l, self.w, self.h),
            (self.w, self.h, self.l),
            (self.h, self.l, self.w)
        ]
        # 去重逻辑（处理立方体等特殊情况）
        seen = set()
        unique = []
        for r in base_rotations:
            key = tuple(sorted(r))
            if key not in seen:
                seen.add(key)
                unique.append(r)
        return unique


class Box:
    def __init__(self, box_id: str, l: float, w: float, h: float):
        self.box_id = box_id
        self.l = l
        self.w = w
        self.h = h
        self.volume = l * w * h
        self.sorted_dims = sorted([l, w, h])


class Order:
    def __init__(self, order_code: str):
        self.order_code = order_code
        self.frozen_items = []
        self.normal_items = []


# ----------------------
# 核心算法模块
# ----------------------
class PackingOptimizer:
    def __init__(self, box_list: list, ice_dim: tuple = (10, 10, 10)):
        """
        :param box_list: 包装箱规格列表，按体积升序排列
        :param ice_dim: 冰块尺寸 (长,宽,高)
        """
        self.boxes = sorted([Box(b['box_id'], b['l'], b['w'], b['h']) for b in box_list],
                            key=lambda x: x.volume)
        self.ice_item = Item("ICE", *ice_dim, 1, is_frozen=True)

    def load_orders_from_csv(self, file_path: str) -> dict:
        """从CSV加载订单数据（格式：Order_Code,Item_Code,Num,TL）"""
        orders = defaultdict(Order)
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                order = orders[row['Order_Code']]
                item = self._get_item_spec(row['Item_Code'])  # 需实现商品规格查询
                item.num = int(row['Num'])
                if row['TL'].strip() in ["冷冻", "冷藏"]:
                    order.frozen_items.append(item)
                else:
                    order.normal_items.append(item)
        return orders

    def optimize_order(self, order: Order) -> dict:
        """处理单个订单的优化"""
        # 并行处理冷冻/常温分箱
        with ThreadPoolExecutor(max_workers=2) as executor:
            frozen_future = executor.submit(
                self._optimize_single_box,
                order.frozen_items + [copy.deepcopy(self.ice_item)] * 2,  # 添加冰块
                "frozen"
            )
            normal_future = executor.submit(
                self._optimize_single_box,
                order.normal_items,
                "normal"
            )
            return {
                "frozen": frozen_future.result(),
                "normal": normal_future.result()
            }

    def _optimize_single_box(self, items: list, box_type: str) -> dict:
        """单箱优化核心算法"""
        # 生成所有物品实例（展开数量）
        expanded_items = []
        for item in items:
            for _ in range(item.num):
                new_item = copy.deepcopy(item)
                new_item.num = 1
                expanded_items.append(new_item)

        # 优化排序策略：按体积降序+底面积优先
        sorted_items = sorted(expanded_items,
                              key=lambda x: (-x.volume, -max(r[0] * r[1] for r in x.generate_rotations()))

        best_solution = None
        for box in self.boxes:
            if
        self._try_packing(sorted_items, box): \
            best_solution = self._calc_utilization(box, sorted_items)
        break  # 选择第一个可行的最小箱
        return best_solution or {"status": "fail"}

    def _try_packing(self, items: list, box: Box) -> bool:
        """贪心装箱尝试（带动态优化）"""
        # 初始化三维空间网格
        space_grid = [[[True for _ in range(box.h)]
                       for _ in range(box.w)]
                      for _ in range(box.l)]

        # 优化放置顺序
        for item in items:
            placed = False
            # 按底面积优先选择旋转方向
            rotations = sorted(item.generate_rotations(),
                               key=lambda r: (-r[0] * r[1], -r[2]))  # 底面积优先，高度次之
            for (l, w, h) in rotations:
                # 寻找可放置位置（从底层向上搜索）
                for x in range(box.l - l + 1):
                    for y in range(box.w - w + 1):
                        z = self._find_z_position(space_grid, x, y, l, w, h)
                        if z is not None:
                            # 标记占用空间
                            for i in range(x, x + l):
                                for j in range(y, y + w):
                                    for k in range(z, z + h):
                                        space_grid[i][j][k] = False
                            placed = True
                            break
                    if placed: break
                if placed: break
            if not placed: return False
        return True

    def _find_z_position(self, grid, x, y, l, w, h) -> int:
        """寻找最低可用Z坐标"""
        max_z = len(grid[0][0]) - h
        for z in range(max_z + 1):
            if all(grid[i][j][k]
                   for i in range(x, x + l)
                   for j in range(y, y + w)
                   for k in range(z, z + h)):
                return z
        return None

    def _calc_utilization(self, box: Box, items: list) -> dict:
        """计算空间利用率"""
        total = sum(item.volume for item in items)
        return {
            "box_id": box.box_id,
            "utilization": total / box.volume * 100,
            "volume": box.volume
        }


# ----------------------
# 使用示例
# ----------------------
if __name__ == "__main__":
    # 初始化包装箱（示例数据）
    boxes = [
        {"box_id": "S", "l": 20, "w": 20, "h": 20},
        {"box_id": "M", "l": 25, "w": 25, "h": 25},
        {"box_id": "L", "l": 30, "w": 30, "h": 30}
    ]

    # 创建优化器
    optimizer = PackingOptimizer(boxes)

    # 加载订单数据
    orders = optimizer.load_orders_from_csv("orders.csv")

    # 处理所有订单
    results = {}
    for order_code, order in orders.items():
        results[order_code] = optimizer.optimize_order(order)

    # 打印结果
    for code, result in results.items():
        print(f"\n订单 {code} 结果:")
        print(f"冷冻箱: {result['frozen'].get('box_id', '无')} "
              f"利用率: {result['frozen'].get('utilization', 0):.1f}%")
        print(f"常温箱: {result['normal'].get('box_id', '无')} "
              f"利用率: {result['normal'].get('utilization', 0):.1f}%")