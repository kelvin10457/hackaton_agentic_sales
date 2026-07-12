from identity import IdentityLocal, IdentityPort


def test_identity_local_implementa_puerto_y_valida_cedula():
    port = IdentityLocal()
    assert isinstance(port, IdentityPort)
    resultado = port.resolver("1713175071")
    assert resultado.valido is True
    assert resultado.tipo == "cedula"


def test_identity_local_rechaza_documento_invalido():
    resultado = IdentityLocal().resolver("0000000000")
    assert resultado.valido is False
    assert resultado.tipo == "invalido"
