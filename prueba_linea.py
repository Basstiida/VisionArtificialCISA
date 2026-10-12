from linea_virtual import evaluar_cruce

pasos = [
    # cam, track, cx,  cy,  numero, tiempo
    (1, 7, 300, 400, "5038", 1000),   # cámara 1: primer avistamiento     -> None
    (2, 7, 450, 300, "2501", 1000),   # cámara 2: MISMO track_id 7, otro bus -> None
    (1, 7, 450, 300, "5038", 1002),   # cámara 1: cruza                    -> salida
    (2, 7, 300, 400, "2501", 1003),   # cámara 2: cruza al revés           -> entrada
    (1, 7, 300, 400, "5038", 1010),   # cámara 1: regresa a los 8 s        -> maniobra
    (2, 9, 450, 300, "5038", 1030),   # 5038 llega a la cámara 2           -> None
    (2, 9, 300, 400, "5038", 1031),   # y entra por la otra puerta         -> entrada
]
for p in pasos:
    print(p, "->", evaluar_cruce(*p))
