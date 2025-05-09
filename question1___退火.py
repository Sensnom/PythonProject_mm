import itertools
import math
import random
import pandas as pd
import numpy as np
# random.seed(247555)

data = pd.read_excel('附件2-商品尺寸.xlsx')

"""
基于模拟退火算法的三维装箱优化方案
核心功能：通过模拟退火算法优化物品装箱顺序和方向，提高容器空间利用率
"""

# 读取数据
# 预处理原始数据，分离常温/冷冻物品
common_item = data[data['TL']=='常温']  # 从原始数据筛选常温物品
cold_item = data[data['TL']=='冷冻']    # 从原始数据筛选冷冻物品

class Item:
    """物品类，封装物品属性和放置信息"""
    def __init__(self, l, w, h, is_frozen):
        self.dims = (l, w, h)       # 物品原始尺寸（长宽高）
        self.is_frozen = is_frozen  # 是否冷冻物品标志
        self.volume = l * w * h     # 计算物品体积
        self.orientation = (l,w,h)   # 当前放置方向（尺寸排列组合）
        self.position = (0, 0, 0)     # 在容器中的坐标(x,y,z)

    def get_current_size(self):
        """获取物品当前方向的实际尺寸"""
        return self.orientation

class Box:
    """容器类，描述装箱容器属性及装载状态"""
    def __init__(self, id, l, w, h, is_used_for_frozen):
        self.id = id                # 容器唯一标识
        self.dims = (l, w, h)       # 容器尺寸（长宽高）
        self.volume = l * w * h     # 容器总容积
        self.is_used_for_frozen = is_used_for_frozen  # 是否冷冻专用容器
        self.used_space = []        # 已装载物品信息列表

def preprocess_order(items, boxes):
    """订单预处理逻辑：冷冻订单添加冰块并过滤容器"""
    if items[0].is_frozen:
        # 添加两个标准尺寸的冰块（15*11*2.5cm）
        items += [Item(15, 11, 2.5, True) for _ in range(2)]
        # 筛选适合冷冻物品的容器
        boxes = [b for b in boxes if b.is_used_for_frozen]
    else:
        # 筛选非冷冻容器
        boxes = [b for b in boxes if not b.is_used_for_frozen]
    return items, boxes


# 相邻空间合并策略
def merge_space(free_regions):
    pass

def block_merge(items):
    pass


def check_overlap(pos1, dims1, pos2, dims2):
    """检查两个物品是否重叠"""
    x1, y1, z1 = pos1
    w1, h1, d1 = dims1
    x2, y2, z2 = pos2
    w2, h2, d2 = dims2
    x_overlap =x2<x1+w1 if x1<=x2  else x1<x2+w2
    y_overlap = y2<y1+h1 if y1<=y2 else y1<y2+h2
    z_overlap = z2<z1+d1 if z1<=z2 else z1<z2+d2
    return x_overlap and y_overlap and z_overlap


def layout_items(items, box):
    """核心装箱布局算法（带空间分割策略）"""
    if not box:
        return
    box.used_space = []  # 重置容器装载状态
    # 初始化可用区域列表，起始为整个容器空间
    free_regions = [{'pos': (0,0,0), 'dims': box.dims}]

    for item in items:  # 遍历所有待装物品
        placed = False  # 物品放置状态标记
        # 按空间利用率和最大尺寸排序可用区域（优先选择大且紧凑的空间）
        free_regions.sort(key=lambda r: (r['dims'][0]*r['dims'][1]*r['dims'][2],  # 区域体积降序
            -max(r['dims'])  # 最大尺寸升序（优先较小最大尺寸）优先选择最大尺寸较小的区域，因为较小的最大尺寸意味着区域更紧凑，更有可能成功放置物品。
        ))

        # 遍历所有可用区域尝试放置
        for i, region in enumerate(free_regions):
            r_pos = region['pos']  # 区域起始坐标
            r_dims = region['dims']  # 区域尺寸


            # 生成物品所有可能方向，并按底面积和高度排序（优先大底面积方向）
            for dim in sorted(itertools.permutations(item.dims),
                              key=lambda d: (-d[0] * d[1], d[2])):  # 优先选择底面积大的方向
                # 检查当前方向是否适合当前区域
                # 检查是否与已放置的物品重叠
                overlap = False
                for used_item in box.used_space:
                    if check_overlap(r_pos, dim, used_item['pos'], used_item['dims']):
                        overlap = True
                        break

                if overlap:
                    continue

                if all(d <= rd for d, rd in zip(dim, r_dims)):
                    # 记录物品放置信息
                    new_pos = (
                        r_pos[0],
                        r_pos[1],
                        r_pos[2]
                    )


                    item.position = new_pos
                    item.orientation = dim

                    box.used_space.append({
                        'pos': new_pos,
                        'dims': dim,
                        'item': item
                    })

                    # 空间分割处理
                    new_regions = []

                                        # X方向剩余空间
                    if r_dims[0] - dim[0] > 0:
                        new_regions.append({
                            'pos': (r_pos[0] + dim[0], r_pos[1], r_pos[2]),
                            'dims': (r_dims[0] - dim[0], r_dims[1], r_dims[2])
                        })

                    # Y方向剩余空间
                    if r_dims[1] - dim[1] > 0:
                        new_regions.append({
                            'pos': (r_pos[0], r_pos[1] + dim[1], r_pos[2]),
                            'dims': (r_dims[0], r_dims[1] - dim[1], r_dims[2])
                        })

                    # Z方向剩余空间
                    if r_dims[2] - dim[2] > 0:
                        new_regions.append({
                            'pos': (r_pos[0], r_pos[1], r_pos[2] + dim[2]),
                            'dims': (r_dims[0], r_dims[1], r_dims[2] - dim[2])
                        })


                    # 更新可用区域列表
                    del free_regions[i]
                    # 过滤掉太小的区域，避免碎片化
                    min_volume = min(i.volume for i in items)
                    new_regions = [r for r in new_regions
                                   if r['dims'][0] * r['dims'][1] * r['dims'][2] >= min_volume]
                    free_regions.extend(new_regions)

                    placed = True
                    break

            if placed:
                break

        if not placed:
            box.used_space = []  # 重置容器装载状态
            return False  # 放置失败终止装箱

    return True  # 所有物品成功放置


def calculate_energy(box, items):
    """计算布局能量值（目标函数）"""
    used_volume = sum(i.volume for i in items)  # 已使用体积
    total_volume = box.volume  # 容器总容积


    # 紧凑度惩罚项（计算X，Y，Z轴方向最大延伸长度占比）
    max_coord_x = max(
        i.position[0] + i.orientation[0] for i in items
    ) if items else 0
    max_coord_y = max(
        i.position[1] + i.orientation[1] for i in items
    ) if items else 0
    max_coord_z = max(
        i.position[2] + i.orientation[2] for i in items
    ) if items else 0

    dim_fill_rate = max_coord_x / box.dims[0]* max_coord_y / box.dims[1]* max_coord_z / box.dims[2]
    # # 高度差惩罚项（计算物品高度差）
    # # 除了计算X，Y，Z轴方向最大延伸长度占比，还应该计算并选择能够最大程度减小高度差的放置方案，使得物品尽可能紧凑。
    # z_positions = [i.position[2]+i.orientation[2] for i in items]
    # z_positions_max = max(z_positions) if z_positions else 0
    # z_positions_min = min(z_positions) if z_positions else 0
    # z_positions_std = np.std(z_positions) if z_positions else 0
    #
    # # 稳定性惩罚项（计算物品稳定性）
    # # 避免除数为0的情况
    # range_z_positions = z_positions_max - z_positions_min if z_positions_max != z_positions_min else 1
    # # 归一化标准差
    # z_positions_std_normalized = z_positions_std / range_z_positions if range_z_positions > 0 else 0

    # 综合能量计算
    return (used_volume / total_volume) * 0.6  + dim_fill_rate * 0.4, box



def block_exchange(new_order, start, length, target):
    end = start + length
    temp = new_order[start:end]
    del new_order[start:end]
    new_order[target:target] = temp
    return new_order


def neighbor_generator(current_order, mutation_rate=0.5):
    """邻居状态生成器（混合变异策略）"""
    new_order = current_order.copy()  # 复制当前状态

    if random.random() < mutation_rate:
        # 单点变异：交换两个随机物品位置
        i, j = random.sample(range(len(new_order)), 2)
        new_order[i], new_order[j] = new_order[j], new_order[i]
    else:
        # 块变异：交换连续物品段（增强局部搜索能力）
        start = random.randint(0, len(new_order)-2)  # 随机起始位置
        length = random.randint(1, min(3, len(new_order)-start))  # 块长度1-3
        # 随机目标位置
        target = random.randint(0, len(new_order)-length)
        # 执行块交换
        new_order = block_exchange(new_order, start, length, target)


    return new_order

def simulated_annealing_pack(items, boxes, initial_temp=1000, cooling_rate=0.995, final_temp=1):
    """模拟退火主算法"""
    for i in items:
        i.position = (0, 0, 0)  # 重置物品位置信息
        i.orientation = (i.dims[0], i.dims[1], i.dims[2])
    # 选择最小可用容器（体积刚好满足物品总体积）
    boxes = sorted([b for b in boxes if b.volume >= sum(i.volume for i in items)],key=lambda x: x.volume)
    if not boxes:
        return None, None,0, 0  # 无可用容器直接返回
    # 初始化状态：按体积和最大尺寸降序排列
    current_order = sorted(items, key=lambda x: (-x.volume, -max(x.dims)))
    best_order = current_order.copy()  # 记录最佳状态
    best_energy = 0  # 最佳能量值
    current_temp = initial_temp  # 初始化温度
    smallest_box = None # 选择最小可用容器
    # 退火循环
    while current_temp > final_temp:
        # 生成邻居状态
        if random.random()*current_temp >0.5:
            new_order = neighbor_generator(current_order)
        else:
            new_order = current_order.copy()

        # 尝试新布局并计算能量
        for box in boxes:
            success = layout_items(new_order, box)
            if success:
                new_energy,new_box = calculate_energy(box, new_order)
                break
            else:
                new_energy = 0
                new_box = None

        for box in boxes:
            success = layout_items(current_order, box)
            if success:
                current_energy,current_box = calculate_energy(box, current_order)
                break
            else:
                current_energy = 0
                current_box = None

        if new_energy > current_energy:
            current_energy = new_energy
            current_order = new_order.copy()
            current_box = new_box

         # 计算接受新解的概率p，根据目标函数值的差异和当前温度T
        else:
            # 接受或拒绝邻居状态
            if math.exp((current_energy - new_energy) / current_temp) > random.random():
                current_energy = new_energy
                current_order = new_order.copy()
                current_box = new_box
            else:
                pass     # 接受失败，继续当前状态

        if current_energy > best_energy:
            best_energy = current_energy
            best_order = current_order.copy()
            smallest_box = current_box
        current_temp *= cooling_rate  # 温度衰减

    # 应用最佳布局方案
    if smallest_box:
        layout_items(best_order, smallest_box)
        used_volume = sum(i.volume for i in best_order)
        utilization = used_volume / smallest_box.volume * 100
        return smallest_box,best_order,used_volume, utilization  # 返回最优容器和利用率
    else:
        return None, None,0, 0  # 无可用容器直接返回


if __name__=='__main__':
    with open('box_inf.txt', 'r',encoding='utf-8') as f:
        lines = f.readlines()

    boxes = []
    items = []
    for line in lines:
        if line.strip()[3] == '纸':
            inf = line.strip().split(',')
            box = Box(inf[0].strip("'"),float(inf[1]),float(inf[2]),float(inf[3]),False)
        else:
            inf = line.strip().split(',')


            box = Box(inf[0].strip("'"),float(inf[1]),float(inf[2]),float(inf[3]),True)

        boxes.append(box)
    my_chosen = input("要选择冷冻物品还是常温的呢？（冷冻：0/常温：1）：")
    if my_chosen == '0':
        chosen_samples = random.sample(range(len(cold_item)), random.randint(4, 9))
        for i in chosen_samples:
            item = Item(float(cold_item.iloc[i]['L']), float(cold_item.iloc[i]['W']), float(cold_item.iloc[i]['H']), True)
            print(f"冷冻物品: {cold_item.iloc[i].to_string()}")
            items.append(item)
    elif my_chosen == '1':
        chosen_samples = random.sample(range(len(common_item)), random.randint(4, 9))
        for i in chosen_samples:
            item = Item(float(common_item.iloc[i]['L']), float(common_item.iloc[i]['W']), float(common_item.iloc[i]['H']), False)
            print(f"常规物品: {common_item.iloc[i].to_string()}")
            items.append(item)
    else:
        print("输入错误")
        exit()


    history = []
    items, boxes = preprocess_order(items, boxes)
    for _ in range(10):
        best_box,best_order,used_volume, utilization = simulated_annealing_pack(items, boxes)
        history.append((best_box,best_order,used_volume, utilization))
    history = sorted(history, key=lambda x: x[3], reverse=True)
    best_box,best_order,used_volume, utilization = history[0]
    if best_box:
        print("=="*50)
        print(f"最佳容器: {best_box.id},容器体积: {best_box.volume:.1f}cm^3,使用的体积: {used_volume:.1f}cm^3, 利用率: {utilization:.1f}%")
        print("物品放置顺序:")
        for i in best_order:
            print(f"尺寸: {i.get_current_size()} 位置: {i.position}")
    else:
        print("无可行解")
