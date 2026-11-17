"""Rumsprogram för herrgården – alla mått i meter.
Koordinater: x längs fasaden (väst→öst), y = djup (framsida y≈0, trädgård bakåt).
Varje rum: (namn, x0, y0, x1, y1).
"""

# Byggnadskroppar (yttermått)
MAIN = (0, 0, 26, 15)        # huvudkropp
WEST = (-10, -3, 0, 11)      # västra flygeln (skjuter fram 3 m)
EAST = (26, -3, 36, 11)      # östra flygeln
BLOCKS = {"main": MAIN, "west": WEST, "east": EAST}

# Våningshöjder (golv till golv)
LEVELS = [
    ("Källare", -3.2, 3.2),
    ("Plan 1", 0.0, 3.9),
    ("Plan 2", 3.9, 3.4),
]
ROOF_BASE = 7.3  # överkant plan 2

ROOMS = {
"Källare": [
    # västra flygeln
    ("Skyddsrum",            -10, -3,  0,  3),
    ("Serverrum",            -10,  3, -5,  7),
    ("Teknik / UPS / el",     -5,  3,  0,  7),
    ("AI-tvättstuga",        -10,  7,  0, 11),
    # huvudkropp
    ("Gym",                    0,  0,  8,  7),
    ("Bastu & relax",          0,  7,  8, 15),
    ("Hiss & trappa",          8,  5, 11, 10),
    ("Korridor",               8,  0, 11,  5),
    ("Förråd",                 8, 10, 11, 15),
    ("Pool & spa",            11,  0, 20, 15),
    ("Biograf",               20,  0, 26,  8),
    ("Vinkällare",            20,  8, 26, 15),
    # östra flygeln
    ("Garage (6 bilar)",      26, -3, 36,  8),
    ("Verkstad / laddning",   26,  8, 36, 11),
],
"Plan 1": [
    # västra flygeln – matens våning
    ("AI-kök (robotkök)",    -10, -3,  0,  3),
    ("Skafferi / varulager", -10,  3, -6,  7),
    ("Eget kök",              -6,  3,  0, 11),
    ("Frukostrum",           -10,  7, -6, 11),
    # huvudkropp
    ("Salong",                 0,  0,  8,  8),
    ("Bibliotek",              0,  8,  8, 15),
    ("Hiss & trappa",          8,  5, 10, 10),
    ("Gäst-WC",                8,  0, 10,  5),
    ("Garderob",               8, 10, 10, 15),
    ("Entréhall (dubbelhöjd)",10,  0, 16,  9),
    ("Orangeri",              10,  9, 16, 15),
    ("Matsal",                16,  0, 26,  8),
    ("Vardagsrum",            16,  8, 26, 15),
    # östra flygeln
    ("Groventré",             26, -3, 30,  3),
    ("Gästsvit",              30, -3, 36,  3),
    ("Städ- & robotcentral",  26,  3, 30,  7),
    ("Förråd",                26,  7, 30, 11),
    ("Kontor / KC",           30,  3, 36, 11),
],
"Plan 2": [
    # västra flygeln – master suite
    ("Master sovrum",        -10, -3,  0,  5),
    ("Walk-in closet",       -10,  5, -5, 11),
    ("Master spa-bad",        -5,  5,  0, 11),
    # huvudkropp
    ("Sovrum 2",               0,  0,  8,  7),
    ("Privat rum",             0,  7,  6, 15),
    ("Bad 2",                  6,  7, 10, 15),
    ("Hiss & trappa",          8,  5, 10,  7),
    ("Korridor",               8,  0, 10,  5),
    ("Galleri (öppet ner)",   10,  0, 16,  9),
    ("Allrum / TV",           10,  9, 16, 15),
    ("Sovrum 3",              16,  0, 26,  7),
    ("Sovrum 4",              16,  7, 22, 15),
    ("Bad 3",                 22,  7, 26, 15),
    # östra flygeln
    ("Barnrum 1",             26, -3, 31,  4),
    ("Barnrum 2",             31, -3, 36,  4),
    ("Lekrum / studio",       26,  4, 36, 11),
],
}

# Dörrar: (våning, x, y, riktning 'h' = öppning i vägg längs x, 'v' = längs y)
DOORS = {
"Källare": [
    (0, 0, 'v'), (0, 9, 'v'), (-5, 5, 'v'), (-2.5, 7, 'h'), (-5, 3, 'h'),
    (8, 3, 'v'), (8, 11, 'v'), (11, 3, 'v'), (11, 7, 'v'), (9.5, 5, 'h'), (9.5, 10, 'h'),
    (20, 4, 'v'), (20, 11, 'v'), (23, 8, 'h'), (26, 5, 'v'), (31, 8, 'h'),
],
"Plan 1": [
    (0, 1, 'v'), (0, 6, 'v'), (-6, 5, 'v'), (-6, 9, 'v'), (-3, 3, 'h'),
    (8, 3, 'v'), (8, 11, 'v'), (10, 2, 'v'), (10, 7, 'v'), (10, 12, 'v'),
    (9, 5, 'h'), (9, 10, 'h'), (13, 9, 'h'), (16, 4, 'v'), (16, 11, 'v'),
    (21, 8, 'h'), (26, 1, 'v'), (26, 5, 'v'), (28, 3, 'h'), (30, 0, 'v'),
    (30, 5, 'v'), (30, 9, 'v'), (4, 8, 'h'),
    (13, 0, 'h'), (13, 15, 'h'), (21, 15, 'h'), (28, -3, 'h'),
],
"Plan 2": [
    (0, 2, 'v'), (-5, 8, 'v'), (-2.5, 5, 'h'), (-7.5, 5, 'h'),
    (8, 3, 'v'), (10, 2, 'v'), (10, 11, 'v'), (9, 5, 'h'), (9, 7, 'h'),
    (6, 11, 'v'), (3, 7, 'h'), (16, 3, 'v'), (16, 11, 'v'), (19, 7, 'h'),
    (22, 11, 'v'), (26, 1, 'v'), (26, 6, 'v'), (28, 4, 'h'), (33, 4, 'h'), (31, 0, 'v'),
],
}

# Rum utan ytterfönster (hemliga/tekniska)
NO_WINDOWS = {"Skyddsrum", "Serverrum", "Teknik / UPS / el", "Privat rum", "Hiss & trappa", "Förråd", "Korridor", "Biograf"}
