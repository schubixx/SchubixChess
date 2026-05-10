from dataclasses import dataclass

from ..LichessEnums import Thema, Laenge


@dataclass(frozen=True)
class VisualizationParameter:
    halbzuege: int
    rating: int
    thema: int
    laenge: int


def _valid_themen():
    return [int(t.value) for t in Thema]


def _valid_laengen():
    return [int(l.value) for l in Laenge]


def encode_visualization_parameter(
    halbzuege: int,
    rating: int,
    thema: int,
    laenge: int,
) -> str:
    """
    Format:
    HH RR TT L

    HH = Halbzüge, 2 Stellen
    RR = Rating / 100, 2 Stellen
    TT = Index des Themas in der Thema-Liste, 2 Stellen
    L  = Länge, 1 Stelle
    """

    themen = _valid_themen()

    if thema not in themen:
        thema = int(Thema.ZUFALL.value)

    thema_index = themen.index(thema)
    rating_bucket = rating // 100

    return f"{halbzuege:02d}{rating_bucket:02d}{thema_index:02d}{laenge:01d}"


def decode_visualization_parameter(parameter: str) -> VisualizationParameter:
    if not parameter or len(parameter) != 7:
        raise ValueError("Ungültiger Parameter.")

    halbzuege = int(parameter[0:2])
    rating_bucket = int(parameter[2:4])
    thema_index = int(parameter[4:6])
    laenge = int(parameter[6:7])

    themen = _valid_themen()
    laengen = _valid_laengen()

    if thema_index < 0 or thema_index >= len(themen):
        raise ValueError("Ungültiges Thema im Parameter.")

    thema = themen[thema_index]

    if laenge not in laengen:
        raise ValueError("Ungültige Länge im Parameter.")

    return VisualizationParameter(
        halbzuege=halbzuege,
        rating=rating_bucket * 100,
        thema=thema,
        laenge=laenge,
    )