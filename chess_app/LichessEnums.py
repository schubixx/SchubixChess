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


class Thema(IntEnum):
    ZUFALL = 0
    ABLENKUNG = 154
    ABZUGSANGRIFF = 104
    ANGRIFF_AUF_DEM_DAMENFLUEGEL = 111
    ANGRIFF_AUF_DEM_KOENIGSFLUEGEL = 109
    ANGRIFF_AUF_F2_ODER_F7 = 102
    DOPPELSCHACH = 105
    EXPONIERTER_KOENIG = 106
    FESSELUNG = 110
    GABEL = 107
    GEFANGENE_FIGUR = 114
    HAENGENDE_FIGUR = 108
    HINLENKUNG = 151
    MATT_IN_1 = 201
    MATT_IN_2 = 202
    MATT_IN_3 = 203
    MATT_IN_4 = 204
    MATT_IN_5 = 205
    MATT = 200
    MATT_ANASTASIA = 206
    MATT_ARABISCHES = 207
    MATT_BODEN_MATT = 209
    MATT_ERSTICKTES_MATT = 213
    MATT_GRUNDREIHENMATT = 208
    MATT_HAKENMATT = 212
    MATT_LAEUFERPAARMATT = 210
    MATT_STERNMATT = 211
    OPFER = 112
    RAEUMUNG = 152
    ROENTGEN_ANGRIFF = 158
    SCHLAGE_DEN_VERTEIDIGER = 103
    SPIESS = 113
    STILLER_ZUG = 157
    UNTERBRECHUNG = 155
    VERTEIDIGUNGSZUG = 153
    VORGERUECKTER_BAUER = 101
    ZUGZWANG = 159
    ZWISCHENZUG = 156


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
    Thema.MATT_IN_1: "Matt in 1",
    Thema.MATT_IN_2: "Matt in 2",
    Thema.MATT_IN_3: "Matt in 3",
    Thema.MATT_IN_4: "Matt in 4",
    Thema.MATT_IN_5: "Matt in 5",
    Thema.MATT: "Matt",
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
}