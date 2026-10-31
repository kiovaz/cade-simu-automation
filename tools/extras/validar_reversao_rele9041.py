#!/usr/bin/env python3
"""Valida no CADe_SIMU (Wine) o .cad de build_reversao_rele9041.py. Uso:
  DISPLAY=:2 CADE_DIR=<pasta do app> python3 tools/extras/validar_reversao_rele9041.py saida.cad [relatorio.json]
Fecha os disjuntores Q1/Q2 antes de cada caso (no app eles iniciam abertos)."""
import json
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))
import app_sim  # noqa: E402
from extras.build_reversao_rele9041 import TESTES  # noqa: E402

if __name__ == "__main__":
    cad = sys.argv[1]
    saida = str(Path(cad).with_suffix("")) + "_app"
    r = app_sim.executar_casos(cad, TESTES, saida=saida, verbose=False, ligar_disjuntores=True)
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(json.dumps(r, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("APROVADO NO APP" if r.get("ok") else "REPROVADO", r.get("erro") or "")
    for c in r.get("casos", []):
        print(f"[{c.get('resultado'):>13}] {c['nome']} | obtido={c.get('obtido')} lamp={c.get('obtido_lampadas')} "
              f"esperado={c.get('esperado')} lamp_esp={c.get('esperado_lampadas')} {c.get('motivo', '')}")
    sys.exit(0 if r.get("ok") else 1)
