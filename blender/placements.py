"""Var varje genererad möbel ska stå: (asset, x, y, z_golv, rotation_grader, största horisontella mått i m eller None)."""
P1, P2, K = 0.0, 3.9, -3.2
PLACEMENTS = [
    # Entréhall
    ("hall_table", 13, 4.5, P1, 0, 1.4), ("pendant", 13, 4.5, P1 + 5.4, 0, 1.2),
    # Salong
    ("sofa", 4, 3.2, P1, 0, 3.2), ("sofa", 4, 5.8, P1, 180, 3.2), ("coffee_table", 4, 4.5, P1, 0, 1.6),
    ("armchair", 1.4, 4.5, P1, 90, 1.0), ("armchair", 6.6, 4.5, P1, -90, 1.0), ("rug", 4, 4.5, P1, 0, 5.0),
    ("side_table", 1.4, 2.6, P1, 0, 0.6),
    # Matsal
    ("dining_table", 21, 4, P1, 0, 5.6),
    *[("dining_chair", 18.7 + i * 0.77, 3.05, P1, 0, 0.5) for i in range(7)],
    *[("dining_chair", 18.7 + i * 0.77, 4.95, P1, 180, 0.5) for i in range(7)],
    ("ring_chandelier", 19.5, 4, P1 + 2.5, 0, 1.3), ("ring_chandelier", 22.5, 4, P1 + 2.5, 0, 1.3),
    # Eget kök
    ("kitchen_island", -4.0, 6.05, P1, 0, 3.0), ("range", -5.55, 7.0, P1, 90, 1.2),
    ("oak_cabinet", -5.6, 4.2, P1, 90, 1.2), ("oak_cabinet", -5.6, 9.8, P1, 90, 1.2), ("oak_cabinet", -0.5, 10.0, P1, -90, 1.2),
    # AI-kök
    ("robot_arm", -7, -0.3, P1 + 1.7, 0, 1.6), ("robot_arm", -3, -0.3, P1 + 1.7, 180, 1.6),
    # Bibliotek
    ("bookshelf", 0.45, 10.0, P1, 90, 3.4), ("bookshelf", 0.45, 13.4, P1, 90, 3.4), ("bookshelf", 2.5, 14.55, P1, 0, 3.4), ("bookshelf", 5.9, 14.55, P1, 0, 3.4),
    ("desk", 4, 10.5, P1, 0, 2.4), ("armchair", 3.2, 13, P1, 180, 1.0), ("armchair", 4.8, 13, P1, 180, 1.0), ("rug", 4, 11.5, P1, 0, 5.0),
    # Orangeri
    ("olive_tree", 11, 10, P1, 0, 2.2), ("olive_tree", 15, 10, P1, 40, 2.2), ("olive_tree", 11, 14, P1, 80, 2.2), ("olive_tree", 15, 14, P1, 120, 2.2),
    ("sofa", 13, 12, P1, 0, 2.6), ("side_table", 13, 13.6, P1, 0, 0.6),
    # Vardagsrum
    ("sofa", 21, 10.5, P1, 0, 4.0), ("coffee_table", 21, 12.3, P1, 0, 1.6), ("tv", 16.2, 11.5, P1 + 0.9, 90, 2.2), ("rug", 21, 11.5, P1, 0, 5.5),
    # Plan 2
    ("bed_master", -5, 0.6, P2, 180, 2.2), ("sofa", -5, 3.8, P2, 180, 3.0), ("rug", -5, 1.5, P2, 0, 5.5),
    ("bathtub", -2.5, 9.85, P2, 0, 1.9), ("vanity", -2.5, 5.45, P2, 180, 2.4),
    ("bed_master", 4, 3.0, P2, 180, 2.0), ("bed_master", 21, 2.5, P2, 180, 2.0), ("bed_master", 19, 11, P2, 0, 2.0),
    ("bed_single", 28.5, 0.0, P2, 180, 2.1), ("bed_single", 33.5, 0.0, P2, 180, 2.1),
    ("sofa", 13, 11.5, P2, 0, 3.6), ("tv", 10.2, 12.0, P2 + 0.9, 90, 2.2), ("rug", 13, 12.5, P2, 0, 5.0),
    ("bed_master", 3.0, 11.0, P2, 0, 2.2), ("rug", 3.0, 11.5, P2, 0, 4.5),
    # Källare
    *[("lounger", 11.7, yy + 0.95, K, 90, 2.0) for yy in (3, 5.5, 8, 10.5)],
    *[("recliner", xx, yy, K + zz, -90, 1.1) for (xx, zz) in ((22.5, 0.0), (24.0, 0.35), (25.3, 0.7)) for yy in (1.5, 3.2, 4.9, 6.6)],
    *[("server_rack", -9.3 + i * 0.75, 3.8, K, 0, 0.6) for i in range(6)],
    ("desk", -7.5, 6.0, K, 180, 2.4), ("bunk_bed", -8.0, -1.8, K, 0, 2.1), ("bunk_bed", -3.0, -1.8, K, 0, 2.1),
    *[("suv", 27.8 + i * 1.8, 0.4, K, 90, 5.4) for i in range(5)],
    ("pendant", 13, 7.5, P1 + 2.6, 0, 0.8),
]
