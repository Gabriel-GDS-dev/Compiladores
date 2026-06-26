import re
import sys
import unittest
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from compilador import Parser, compilar_codigo  # noqa: E402


class TestConformidadeCompilador(unittest.TestCase):
    def compilar_ok(self, codigo: str):
        resultado = compilar_codigo(codigo, "teste")
        self.assertTrue(resultado.sucesso, resultado.diagnostico)
        return resultado

    def compilar_erro(self, codigo: str, trecho: str):
        resultado = compilar_codigo(codigo, "teste")
        self.assertFalse(resultado.sucesso)
        self.assertIn(trecho, resultado.diagnostico)
        return resultado

    def test_constantes_globais_int_e_float(self):
        resultado = self.compilar_ok(
            "const LIMITE = 10; const PI = 3.14; "
            "float area(float r){ return PI * r * r; } "
            "int main(){ return LIMITE; }"
        )
        constantes = {s.nome: s for s in resultado.simbolos if s.categoria == "constante"}
        self.assertEqual(constantes["LIMITE"].tipo, "int")
        self.assertEqual(constantes["PI"].tipo, "float")
        self.assertEqual(constantes["LIMITE"].nivel, 0)

    def test_constante_nao_pode_ser_alterada(self):
        self.compilar_erro(
            "const LIMITE = 10; int main(){ LIMITE = 20; return LIMITE; }",
            "constante 'LIMITE' nao pode ter seu valor alterado",
        )

    def test_main_e_obrigatoria(self):
        self.compilar_erro(
            "int auxiliar(){ return 0; }",
            "programa deve declarar a funcao de entrada 'main'",
        )

    def test_chamada_de_funcao_declarada_adiante(self):
        self.compilar_ok(
            "float primeira(){ float x; x = depois(1.0); return x; } "
            "float depois(float x){ return x; } "
            "int main(){ return 0; }"
        )

    def test_sombreamento_em_bloco_interno(self):
        resultado = self.compilar_ok(
            "int main(){ int x; x=1; { int x; x=2; } return x; }"
        )
        xs = [s for s in resultado.simbolos if s.nome == "x"]
        self.assertEqual([s.nivel for s in xs], [1, 2])

    def test_identificador_de_bloco_nao_vaza(self):
        self.compilar_erro(
            "int main(){ { int y; y=1; } return y; }",
            "identificador 'y' usado antes da declaracao",
        )

    def test_snapshots_refletem_tabela_ativa(self):
        resultado = self.compilar_ok(
            "int f(){int x; x=1; return x;} int main(){int y; y=2; return y;}"
        )
        apos_remocao_f = next(
            snap for snap in resultado.snapshots_tabela
            if snap["rotulo"].startswith("Removeu escopo da funcao 'f'")
        )
        nomes = [linha[0] for linha in apos_remocao_f["linhas"]]
        self.assertIn("f", nomes)
        self.assertNotIn("x", nomes)

    def test_dangling_else_e_resolvido_para_if_mais_proximo(self):
        self.compilar_ok(
            "int main(){ if(1) if(1) return 1; else return 0; return 0; }"
        )

    def test_todas_as_producoes_sao_exercitadas(self):
        codigos = [
            path.read_text(encoding="utf-8")
            for path in (RAIZ / "examples").rglob("*.txt")
            if "ll1" not in path.parts
        ]
        codigos.append(
            "const C=1; int zero(){return 0;} int main(){int a; int b; "
            "a=(1+2)*(3-1)/2; b=zero(); {} "
            "if(a==b){print(a);} if(a!=b){print(b);} "
            "if(a<b){print(a);} if(a>=b){print(b);} return C;}"
        )

        usadas: set[int] = set()
        for codigo in codigos:
            resultado = compilar_codigo(codigo, "cobertura")
            for passo in resultado.passos_sintaticos:
                usadas.update(int(n) for n in re.findall(r"Usa (\d+):", passo.acao))

        self.assertEqual(set(Parser.PRODUCOES), usadas)


if __name__ == "__main__":
    unittest.main()
