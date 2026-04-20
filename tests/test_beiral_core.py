import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "codigo_fonte"))

from beiral.core import EntradaBeiral, calcular_beiral, sanitize_filename_component, validar_entrada


class BeiralCoreTests(unittest.TestCase):
    def test_calcula_cargas_e_momento_sem_p(self) -> None:
        entrada = EntradaBeiral(
            nome_projeto="Projeto A",
            espessura_cm=14.0,
            largura_cm=110.0,
            carga_permanente_tf_m2=0.3,
            carga_acidental_tf_m2=0.2,
            possui_nervura_borda=False,
        )

        resultado = calcular_beiral(entrada)

        self.assertAlmostEqual(resultado.espessura_m, 0.14)
        self.assertAlmostEqual(resultado.largura_m, 1.10)
        self.assertAlmostEqual(resultado.peso_proprio_laje_tf_m2, 0.35)
        self.assertAlmostEqual(resultado.carga_total_q_tf_m2, 0.85)
        self.assertAlmostEqual(resultado.carga_total_p_tf_m, 0.0)
        self.assertAlmostEqual(resultado.momento_total_tf_m, 0.51425)
        self.assertAlmostEqual(resultado.majorador, 1.25)
        self.assertAlmostEqual(resultado.msk_tf_m, 0.6428125)
        self.assertFalse(resultado.possui_carga_concentrada)

    def test_calcula_carga_concentrada_com_nervura_e_guarda_corpo(self) -> None:
        entrada = EntradaBeiral(
            nome_projeto="Projeto B",
            espessura_cm=12.0,
            largura_cm=120.0,
            carga_permanente_tf_m2=0.25,
            carga_acidental_tf_m2=0.15,
            possui_nervura_borda=True,
            espessura_nervura_cm=14.0,
            altura_nervura_cm=70.0,
            possui_guarda_corpo=True,
            espessura_alvenaria_cm=12.0,
            altura_alvenaria_cm=110.0,
        )

        resultado = calcular_beiral(entrada)

        self.assertAlmostEqual(resultado.peso_proprio_nervura_tf_m, 0.245)
        self.assertAlmostEqual(resultado.carga_alvenaria_tf_m, 0.1716)
        self.assertAlmostEqual(resultado.carga_total_p_tf_m, 0.4166)
        self.assertAlmostEqual(resultado.momento_distribuido_tf_m, 0.504)
        self.assertAlmostEqual(resultado.momento_concentrado_tf_m, 0.49992)
        self.assertAlmostEqual(resultado.momento_total_tf_m, 1.00392)
        self.assertTrue(resultado.possui_carga_concentrada)

    def test_valida_campos_obrigatorios(self) -> None:
        entrada = EntradaBeiral(
            nome_projeto=" ",
            espessura_cm=0.0,
            largura_cm=0.0,
            carga_permanente_tf_m2=-1.0,
            carga_acidental_tf_m2=-1.0,
            possui_nervura_borda=True,
            espessura_nervura_cm=0.0,
            altura_nervura_cm=0.0,
            possui_guarda_corpo=True,
            espessura_alvenaria_cm=0.0,
            altura_alvenaria_cm=0.0,
        )

        erros = validar_entrada(entrada)

        self.assertGreaterEqual(len(erros), 7)

    def test_sanitiza_nome_de_arquivo(self) -> None:
        nome = sanitize_filename_component("Projeto: Beiral / 01")
        self.assertEqual(nome, "Projeto_Beiral__01")


if __name__ == "__main__":
    unittest.main()
