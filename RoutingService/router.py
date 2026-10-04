import math
import random


class rt_point:
    def __init__(self):
        self.rating = random.choice([0.1, 0.5, 1.0])
        self.visit_count = 0
        self.looped = 0
        self.watch_place = 0
        self.loop_start = 0
        self.loop_start = 0
        self.coordinates = [random.randint(1, 100), random.randint(1, 100)]


def get_rand_points_array():
    points = []
    for i in range(100):
        points.append(rt_point())
    return points


def get_distance(point1, point2):
    distance = (point1.coordinates[0] - point2.coordinates[0]) ** 2 + (
                point1.coordinates[1] - point2.coordinates[1]) ** 2
    return math.sqrt(distance)


def get_distance_matrix(points):
    matrix = []
    for i in range(len(points)):
        matrix.append([])
    for i in range(len(points)):
        for j in range(0, i):
            matrix[i].append(matrix[j][i])
        for j in range(i, len(points)):
            matrix[i].append(get_distance(points[i], points[j]))
    return matrix


def get_point_weightened_rt(rating, distance):
    wgt_rt = rating / (1 + distance) ** 2
    return wgt_rt


def find_loop(route, new_point_index):
    if new_point_index in route:
        loop_start_index = route.index(new_point_index)
        if len(route) - loop_start_index >= 3:
            loop_points_indices = route[loop_start_index:] + [new_point_index]
            return True, loop_start_index, loop_points_indices
        else:
            return False, -1, []
    return False, -1, []


def mark_loop_points(points, loop_points_indices, loop_start_index):
    for idx in loop_points_indices:
        if idx == loop_start_index:
            points[idx].loop_start = 1
            points[idx].looped = 0
        else:
            points[idx].looped = 1
            points[idx].loop_start = 0


def can_visit_point(point, current_route, new_point_index, previous_point=None):
    if new_point_index not in current_route:
        return True

    if point.looped == 1:
        return False

    if point.loop_start == 1:
        return True

    loop_start_idx = current_route.index(new_point_index)
    if len(current_route) - loop_start_idx >= 3:
        return True
    else:
        return False


def build_route(points, start_point_index=0, max_steps=20):
    if not points:
        return []

    n = len(points)
    route = [start_point_index]
    current_point = start_point_index
    previous_point = None

    for point in points:
        point.visit_count = 0
        point.looped = 0
        point.loop_start = 0
        point.watch_place = 0

    points[start_point_index].visit_count = 1

    print(f"\n{'=' * 60}")
    print(f"НАЧАЛО ПОСТРОЕНИЯ МАРШРУТА")
    print(f"{'=' * 60}")
    print(f"Стартовая точка: {start_point_index} (рейтинг={points[start_point_index].rating:.2f})")
    print(f"Правила: кольца минимум из 3 уникальных точек")
    loop_count = 0
    while len(route) < max_steps:
        best_next = None
        best_score = -float('inf')

        print(f"\n--- Шаг {len(route)} ---")
        print(f"Текущая точка: {current_point}")
        if previous_point is not None:
            print(f"Предыдущая точка: {previous_point}")

        for next_point_idx in range(n):
            if next_point_idx == current_point:
                continue
            if next_point_idx == previous_point:
                continue
            if not can_visit_point(points[next_point_idx], route, next_point_idx, current_point):
                reason = ""
                if points[next_point_idx].looped == 1:
                    reason = "точка внутри кольца (заблокирована)"
                elif next_point_idx in route and points[next_point_idx].loop_start != 1:
                    loop_start_idx = route.index(next_point_idx)
                    if len(route) - loop_start_idx < 3:
                        reason = "попытка создать кольцо менее чем из 3 точек (запрещено)"
                    else:
                        reason = "недоступна по другим причинам"
                else:
                    reason = "недоступна"
                print(f"  Точка {next_point_idx}: НЕДОСТУПНА - {reason}")
                continue

            distance = get_distance(points[current_point], points[next_point_idx])
            score = get_point_weightened_rt(points[next_point_idx].rating, distance)

            if next_point_idx in route and points[next_point_idx].loop_start != 1:
                mult = 1.2 - 0.05 * loop_count
                loop_count += 1
                score *= mult
                print(f"  Точка {next_point_idx}: образует кольцо, бонус ")

            visit_status = "НОВАЯ" if next_point_idx not in route else "СОЗДАЕТ КОЛЬЦО"
            print(f"  Точка {next_point_idx}: рейтинг={points[next_point_idx].rating:.2f}, "
                  f"расст={distance:.2f}, score={score:.4f}, {visit_status}")

            if score > best_score:
                best_score = score
                best_next = next_point_idx

        if best_next is None:
            print(f"\nНет доступных точек для продолжения маршрута")
            break

        is_loop, loop_start_idx, loop_points = find_loop(route, best_next)

        if is_loop:
            print(f"\n!!! ОБНАРУЖЕНО ВАЛИДНОЕ КОЛЬЦО !!!")
            print(f"Замыкание на точку {best_next} (была на позиции {loop_start_idx})")
            print(f"Размер кольца: {len(loop_points)} точек")
            print(f"Точки в кольце: {loop_points}")

            mark_loop_points(points, loop_points, loop_start_idx)
            print(f"Точка {loop_start_idx} помечена как loop_start (можно посещать повторно)")
            for idx in loop_points:
                if idx != loop_start_idx:
                    print(f"Точка {idx} помечена как looped (заблокирована для будущих посещений)")

        route.append(best_next)
        points[best_next].visit_count += 1
        previous_point = current_point
        current_point = best_next

        print(f"\nДобавлена точка {best_next} (рейтинг={points[best_next].rating:.2f}, score={best_score:.4f})")
        print(f"Текущий маршрут: {route}")

    return route


def mark_watch_places(points, route, WD, WN):
    candidates = []
    for i, point in enumerate(points):
        if i in route:
            continue
        if point.rating != 1.0:
            continue
        min_dist = min(get_distance(points[i], points[r]) for r in route)
        if min_dist < WD:
            candidates.append((i, min_dist))

    candidates.sort(key=lambda x: x[1])
    selected = candidates[:WN]

    for idx, dist in selected:
        points[idx].watch_place = 1
        print(f"Точка {idx} помечена как смотровая площадка (расстояние до маршрута = {dist:.2f})")

    return len(selected)


def print_route_info(points, route):
    # ... твой код вывода ...
    pass