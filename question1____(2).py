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

#
# def merge_adjacent_spaces(candidate_positions, box):
#     merged = []
#     for pos in sorted(candidate_positions, key=lambda p: (p[2], p[1], p[0])):
#         x,y,z = pos[0]
#         merged_flag = False
#         for m in merged:
#             mx,my,mz = m
#             if my == y and mz == z and mx + 1 == x:
#                 merged.remove(m)
#                 merged.append((mx, my, mz))
#                 merged_flag = True
#                 break
#             # 纵向合并（y轴方向）
#             if mx == x and mz == z and my + 1 == y:
#                 merged.remove(m)
#                 merged.append((x, my, mz))
#                 merged_flag = True
#                 break
#             # 高度合并（z轴方向）
#             if mx == x and my == y and mz + 1 == z:
#                 merged.remove(m)
#                 merged.append((x, y, mz))
#                 merged_flag = True
#                 break
#         if not merged_flag:
#             merged.append(pos)
#     return merged

#
# def try_rearrange(placed_items, box):
#     """局部重排：尝试调整已放置物体的位置或旋转方向"""
#     for i in range(len(placed_items)):
#         item = placed_items[i]
#         # 生成所有可能的旋转
#         rotations = sorted(item['item'].generate_rotations(),
#                            key=lambda d: d[0] * d[1] * d[2], reverse=True)
#         for (new_l, new_w, new_h) in rotations:
#             # 尝试新方向是否更优
#             if (new_l <= item.orientations[0] and new_w <= item.orientations[1] and new_h <= item.orientations[2]):
#                 continue  # 跳过更差方向
#             # 临时移除当前物体
#             temp_placed = [p for p in placed_items if p != item]
#             # 检查新方向是否能放入原位置
#             x, y, z = item.positions
#             if x + new_l > box.l or y + new_w > box.w or z + new_h > box.h:
#                 continue
#             # 检查与其他物体是否重叠
#             overlap = False
#             for p in temp_placed:
#                 px, py, pz = p.positions
#                 pl, pw, ph = p.orientations
#                 if not (x + new_l <= px or x >= px + pl or
#                         y + new_w <= py or y >= py + pw or
#                         z + new_h <= pz or z >= pz + ph):
#                     overlap = True
#                     break
#             if not overlap:
#                 # 更新方向和候选位置
#                 item.orientations = (new_l, new_w, new_h)
#                 return True
#     return False



def greedy_pack(items, boxes):
    items, boxes = preprocess_order(items, boxes)
    boxes_sorted = sorted(boxes, key=lambda b: b.volume)
    boxes_sorted = [x for x in boxes_sorted if x.volume > sum([item.volume for item in items])]
    items_sorted = sorted(items, key=lambda x: x.volume, reverse=True)

    def merge_regions(regions):
        merged = []
        for r in sorted(regions, key=lambda x: (x[2], x[1], x[0])):
            x, y, z, l, w, h = r
            found = False
            for i in range(len(merged)):
                mx, my, mz, ml, mw, mh = merged[i]
                # 合并垂直方向(Z轴)相同且XY面重叠的区域
                if z == mz and h == mh:
                    if (x == mx and l == ml and (y == my + mw or my == y + w)):
                        new_w = max(y + w, my + mw) - min(y, my)
                        merged[i] = (x, min(y, my), z, l, new_w, h)
                        found = True
                        break
                    if (y == my and w == mw and (x == mx + ml or mx == x + l)):
                        new_l = max(x + l, mx + ml) - min(x, mx)
                        merged[i] = (min(x, mx), y, z, new_l, w, h)
                        found = True
                        break
            if not found:
                merged.append(r)
        return merged

    for box in boxes_sorted:
        box.placed_items = []
        box.available_regions = [(0, 0, 0, box.l, box.w, box.h)]  # (x, y, z, l, w, h)

        all_placed = True
        for item in items_sorted:
            best_position = None
            best_orientation = None
            remaining_space = float('inf')

            # 生成所有可能方向并按底面积排序
            orientations = sorted(item.generate_orientations(),
                                key=lambda dim: (-dim[0]*dim[1], -dim[2]))

            for (l, w, h) in orientations:
                for i, region in enumerate(box.available_regions):
                    rx, ry, rz, rl, rw, rh = region
                    if l > rl or w > rw or h > rh:
                        continue

                    # 优先选择空间利用率更高的位置
                    current_space = (rl - l) * (rw - w) * (rh - h)
                    if current_space < remaining_space:
                        remaining_space = current_space
                        best_position = (rx, ry, rz, i)
                        best_orientation = (l, w, h)

            if best_position:
                x, y, z, region_idx = best_position
                l, w, h = best_orientation
                region = box.available_regions.pop(region_idx)
                rx, ry, rz, rl, rw, rh = region

                # 添加分割后的新区域
                new_regions = []
                if rl - l > 0:  # 右侧剩余空间
                    new_regions.append((x + l, y, z, rl - l, w, rh))
                if rw - w > 0:  # 前方剩余空间
                    new_regions.append((x, y + w, z, l, rw - w, rh))
                if rh - h > 0:  # 上方剩余空间
                    new_regions.append((x, y, z + h, l, w, rh - h))

                # 合并相邻空间
                box.available_regions += new_regions
                box.available_regions = merge_regions(box.available_regions)

                # 记录物品位置
                item.positions = (x, y, z)
                item.orientations = (l, w, h)
                box.placed_items.append(item)
            else:
                all_placed = False
                break

        if all_placed:
            used_volume = sum(x.volume for x in box.placed_items)
            utilization = used_volume / box.volume * 100
            return box, utilization
    return None, 0

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
    print(f"选择的箱子编号: {chosen_box.id}, 箱子的容量: {chosen_box.volume}, 已放入的商品数量: {len(chosen_box.placed_items)},utilization: {utilization:.2f}%")


