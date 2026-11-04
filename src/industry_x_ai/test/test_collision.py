from industry_x_ai.collision import min_arm_distance, segment_distance


def test_segment_distance_parallel_and_crossing():
    assert abs(segment_distance(((0, 0, 0), (1, 0, 0)), ((0, 1, 0), (1, 1, 0))) - 1.0) < 1e-9
    assert segment_distance(((0, 0, 0), (1, 0, 0)), ((0.5, -1, 0), (0.5, 1, 0))) < 1e-9
    assert abs(segment_distance(((0, 0, 0), (1, 0, 0)), ((2, 0, 0), (3, 0, 0))) - 1.0) < 1e-9


def test_min_arm_distance_ignores_base():
    a = [((0, 0, 0), (0, 0, 1)), ((5, 5, 5), (6, 5, 5))]
    b = [((0, 0, 0), (0, 0, 1)), ((8, 5, 5), (9, 5, 5))]
    assert abs(min_arm_distance(a, b) - 2.0) < 1e-9
