import pandas as pd
import numpy as np
import itertools

data = pd.read_excel('附件2-商品尺寸.xlsx')
common_item = data[data['TL']=='常温']
cold_item = data[data['TL']=='冷冻']



class Item:
    # 定义一个名为 Box 的类，用于表示一个长方体盒子

    def __init__(self, l, w, h ,is_frozen,is_placed=False,orientations=None):
        # 定义类的构造函数，初始化盒子对象的属性。
        # 参数包括盒子的 id，长度（length），宽度（width），高度（height)。
        # 将传入的 id 赋值给盒子对象的 id 属性
        self.l = l
        # 将传入的长度赋值给盒子对象的 length 属性
        self.w = w
        # 将传入的宽度赋值给盒子对象的 width 属性
        self.h = h
        # 将传入的高度赋值给盒子对象的 height 属性
        self.is_frozen = is_frozen
        # 将传入的冷冻状态赋值给盒子对象的 is_frozen 属性
        self.volume = l * w * h
        # 计算盒子的体积并赋值给盒子对象的 volume 属性。注意，这里传入的 volume 参数实际上没有被使用，计算是基于 length, width, height 的。
        self.orientations =orientations
        # 调用 generate_orientations 方法，生成盒子的所有可能方向，并将结果赋值给 boxes 对象的 orientations 属性
        self.positions = (0,0,0)

        self.is_placed = is_placed
        # 定义一个 is_placed 属性，用于表示是否已经放置在某个容器中。默认值为 False。

    def generate_orientations(self):
        """生成所有6种可能的尺寸旋转组合"""
        return list(set(itertools.permutations([self.l, self.w, self.h])))



class Box:
    def __init__(self,id, l, w, h,is_used_for_frozen,available_positions):
        # 初始化 pack_space 类的实例，接收容器的 id、长度、宽度和高度作为参数
        self.id = id
        self.l = l  # 容器的长度
        self.w = w  # 容器的宽度
        self.h = h  # 容器的高度
        self.placed_items = []  # 用于存储已放入容器中的盒子列表
        self.volume = l * w * h  # 计算容器的总体积
        self.is_used_for_frozen = is_used_for_frozen  # 冷冻容器标志
        self.available_positions = available_positions
        self.is_available = True  # 容器可用性标志

def preprocess_order(items,boxs):
    """预处理：若为冷冻订单，添加两个冰块"""
    if items[0].is_frozen:
        ice1 = Item(15,11,2.5, True)
        ice2 = Item(15, 11, 2.5, True)
        items.append(ice1)
        items.append(ice2)
        boxs = [x for x in boxs if x.is_used_for_frozen]
    else:
        boxs = [x for x in boxs if not x.is_used_for_frozen]
    return items,boxs



def greedy_pack(items, boxes):
    """优化后的贪心装箱算法"""
    items, boxes = preprocess_order(items, boxes)

    # 按剩余空间潜力排序箱子（优先小体积且高瘦型）
    boxes_sorted = sorted(boxes,
        key=lambda b: (b.volume, -min(b.l, b.w, b.h)))
    boxes_sorted = [x for x in boxes_sorted
                   if x.volume >= sum(item.volume for item in items)]

    # 按体积和最大边长综合排序商品（优先大体积且立方体型）
    items_sorted = sorted(items,
        key=lambda x: (-x.volume, -max(x.l, x.w, x.h)))

    for box in boxes_sorted:
        # 初始化每个箱子的可用位置和已放置物品
        box.available_positions = [(0, 0, 0)]
        box.placed_items = []
        unplaced = items_sorted.copy()

        # 分层放置策略：优先填满低层再升高
        while unplaced:
            lowest_z = min(pos[2] for pos in box.available_positions)
            layer_positions = [pos for pos in box.available_positions
                              if pos[2] == lowest_z]

            # 在当前层选择最适合物品
            placed = False
            for pos in sorted(layer_positions,
                            key=lambda p: (p[1], p[0])):  # 优先靠前的y轴
                for item in list(unplaced):  # 改为直接遍历物品
                    # 生成所有可能方向，优先接近立方体的方向
                    orientations = sorted(item.generate_orientations(),
                        key=lambda dim: (-min(dim), -sum(dim)))

                    for (l, w, h) in orientations:
                        if (pos[0]+l <= box.l and
                            pos[1]+w <= box.w and
                            pos[2]+h <= box.h):

                            # 三维碰撞检测优化
                            collision = any(
                                pos[0] < placed_pos[0]+placed_l and
                                pos[0]+l > placed_pos[0] and
                                pos[1] < placed_pos[1]+placed_w and
                                pos[1]+w > placed_pos[1] and
                                pos[2] < placed_pos[2]+placed_h and
                                pos[2]+h > placed_pos[2]
                                for (placed_pos, (placed_l, placed_w, placed_h)) in
                                [(i.positions, i.orientations) for i in box.placed_items]
                            )

                            if not collision:
                                # 更新物品状态
                                item.positions = pos
                                item.orientations = (l, w, h)
                                box.placed_items.append(item)

                                # 移除已用空间，生成新候选位置
                                box.available_positions.remove(pos)
                                new_positions = [
                                    (pos[0]+l, pos[1], pos[2]),
                                    (pos[0], pos[1]+w, pos[2]),
                                    (pos[0], pos[1], pos[2]+h)
                                ]
                                box.available_positions += [
                                    p for p in new_positions
                                    if p[0] < box.l and p[1] < box.w and p[2] < box.h
                                ]

                                # 空间位置去重排序
                                box.available_positions = sorted(
                                    list(set(box.available_positions)),
                                    key=lambda x: (x[2], x[1], x[0])
                                )

                                unplaced.remove(item)  # 改为直接移除物品
                                placed = True
                                break
                        if placed: break
                    if placed: break
                if placed: break
            if not placed: break  # 当前层无法放置更多

        if not unplaced:
            utilization = sum(i.volume for i in box.placed_items) / box.volume * 100
            return box, round(utilization, 2)

    return None, 0

def check_collision(box, x, y, z, l, w, h):
    """改进的碰撞检测算法，考虑三维空间重叠"""
    for placed_item in box.placed_items:
        px, py, pz = placed_item.positions
        pl, pw, ph = placed_item.orientations
        if not (x + l <= px or x >= px + pl or
                y + w <= py or y >= py + pw or
                z + h <= pz or z >= pz + ph):
            return True
    return False


if __name__=='__main__':
    with open('box_inf.txt', 'r',encoding='utf-8') as f:
        lines = f.readlines()

    boxs = []
    items = []
    for line in lines:
        if line.strip()[3] == '纸':
            inf = line.strip().split(',')
            box = Box(inf[0].strip("'"),float(inf[1]),float(inf[2]),float(inf[3]),False,[(0,0,0)])
        else:
            inf = line.strip().split(',')
            box = Box(inf[0].strip("'"),float(inf[1]),float(inf[2]),float(inf[3]),True,[(0,0,0)])

        boxs.append(box)
    for i in range(5):
        if data.iloc[i]['TL'] == '冷冻':
            item = Item(float(data.iloc[i]['L']), float(data.iloc[i]['W']), float(data.iloc[i]['H']), True)
        else:
            item = Item(float(data.iloc[i]['L']), float(data.iloc[i]['W']), float(data.iloc[i]['H']), False)

        items.append(item)

    chosen_box, utilization = greedy_pack(items, boxs)
    print(f"选择的箱子编号: {chosen_box.id}, 箱子的容量: {chosen_box.volume}, 已放入的商品数量: {len(chosen_box.placed_items)},已放入的商品体积: {sum([item.volume for item in chosen_box.placed_items])}, 冷冻容器标志: {chosen_box.is_used_for_frozen},utilization: {utilization:.2f}%")





















# class Plane:
#     def __init__(self, x, y, z, length, width):
#         self.x = x
#         self.y = y
#         self.z = z
#         self.length = length
#         self.width = width
#
#     def can_place(self, box, orientation):
#         return orientation[0] <= self.length and orientation[1] <= self.width
#
# class Packing:
#     def __init__(self, container_length, container_width, container_height):
#         self.container_length = container_length
#         self.container_width = container_width
#         self.container_height = container_height
#         self.planes = [Plane(0, 0, 0, container_length, container_width)]
#         self.packing_list = []
#
#     def place_box(self, box):
#         best_plane = None
#         best_orientation = None
#         min_remaining_space = float('inf')
#
#         for orientation in box.orientations:
#             for plane in self.planes:
#                 if plane.can_place(box, orientation):
#                     remaining_space = self.calculate_remaining_space(plane, orientation)
#                     if remaining_space < min_remaining_space:
#                         min_remaining_space = remaining_space
#                         best_plane = plane
#                         best_orientation = orientation
#
#         if best_plane and best_orientation:
#             self.packing_list.append((box.id, best_plane.x, best_plane.y, best_plane.z, best_orientation))
#             self.update_planes(best_plane, best_orientation, box)
#             return True
#         return False
#
#     def calculate_remaining_space(self, plane, orientation):
#         return plane.length * plane.width - orientation[0] * orientation[1]
#
#     def update_planes(self, plane, orientation, box):
#         self.planes.remove(plane)
#         new_plane_z = plane.z + orientation[2]
#         if new_plane_z < self.container_height:
#             self.planes.append(Plane(plane.x, plane.y, new_plane_z, plane.length, plane.width))
#         # 添加其他可能的新平面，例如右侧和后侧平面
#         if orientation[0] < plane.length:
#             self.planes.append(Plane(plane.x + orientation[0], plane.y, plane.z, plane.length - orientation[0], plane.width))
#         if orientation[1] < plane.width:
#             self.planes.append(Plane(plane.x, plane.y + orientation[1], plane.z, plane.length, plane.width - orientation[1]))
#
#     def pack_boxes(self, boxes):
#         boxes.sort(key=lambda x: x.length * x.width * x.height, reverse=True)
#         for box in boxes:
#             if not self.place_box(box):
#                 print(f"Box {box.id} cannot be placed in the container.")
#         self.calculate_fill_rate()
#
#     def calculate_fill_rate(self):
#         total_volume = self.container_length * self.container_width * self.container_height
#         packed_volume = sum(box.length * box.width * box.height for box, _, _, _, _ in self.packing_list)
#         fill_rate = packed_volume / total_volume
#         print(f"Container fill rate: {fill_rate * 100:.2f}%")
#
# # Example usage
# if __name__ == "__main__":
#     # Define container dimensions
#     container_length = 10
#     container_width = 10
#     container_height = 10
#
#     # Define boxes
#     boxes = [
#         Box(1, 3, 2, 2),
#         Box(2, 2, 2, 2),
#         Box(3, 1, 1, 1)
#     ]
#
#     # Create packing instance
#     packing = Packing(container_length, container_width, container_height)
#
#     # Pack boxes
#     packing.pack_boxes(boxes)
#
#     # Print packing plan
#     print("Packing plan:")
#     for entry in packing.packing_list:
#         box_id, x, y, z, orientation = entry
#         print(f"Box {box_id} placed at ({x}, {y}, {z}) with orientation {orientation}")