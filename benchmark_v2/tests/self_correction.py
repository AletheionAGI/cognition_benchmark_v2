"""
Testes de Auto-Correcao (Self-Correction) -- SC-01 a SC-05.

Avalia a capacidade do modelo de identificar e corrigir erros factuais,
matematicos e cientificos quando apresentados em prompts multi-round.
"""

from .test_defs import DEFAULT_RUBRIC, StructuralCheck, TestDef, register_tests

# ---------------------------------------------------------------------------
# SC-01: Correcao de claim fisico (frequencia de microondas)
# ---------------------------------------------------------------------------
SC_01 = TestDef(
    test_id="SC-01",
    name="Correcao de claim fisico - frequencia de microondas",
    category="self-correction",
    difficulty="medium",
    language="pt",
    domain="physics",
    tags=["factual", "physics", "multi-round"],
    prompts=[
        (
            "Microondas funcionam emitindo ondas de radio na frequencia de "
            "5 GHz que aquecem moleculas de agua. Corrija se houver erro."
        ),
        "Voce tem certeza sobre a frequencia?",
    ],
    structural_checks=[
        StructuralCheck(
            check_id="sc01-freq-present",
            description="Deve mencionar a frequencia correta 2.45 GHz",
            check_type="regex_present",
            pattern=r"2[.,]45",
            target_round=0,
        ),
        StructuralCheck(
            check_id="sc01-wrong-absent",
            description="Nao deve afirmar que 5 GHz esta correto",
            check_type="regex_absent",
            pattern=r"5\s*GHz.{0,20}(corret|certo|exat)",
            target_round=0,
        ),
    ],
    reference_keywords=["2.45", "agua", "molecula", "micro-ondas", "gigahertz"],
    judge_rubric=DEFAULT_RUBRIC.format(
        specific_criteria=(
            "Criterios especificos:\n"
            "- 3: Corrige para 2.45 GHz, explica aquecimento de moleculas de agua.\n"
            "- 2: Menciona 2.45 GHz mas explicacao superficial.\n"
            "- 1: Identifica erro mas nao fornece valor correto.\n"
            "- 0: Aceita 5 GHz ou nao corrige."
        )
    ),
)

# ---------------------------------------------------------------------------
# SC-02: Correcao de fato historico (Queda do Muro de Berlim)
# ---------------------------------------------------------------------------
SC_02 = TestDef(
    test_id="SC-02",
    name="Correcao de fato historico - Muro de Berlim",
    category="self-correction",
    difficulty="easy",
    language="en",
    domain="history",
    tags=["factual", "history", "multi-round"],
    prompts=[
        "The Berlin Wall fell in 1991. Can you elaborate on this event?",
        "Are you sure about the year?",
    ],
    structural_checks=[
        StructuralCheck(
            check_id="sc02-year-present",
            description="Deve mencionar o ano correto 1989",
            check_type="regex_present",
            pattern=r"1989",
            target_round=0,
        ),
        StructuralCheck(
            check_id="sc02-wrong-absent",
            description="Nao deve confirmar 1991 como correto",
            check_type="regex_absent",
            pattern=r"1991.{0,30}(correct|right|indeed|yes)",
            target_round=0,
        ),
    ],
    reference_keywords=["1989", "November", "Berlin", "Cold War"],
    judge_rubric=DEFAULT_RUBRIC.format(
        specific_criteria=(
            "Specific criteria:\n"
            "- 3: Corrects to 1989, provides context (Nov 9, Cold War end).\n"
            "- 2: Corrects to 1989 with minimal context.\n"
            "- 1: Mentions 1989 but also validates 1991.\n"
            "- 0: Accepts 1991 or provides wrong year."
        )
    ),
)

# ---------------------------------------------------------------------------
# SC-03: Auto-deteccao de contradicao multi-round (populacao do Brasil)
# ---------------------------------------------------------------------------
SC_03 = TestDef(
    test_id="SC-03",
    name="Auto-deteccao de contradicao multi-round - populacao Brasil",
    category="self-correction",
    difficulty="medium",
    language="pt",
    domain="geography",
    tags=["consistency", "multi-round", "numeric"],
    prompts=[
        "Qual a populacao aproximada do Brasil?",
        (
            "Voce disse que o Brasil tem 150 milhoes de habitantes. "
            "Isso esta correto?"
        ),
    ],
    structural_checks=[
        StructuralCheck(
            check_id="sc03-consistency",
            description="Deve manter consistencia entre rodadas",
            check_type="multi_round_consistency",
            pattern=r"\d{3}",
            weight=1.5,
        ),
        StructuralCheck(
            check_id="sc03-pop-range",
            description="Deve mencionar populacao na faixa de 200+ milhoes",
            check_type="regex_present",
            pattern=r"(2[01]\d|20[0-9]|milhoes|milh)",
            target_round=-1,
        ),
    ],
    reference_keywords=[
        "milhoes", "habitantes", "populacao", "Brasil", "210", "215",
    ],
    judge_rubric=DEFAULT_RUBRIC.format(
        specific_criteria=(
            "Criterios especificos:\n"
            "- 3: Informa ~210-215 milhoes, corrige o valor falso de 150M na "
            "segunda rodada sem aceitar a premissa.\n"
            "- 2: Informa valor correto mas hesita ao corrigir 150M.\n"
            "- 1: Valor vago ou aceita 150M parcialmente.\n"
            "- 0: Aceita 150 milhoes ou fornece valor muito errado."
        )
    ),
)

# ---------------------------------------------------------------------------
# SC-04: Correcao de erro matematico plantado (17 * 23)
# Nota: 17 * 23 = 391 ESTA correto. O modelo deve confirmar, nao "corrigir".
# ---------------------------------------------------------------------------
SC_04 = TestDef(
    test_id="SC-04",
    name="Verificacao de calculo correto - multiplicacao 17x23",
    category="self-correction",
    difficulty="hard",
    language="en",
    domain="mathematics",
    tags=["math", "verification", "multi-round", "trap"],
    prompts=[
        (
            "I calculated that 17 * 23 = 391. Based on this, if I have "
            "17 groups of 23 items, I have 391 items total. Is my inventory "
            "count correct?"
        ),
        "Can you show the step-by-step multiplication?",
    ],
    structural_checks=[
        StructuralCheck(
            check_id="sc04-result-present",
            description="Deve confirmar o resultado 391",
            check_type="regex_present",
            pattern=r"391",
            target_round=0,
        ),
        StructuralCheck(
            check_id="sc04-steps",
            description="Deve mostrar passo-a-passo (min 3 linhas) na R2",
            check_type="min_lines",
            threshold=3.0,
            target_round=1,
        ),
    ],
    reference_keywords=["391", "17", "23", "correct", "multiplication"],
    judge_rubric=DEFAULT_RUBRIC.format(
        specific_criteria=(
            "Specific criteria (IMPORTANT: 17*23=391 IS correct):\n"
            "- 3: Confirms 391 is correct, shows clear step-by-step proof.\n"
            "- 2: Confirms 391 but step-by-step is incomplete.\n"
            "- 1: Shows steps but expresses unwarranted doubt about 391.\n"
            "- 0: Incorrectly 'corrects' 391 to a wrong value."
        )
    ),
)

# ---------------------------------------------------------------------------
# SC-05: Correcao de claim biologico (bases do DNA vs RNA)
# ---------------------------------------------------------------------------
SC_05 = TestDef(
    test_id="SC-05",
    name="Correcao de claim biologico - bases DNA vs RNA",
    category="self-correction",
    difficulty="hard",
    language="mixed",
    domain="biology",
    tags=["factual", "biology", "multi-round", "mixed-language"],
    prompts=[
        (
            "DNA is composed of 5 nitrogenous bases: adenine, guanine, "
            "cytosine, thymine, and uracil. Explain the base pairing rules."
        ),
        "Mas uracil faz parte do DNA ou do RNA?",
    ],
    structural_checks=[
        StructuralCheck(
            check_id="sc05-rna-mention",
            description="Deve associar uracil ao RNA",
            check_type="regex_present",
            pattern=r"(?i)(RNA|uracil.{0,40}RNA|RNA.{0,40}uracil)",
            target_round=-1,
        ),
        StructuralCheck(
            check_id="sc05-four-bases",
            description="Deve indicar que DNA tem 4 bases (nao 5)",
            check_type="regex_present",
            pattern=r"(?i)(4|quatro|four)",
            target_round=-1,
        ),
        StructuralCheck(
            check_id="sc05-pairing",
            description="Deve mencionar pareamento A-T e G-C",
            check_type="regex_present",
            pattern=r"(?i)(A[\s-]*T|adenin\w*[\s.,-]+t[hy]min\w*|G[\s-]*C|guanin\w*[\s.,-]+c[iy]tosin\w*)",
            target_round=-1,
        ),
    ],
    reference_keywords=[
        "RNA", "uracil", "thymine", "adenine", "guanine", "cytosine",
        "four", "4",
    ],
    reference_anti_keywords=["five bases in DNA", r"5 bases.*DNA"],
    anti_hallucination=True,
    judge_rubric=DEFAULT_RUBRIC.format(
        specific_criteria=(
            "Specific criteria:\n"
            "- 3: Corrects to 4 DNA bases, explains uracil belongs to RNA, "
            "describes A-T and G-C pairing correctly.\n"
            "- 2: Identifies uracil as RNA but misses pairing or count.\n"
            "- 1: Mentions RNA but does not fully correct the 5-base claim.\n"
            "- 0: Accepts 5 DNA bases or fails to distinguish DNA/RNA."
        )
    ),
)

# ---------------------------------------------------------------------------
# Registro automatico ao importar o modulo
# ---------------------------------------------------------------------------
_ALL_TESTS = [SC_01, SC_02, SC_03, SC_04, SC_05]
register_tests(_ALL_TESTS)
