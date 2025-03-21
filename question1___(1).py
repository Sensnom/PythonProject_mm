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
    # 定义一个贪心算法函数，用于将商品尽可能高效地放入包装箱中
    """贪心算法核心逻辑"""
    # 预处理：若为冷冻订单，添加两个冰块

    items, boxes = preprocess_order(items,boxes)


    # 按体积从小到大对包装箱进行排序，以便优先使用体积较小的包装箱
    boxes_sorted = sorted(boxes, key=lambda b: b.volume)
    boxes_sorted = [x for x in boxes_sorted if x.volume > sum([item.volume for item in items])]
    # 按体积从大到小对商品进行排序，以便优先放入体积较大的商品
    items_sorted = sorted(items, key=lambda x: x.volume, reverse=True)

    for box in boxes_sorted:
        for item in items_sorted:
            orientations = sorted(item.generate_orientations(),key=lambda x: (x[0],x[1],x[2]),reverse=True)

            for (l,w,h) in orientations:
                for pos in sorted(box.available_positions,key=lambda x: (x[2],x[1],x[0])):
                    x,y,z = pos
                    if x + l > box.l or y + w > box.w or z + h > box.h:
                        continue

                    overlap = False
                    for placed_item in box.placed_items:
                        px,py,pz = placed_item.positions
                        pl,pw,ph = placed_item.orientations
                        if not (x + l <= px or x >= px + pl or
                                y + w <= py or y >= py + pw or
                                z + h <= pz or z >= pz + ph):
                            overlap = True
                            break

                    if not overlap:
                        item.positions = (x,y,z)
                        item.orientations = (l,w,h)
                        box.placed_items.append(item)

                        box.available_positions.remove(pos)

                        new_available_positions=[]
                        if x + l <= box.l: new_available_positions.append((x + l, y, z))
                        if y + w <= box.w: new_available_positions.append((x, y + w, z))
                        if z + h <= box.h: new_available_positions.append((x, y, z + h))

                        box.available_positions.extend(new_available_positions)
                        box.available_positions = sorted(list(set(box.available_positions)), key=lambda x : (x[2],x[1],x[0]))

                        item.is_placed = True
                        break
                if item.is_placed:
                    break

            if not item.is_placed:
                box.is_available = False
                break

        if box.is_available:
            used_volume = sum(x.volume for x in box.placed_items)
            utilization = used_volume / box.volume * 100
            return box, utilization
    return None, 0,0

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
    for i in range(8):
        if data.iloc[i]['TL'] == '冷冻':
            item = Item(float(data.iloc[i]['L']), float(data.iloc[i]['W']), float(data.iloc[i]['H']), True)
        else:
            item = Item(float(data.iloc[i]['L']), float(data.iloc[i]['W']), float(data.iloc[i]['H']), False)

        items.append(item)

    chosen_box, utilization = greedy_pack(items, boxs)
    print(f"选择的箱子编号: {chosen_box.id}, 箱子的容量: {chosen_box.volume}, 已放入的商品数量: {len(chosen_box.placed_items)},utilization: {utilization:.2f}%")


