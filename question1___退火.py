import itertools
import math
import random
import pandas as pd
import numpy as np

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
        self.orientation = None    # 当前放置方向（尺寸排列组合）
        self.position = None       # 在容器中的坐标(x,y,z)

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

def layout_items(items, box):
    """核心装箱布局算法（带空间分割策略）"""
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
            for dim in sorted(itertools.permutations(item.dims),key=lambda d: (-d[0]*d[1], -d[2])):
                # 检查当前方向是否适合当前区域
                if all(d <= rd for d, rd in zip(dim, r_dims)):
                    # 记录物品放置信息
                    item.position = r_pos
                    item.orientation = dim
                    box.used_space.append({
                        'pos': r_pos,
                        'dims': dim,
                        'item': item
                    })

                    # 空间分割处理（生成三个方向的剩余空间）
                    new_regions = []
                    remaining = (  # 计算各方向剩余尺寸
                        r_dims[0] - dim[0],
                        r_dims[1] - dim[1],
                        r_dims[2] - dim[2]
                    )

                    # X轴方向剩余空间（右侧空间）
                    if remaining[0] > 0:
                        new_regions.append({
                            'pos': (r_pos[0]+dim[0], r_pos[1], r_pos[2]),
                            'dims': (remaining[0], r_dims[1], r_dims[2])
                        })
                    # Y轴方向剩余空间（前方空间）
                    if remaining[1] > 0:
                        new_regions.append({
                            'pos': (r_pos[0], r_pos[1]+dim[1], r_pos[2]),
                            'dims': (dim[0], remaining[1], r_dims[2])
                        })
                    # Z轴方向剩余空间（上方空间）
                    if remaining[2] > 0:
                        new_regions.append({
                            'pos': (r_pos[0], r_pos[1], r_pos[2]+dim[2]),
                            'dims': (dim[0], dim[1], remaining[2])
                        })

                    # 更新可用区域列表
                    del free_regions[i]  # 移除已使用区域
                    free_regions.extend(new_regions)  # 添加新分割区域
                    placed = True  # 标记已成功放置
                    break  # 退出方向循环

            if placed:
                break  # 退出区域循环
        if not placed:
            return False  # 放置失败终止装箱
    return True  # 所有物品成功放置

def calculate_energy(box, items):
    """计算布局能量值（目标函数）"""
    used_volume = sum(i.volume for i in items)  # 已使用体积
    total_volume = box.volume  # 容器总容积

    # 紧凑度惩罚项（计算X轴方向最大延伸长度占比）
    max_coord = max(
        i.position[0] + i.orientation[0] for i in items
    ) if items else 0
    compact_penalty = max_coord / box.dims[0]  # 范围[0,1]

    # 综合能量计算（体积利用率权重90% + 紧凑度权重10%）
    return (used_volume / total_volume) * 0.9 + compact_penalty * 0.1


def neighbor_generator(current_order, mutation_rate=0.2):
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
        end = start + length  # 计算结束位置
        # 随机目标位置
        target = random.randint(0, len(new_order)-length)
        # 执行块交换
        new_order[start:end], new_order[target:target+length] = \
            new_order[target:target+length], new_order[start:end]

    return new_order

def simulated_annealing_pack(items, boxes, initial_temp=1000, cooling_rate=0.995, final_temp=1):
    """模拟退火主算法"""
    items, boxes = preprocess_order(items, boxes)
    if not boxes:
        return None, 0  # 无可用容器直接返回

    # 选择最小可用容器（体积刚好满足物品总体积）
    box = min([b for b in boxes if b.volume >= sum(i.volume for i in items)],
             key=lambda x: x.volume)

    # 初始化状态：按体积和最大尺寸降序排列
    current_order = sorted(items, key=lambda x: (-x.volume, -max(x.dims)))
    best_order = current_order.copy()  # 记录最佳状态
    best_energy = 0  # 最佳能量值
    current_temp = initial_temp  # 初始化温度

    # 退火循环
    while current_temp > final_temp:
        # 生成邻居状态
        new_order = neighbor_generator(current_order)

        # 尝试新布局并计算能量
        success = layout_items(new_order, box)
        current_energy = calculate_energy(box, new_order) if success else 0

        # 更新全局最优
        if current_energy > best_energy:
            best_energy = current_energy
            best_order = new_order.copy()

        # Metropolis准则判断状态转移
        energy_diff = current_energy - best_energy
        if energy_diff > 0 or math.exp(energy_diff / current_temp) > random.random():
            current_order = new_order.copy()

        current_temp *= cooling_rate  # 温度衰减

    # 应用最佳布局方案
    layout_items(best_order, box)
    used_volume = sum(i.volume for i in best_order)
    utilization = used_volume / box.volume * 100
    return box, utilization  # 返回最优容器和利用率



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
    for i in range(9):
        if data.iloc[i]['TL'] == '冷冻':
            item = Item(float(data.iloc[i]['L']), float(data.iloc[i]['W']), float(data.iloc[i]['H']), True)
        else:
            item = Item(float(data.iloc[i]['L']), float(data.iloc[i]['W']), float(data.iloc[i]['H']), False)

        items.append(item)

best_box, utilization = simulated_annealing_pack(items, boxes)
print(f"Best box: {best_box.id}, Utilization: {utilization:.1f}%")
