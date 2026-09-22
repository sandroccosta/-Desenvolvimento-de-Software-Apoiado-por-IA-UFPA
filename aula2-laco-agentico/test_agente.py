import unittest
from unittest.mock import patch

import agente


class TestExperimentos(unittest.TestCase):
    def test_executa_cinco_pares_com_a_mesma_semente_em_cada_par(self):
        chamadas = []

        def registrar(modo, semente):
            chamadas.append((modo, semente))
            return 2

        with patch.object(agente, "rodar", side_effect=registrar):
            agente.executar_experimentos()

        esperado = [
            (modo, semente)
            for semente in agente.SEMENTES
            for modo in ("boa", "vaga")
        ]
        self.assertEqual(chamadas, esperado)


if __name__ == "__main__":
    unittest.main()
