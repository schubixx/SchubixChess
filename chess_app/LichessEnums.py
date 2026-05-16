from enum import IntEnum

class Laenge(IntEnum):
    BELIEBIG = 0
    EINZUEGIG = 1
    KURZE_AUFGABE = 2
    MEHRZUEGIGE_AUFGABE = 3
    SEHR_LANGE_AUFGABE = 4

LAENGE_NAMEN = {
    Laenge.BELIEBIG: "beliebige Länge",
    Laenge.EINZUEGIG: "einzügige Aufgabe",
    Laenge.KURZE_AUFGABE: "kurze Aufgabe",
    Laenge.MEHRZUEGIGE_AUFGABE: "mehrzügige Aufgabe",
    Laenge.SEHR_LANGE_AUFGABE: "sehr lange Aufgabe",
}


from enum import IntEnum


class Thema(IntEnum):
    ZUFALL = 0

    # normale Motive
    VORGERUECKTER_BAUER = 117
    ANGRIFF_AUF_F2_ODER_F7 = 121
    SCHLAGE_DEN_VERTEIDIGER = 113
    ABZUGSANGRIFF = 103
    DOPPELSCHACH = 104
    EXPONIERTER_KOENIG = 118
    GABEL = 100
    HAENGENDE_FIGUR = 112
    ANGRIFF_AUF_DEM_KOENIGSFLUEGEL = 119
    FESSELUNG = 101
    ANGRIFF_AUF_DEM_DAMENFLUEGEL = 120
    OPFER = 114
    SPIESS = 102
    GEFANGENE_FIGUR = 111

    HINLENKUNG = 105
    VERTEIDIGUNGSZUG = 116
    ABLENKUNG = 106
    RAEUMUNG = 108
    UNTERBRECHUNG = 107
    STILLER_ZUG = 115
    ZWISCHENZUG = 110
    ROENTGEN_ANGRIFF = 109

    # in INITIAL_TAG_MAP nicht enthalten, daher frei vergeben
    ZUGZWANG = 159

    # Matt allgemein
    MATT = 200

    # Matt in X
    MATT_IN_1 = 1
    MATT_IN_2 = 2
    MATT_IN_3 = 3
    MATT_IN_4 = 4
    MATT_IN_5 = 5

    # Mattbilder
    MATT_ANASTASIA = 10
    MATT_ARABISCHES = 11
    MATT_GRUNDREIHENMATT = 12
    MATT_BODEN_MATT = 13
    MATT_LAEUFERPAARMATT = 14
    MATT_STERNMATT = 15
    MATT_HAKENMATT = 16
    MATT_ERSTICKTES_MATT = 17

    # Phasen ab 1000
    PHASE_EROEFFNUNG = 1001
    PHASE_MITTELSPIEL = 1002
    PHASE_ENDSPIEL = 1003
    PHASE_BAUERN_ENDSPIEL = 1004
    PHASE_TURM_ENDSPIEL = 1005
    PHASE_LAEUFER_ENDSPIEL = 1006
    PHASE_SPRINGER_ENDSPIEL = 1007
    PHASE_DAMEN_ENDSPIEL = 1008
    PHASE_DAME_TURM_ENDSPIEL = 1009


THEMA_NAMEN = {
    Thema.ZUFALL: "Zufällige Aufgabe",

    Thema.ABLENKUNG: "Ablenkung",
    Thema.ABZUGSANGRIFF: "Abzugsangriff",
    Thema.ANGRIFF_AUF_DEM_DAMENFLUEGEL: "Angriff auf dem Damenflügel",
    Thema.ANGRIFF_AUF_DEM_KOENIGSFLUEGEL: "Angriff auf dem Königsflügel",
    Thema.ANGRIFF_AUF_F2_ODER_F7: "Angriff auf f2 oder f7",
    Thema.DOPPELSCHACH: "Doppelschach",
    Thema.EXPONIERTER_KOENIG: "Exponierter König",
    Thema.FESSELUNG: "Fesselung",
    Thema.GABEL: "Gabel",
    Thema.GEFANGENE_FIGUR: "Gefangene Figur",
    Thema.HAENGENDE_FIGUR: "Hängende Figur",
    Thema.HINLENKUNG: "Hinlenkung",

    Thema.MATT: "Matt",

    Thema.MATT_IN_1: "Matt in 1",
    Thema.MATT_IN_2: "Matt in 2",
    Thema.MATT_IN_3: "Matt in 3",
    Thema.MATT_IN_4: "Matt in 4",
    Thema.MATT_IN_5: "Matt in 5",

    Thema.MATT_ANASTASIA: "Matt: Anastasia",
    Thema.MATT_ARABISCHES: "Matt: Arabisches",
    Thema.MATT_BODEN_MATT: "Matt: Boden-Matt",
    Thema.MATT_ERSTICKTES_MATT: "Matt: ersticktes Matt",
    Thema.MATT_GRUNDREIHENMATT: "Matt: Grundreihenmatt",
    Thema.MATT_HAKENMATT: "Matt: Hakenmatt",
    Thema.MATT_LAEUFERPAARMATT: "Matt: Läuferpaarmatt",
    Thema.MATT_STERNMATT: "Matt: Sternmatt",

    Thema.OPFER: "Opfer",
    Thema.RAEUMUNG: "Räumung",
    Thema.ROENTGEN_ANGRIFF: "Röntgen-Angriff",
    Thema.SCHLAGE_DEN_VERTEIDIGER: "Schlage den Verteidiger",
    Thema.SPIESS: "Spieß",
    Thema.STILLER_ZUG: "Stiller Zug",
    Thema.UNTERBRECHUNG: "Unterbrechung",
    Thema.VERTEIDIGUNGSZUG: "Verteidigungszug",
    Thema.VORGERUECKTER_BAUER: "Vorgerückter Bauer",
    Thema.ZUGZWANG: "Zugzwang",
    Thema.ZWISCHENZUG: "Zwischenzug",

    Thema.PHASE_EROEFFNUNG: "Phase: Eröffnung",
    Thema.PHASE_MITTELSPIEL: "Phase: Mittelspiel",
    Thema.PHASE_ENDSPIEL: "Phase: Endspiel",
    Thema.PHASE_BAUERN_ENDSPIEL: "Phase: Bauernendspiel",
    Thema.PHASE_TURM_ENDSPIEL: "Phase: Turmendspiel",
    Thema.PHASE_LAEUFER_ENDSPIEL: "Phase: Läuferendspiel",
    Thema.PHASE_SPRINGER_ENDSPIEL: "Phase: Springerendspiel",
    Thema.PHASE_DAMEN_ENDSPIEL: "Phase: Damenendspiel",
    Thema.PHASE_DAME_TURM_ENDSPIEL: "Phase: Dame-Turm-Endspiel",
}