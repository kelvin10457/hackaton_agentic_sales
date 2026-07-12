"""test_ruta — Enrutamiento determinista. Biblia §6.3."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.calcular_ruta import calcular_ruta


def test_b2b_siempre_ventas_corporativas():
    assert calcular_ruta("B2B", score_total=10, pidio_asesor=False) == "ventas_corporativas"
    assert calcular_ruta("B2B", score_total=95, pidio_asesor=True) == "ventas_corporativas"


def test_b2c_caliente_con_asesor():
    assert calcular_ruta("B2C", score_total=88, pidio_asesor=True) == "asesoria_inversion"


def test_b2c_caliente_sin_asesor():
    assert calcular_ruta("B2C", score_total=75, pidio_asesor=False) == "programa_inicial"


def test_b2c_tibio():
    assert calcular_ruta("B2C", score_total=55, pidio_asesor=False) == "nutricion_educativa"


def test_b2c_frio():
    assert calcular_ruta("B2C", score_total=20, pidio_asesor=False) == "automatico"


def test_maria_da_asesoria_inversion():
    """Verifica el caso real de María: score 88, pidió asesor."""
    assert calcular_ruta("B2C", score_total=88, pidio_asesor=True) == "asesoria_inversion"


def test_andres_da_ventas_corporativas():
    """Verifica el caso real de Andrés: B2B, score 65."""
    assert calcular_ruta("B2B", score_total=65, pidio_asesor=False) == "ventas_corporativas"
