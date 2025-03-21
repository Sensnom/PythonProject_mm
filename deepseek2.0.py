class Item:
    def __init__(self, l, w, h, num, is_frozen=False):
        self.l = l
        self.w = w
        self.h = h
        self.num = num
        self.is_frozen = is_frozen

    def generate_rotations(self):
        """生成3种循环旋转方向（避免对称重复）"""
        # 三种循环排列：(l, w, h), (w, h, l), (h, l, w)
        rotations = [
            (self.l, self.w, self.h),
            (self.w, self.h, self.l),
            (self.h, self.l, self.w)
        ]
        # 去重（若存在边长相等的情况）
        unique_rotations = []
        seen = set()
        for r in rotations:
            key = tuple(sorted(r))  # 通过排序去重对称方向
            if key not in seen:
                seen.add(key)
                unique_rotations.append(r)
        return unique_rotations

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


def merge_adjacent_spaces(candidate_positions, box):
    """合并相邻的候选位置，减少空间碎片"""
    merged = []
    for pos in sorted(candidate_positions, key=lambda p: (p[2], p[1], p[0])):
        x, y, z = pos
        # 检查是否可以与已有空间合并
        merged_flag = False
        for m in merged:
            mx, my, mz = m
            # 横向合并（x轴方向）
            if my == y and mz == z and mx + 1 == x:
                merged.remove(m)
                merged.append((mx, my, mz))
                merged_flag = True
                break
            # 纵向合并（y轴方向）
            if mx == x and mz == z and my + 1 == y:
                merged.remove(m)
                merged.append((x, my, mz))
                merged_flag = True
                break
            # 高度合并（z轴方向）
            if mx == x and my == y and mz + 1 == z:
                merged.remove(m)
                merged.append((x, y, mz))
                merged_flag = True
                break
        if not merged_flag:
            merged.append(pos)
    return merged


def try_rearrange(placed_items, box):
    """局部重排：尝试调整已放置物体的位置或旋转方向"""
    for i in range(len(placed_items)):
        item = placed_items[i]
        # 生成所有可能的旋转
        rotations = sorted(item['item'].generate_rotations(),
                           key=lambda d: d[0] * d[1] * d[2], reverse=True)
        for (new_l, new_w, new_h) in rotations:
            # 尝试新方向是否更优
            if (new_l <= item['dims'][0] and new_w <= item['dims'][1] and new_h <= item['dims'][2]):
                continue  # 跳过更差方向
            # 临时移除当前物体
            temp_placed = [p for p in placed_items if p != item]
            # 检查新方向是否能放入原位置
            x, y, z = item['pos']
            if x + new_l > box.l or y + new_w > box.w or z + new_h > box.h:
                continue
            # 检查与其他物体是否重叠
            overlap = False
            for p in temp_placed:
                px, py, pz = p['pos']
                pl, pw, ph = p['dims']
                if not (x + new_l <= px or x >= px + pl or
                        y + new_w <= py or y >= py + pw or
                        z + new_h <= pz or z >= pz + ph):
                    overlap = True
                    break
            if not overlap:
                # 更新方向和候选位置
                item['dims'] = (new_l, new_w, new_h)
                return True
    return False


def greedy_pack_optimized(items, boxes):
    """改进后的贪心算法（含动态优化）"""
    boxes_sorted = sorted(boxes, key=lambda b: b.volume)
    items_sorted = sorted(items, key=lambda x: x.l * x.w * x.h, reverse=True)

    for box in boxes_sorted:
        candidate_positions = [(0, 0, 0)]
        placed_items = []
        feasible = True

        for item in items_sorted:
            for _ in range(item.num):
                placed = False
                rotations = sorted(item.generate_rotations(),
                                   key=lambda d: d[0] * d[1] * d[2], reverse=True)

                for (l, w, h) in rotations:
                    # 候选位置合并优化
                    candidate_positions = merge_adjacent_spaces(candidate_positions, box)
                    for pos in sorted(candidate_positions, key=lambda p: (p[2], p[1], p[0])):
                        x, y, z = pos
                        if x + l > box.l or y + w > box.w or z + h > box.h:
                            continue
                        # 重叠检查
                        overlap = False
                        for p in placed_items:
                            px, py, pz = p['pos']
                            pl, pw, ph = p['dims']
                            if not (x + l <= px or x >= px + pl or
                                    y + w <= py or y >= py + pw or
                                    z + h <= pz or z >= pz + ph):
                                overlap = True
                                break
                        if not overlap:
                            placed_items.append({
                                'pos': (x, y, z),
                                'dims': (l, w, h),
                                'item': item
                            })
                            candidate_positions.remove(pos)
                            new_positions = [
                                (x + l, y, z) if x + l <= box.l else None,
                                (x, y + w, z) if y + w <= box.w else None,
                                (x, y, z + h) if z + h <= box.h else None
                            ]
                            new_positions = [p for p in new_positions if p is not None]
                            candidate_positions += new_positions
                            candidate_positions = sorted(
                                list(set(candidate_positions)),
                                key=lambda p: (p[2], p[1], p[0])
                            )
                            # 动态优化：尝试局部重排
                            if try_rearrange(placed_items, box):
                                candidate_positions = merge_adjacent_spaces(candidate_positions, box)
                            placed = True
                            break
                    if placed: break
                if not placed:
                    feasible = False
                    break
            if not feasible: break
        if feasible:
            used_volume = sum(d['dims'][0] * d['dims'][1] * d['dims'][2] for d in placed_items)
            utilization = used_volume / box.volume * 100
            return {
                'box': box.box_id,
                'volume': box.volume,
                'utilization': round(utilization, 2),
                'placements': placed_items
            }
    return None