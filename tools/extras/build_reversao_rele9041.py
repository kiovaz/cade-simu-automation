#!/usr/bin/env python3
"""Reversao direta com o RELE DE FALTA DE FASE REAL do CADe_SIMU (classe 9041, rotulo -RFF).

Parte do exemplo `reversao_falta_fase` (relé simulado com chave+bobina), troca o degrau do relé pelo
9041 de verdade e acrescenta a chave -SF (8009, NF retentiva) em serie com a fase L3 do relé: clicar em
-SF no app = falta da fase L3. O 9041 energiza com as 3 fases presentes e comanda por ROTULO os contatos
auxiliares 7000/7001 `-RFF` (provado no app em 31/10/2026: sem L3 -> NF fecha; com L3 -> NA fecha).
Rele auxiliar -KA1 ("comando liberado"): bobina em serie com RT1 e o NA de -RFF; o resto do comando usa o
NA de -KA1 (a serie principal nao cabe na folha com RT1 + RFF + S0 + os dois ramos).

Uso: python3 tools/extras/build_reversao_rele9041.py saida.cad
O gate do projeto nao modela o 9041 (trata o contato -RFF como entrada `RFF`); a prova e o app:
  python3 tools/extras/validar_reversao_rele9041.py saida.cad     (precisa de Wine + CADe_SIMU)
"""
import copy
import json
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))
import build_spec  # noqa: E402
import layout as L  # noqa: E402

ORIGEM = TOOLS / "examples" / "reversao_falta_fase.layout.json"

# casos do app (chave = rotulo sem '-'; SF=true clica na chave = falta da fase L3). Sem bobina RFF.
TESTES = [
    {"nome": "repouso: sem falta, KA1 liberado", "entradas": {}, "esperado": ["KA1"], "esperado_lampadas": []},
    {"nome": "S1 liga horario", "entradas": {"S1": True}, "esperado": ["KA1", "KM1"], "esperado_lampadas": ["H1", "H2"]},
    {"nome": "S2 liga anti-horario", "entradas": {"S2": True}, "esperado": ["KA1", "KM2"], "esperado_lampadas": ["H1", "H3"]},
    {"nome": "selo mantem horario", "entradas": {}, "inicial": ["KA1", "KM1"], "esperado": ["KA1", "KM1"], "esperado_lampadas": ["H1", "H2"]},
    {"nome": "selo mantem anti-horario", "entradas": {}, "inicial": ["KA1", "KM2"], "esperado": ["KA1", "KM2"], "esperado_lampadas": ["H1", "H3"]},
    {"nome": "reversao direta: S2 com horario ligado inverte sem S0", "entradas": {"S2": True}, "inicial": ["KA1", "KM1"],
     "esperado": ["KA1", "KM2"], "esperado_lampadas": ["H1", "H3"]},
    {"nome": "reversao direta: S1 com anti-horario ligado inverte sem S0", "entradas": {"S1": True}, "inicial": ["KA1", "KM2"],
     "esperado": ["KA1", "KM1"], "esperado_lampadas": ["H1", "H2"]},
    {"nome": "S0 desliga horario", "entradas": {"S0": True}, "inicial": ["KA1", "KM1"], "esperado": ["KA1"], "esperado_lampadas": []},
    {"nome": "S0 desliga anti-horario", "entradas": {"S0": True}, "inicial": ["KA1", "KM2"], "esperado": ["KA1"], "esperado_lampadas": []},
    {"nome": "sobrecarga (RT1) desliga, sem acender H4", "entradas": {"RT1": True}, "inicial": ["KA1", "KM1"], "esperado": [],
     "esperado_lampadas": []},
    {"nome": "sobrecarga impede partida", "entradas": {"RT1": True, "S1": True}, "esperado": [], "esperado_lampadas": []},
    {"nome": "falta de fase desliga e acende H4", "entradas": {"SF": True}, "inicial": ["KA1", "KM1"], "esperado": [],
     "esperado_lampadas": ["H4"]},
    {"nome": "falta de fase impede partida", "entradas": {"SF": True, "S1": True}, "esperado": [], "esperado_lampadas": ["H4"]},
    {"nome": "sem auto-religamento", "entradas": {}, "esperado": ["KA1"], "esperado_lampadas": []},
]


def spec_baixa():
    d = json.loads(ORIGEM.read_text(encoding="utf-8"))
    lay = copy.deepcopy(d["layout"])
    r_aux, r_main = lay["comando"][0]["rungs"]
    # r_aux = serie[RT1, paralelo[serie[SF, bobina RFF], serie[nrff, H4]]]; r_main = serie[rff, S0, par]
    RT1 = r_aux["serie"][0]
    h4 = r_aux["serie"][1]["paralelo"][1]                 # serie[nrff (7001 -RFF), H4]
    rff, S0, par = r_main["serie"]                         # rff = 7000 -RFF (NA do rele de fase)
    ka_coil = ["KA1", "9000", "-KA1"]
    ka_na = ["ka", "7000", "-KA1"]
    aux = {"paralelo": [{"serie": [RT1, rff, ka_coil]}, h4]}
    main = {"serie": [ka_na, S0, par]}
    lay["comando"][0]["rungs"] = [aux, main]
    baixa = L.compilar(lay)
    # relé 9041 sob os trilhos de fase: p1<-L1, p2<-L2, p3<-SF(8009)<-L3 (SF A em L3, B no p3, mesmo x)
    xr = 150
    baixa["simbolos"] += [
        {"classe": "8009", "x": xr + 12, "y": 29, "rotulo": "-SF", "id": "SF"},
        {"classe": "9041", "x": xr, "y": 50, "rotulo": "-RFF", "id": "RFF9041"},
    ]
    baixa["conexoes"] += [
        {"de": ["RFF9041", "p1"], "para": ["L1", "rail"]},
        {"de": ["RFF9041", "p2"], "para": ["L2", "rail"]},
        {"de": ["SF", "A"], "para": ["L3", "rail"]},
        {"de": ["SF", "B"], "para": ["RFF9041", "p3"]},
    ]
    baixa["titulo"] = "REVERSAO COM RELE DE FALTA DE FASE 9041"
    baixa["testes"] = TESTES
    return baixa


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "reversao_rele9041.cad"
    r = build_spec.construir(spec_baixa(), out)
    print(json.dumps({k: r[k] for k in r if k in ("ok", "erros", "avisos")}, ensure_ascii=False, indent=1)[:1500])
