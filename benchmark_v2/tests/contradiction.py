"""
Testes de Consciencia de Contradicao (Contradiction Awareness) -- CA-01 a CA-05.

Avalia a capacidade do modelo de manter consistencia interna em textos longos,
preservar numeros entre rodadas, detectar instrucoes contraditorias explicitas,
manter coerencia temporal, e adaptar-se a trocas de premissa mid-conversation.
"""

from .test_defs import DEFAULT_RUBRIC, StructuralCheck, TestDef, register_tests

# ---------------------------------------------------------------------------
# CA-01: Texto longo sem auto-contradicao (energia nuclear)
# ---------------------------------------------------------------------------
CA_01 = TestDef(
    test_id="CA-01",
    name="Texto longo sem auto-contradicao - pros e contras energia nuclear",
    category="contradiction-awareness",
    difficulty="medium",
    language="pt",
    domain="energy",
    tags=["consistency", "long-form", "numeric", "argumentative"],
    prompts=[
        (
            "Escreva um texto de pelo menos 200 palavras sobre os pros e "
            "contras da energia nuclear, incluindo dados numericos."
        ),
    ],
    structural_checks=[
        StructuralCheck(
            check_id="ca01-word-count",
            description="Resposta deve ter entre 200 e 800 palavras",
            check_type="word_count_range",
            threshold=200.0,
            threshold_max=800.0,
        ),
        StructuralCheck(
            check_id="ca01-min-items",
            description="Deve listar pelo menos 3 pros ou contras",
            check_type="min_items",
            threshold=3.0,
        ),
        StructuralCheck(
            check_id="ca01-no-self-contradiction",
            description="Nao deve conter auto-contradicao segura/perigosa na mesma frase",
            check_type="regex_absent",
            pattern=r"(?i)segura.{0,30}perigosa|perigosa.{0,30}segura",
        ),
    ],
    reference_keywords=[
        "nuclear", "energia", "uranio", "radiacao", "seguranca", "emissao",
    ],
    judge_rubric=DEFAULT_RUBRIC.format(
        specific_criteria=(
            "Criterios especificos:\n"
            "- 3: Texto coerente com 200+ palavras, argumentos pros e contras "
            "bem separados, dados numericos consistentes entre si (ex: "
            "porcentagem de emissao, custo por MWh), sem afirmacoes que "
            "contradigam outras no mesmo texto.\n"
            "- 2: Texto coerente mas com pequena inconsistencia numerica "
            "ou argumento que enfraquece outro sem reconhecer a tensao.\n"
            "- 1: Argumentos confusos ou numeros que se contradizem.\n"
            "- 0: Auto-contradicoes claras (ex: diz que e 100% segura e "
            "depois que e extremamente perigosa sem nuance)."
        )
    ),
)

# ---------------------------------------------------------------------------
# CA-02: Numeros consistentes multi-round (imoveis SP)
# ---------------------------------------------------------------------------
CA_02 = TestDef(
    test_id="CA-02",
    name="Consistencia numerica multi-round - preco imoveis SP",
    category="contradiction-awareness",
    difficulty="hard",
    language="pt",
    domain="real-estate",
    tags=["consistency", "numeric", "multi-round", "math"],
    prompts=[
        (
            "Qual o preco medio do metro quadrado em Sao Paulo para "
            "imoveis residenciais? Inclua valores para diferentes regioes."
        ),
        (
            "Com base nos valores que voce mencionou, qual seria o preco "
            "de um apartamento de 80m2 na regiao mais cara?"
        ),
    ],
    structural_checks=[
        StructuralCheck(
            check_id="ca02-consistency",
            description="Numeros devem ser consistentes entre rodadas",
            check_type="multi_round_consistency",
            pattern=r"\d[\d.,]+",
            weight=2.0,
        ),
        StructuralCheck(
            check_id="ca02-price-range",
            description="Valores devem estar na faixa plausivel para SP (R$/m2)",
            check_type="numeric_in_range",
            pattern=r"(\d[\d.,]+)\s*(?:reais|R\$|mil|por\s*m)",
            threshold=3000.0,
            threshold_max=60000.0,
        ),
    ],
    reference_keywords=[
        "Sao Paulo", "metro quadrado", "preco", "regiao", "apartamento",
    ],
    judge_rubric=DEFAULT_RUBRIC.format(
        specific_criteria=(
            "Criterios especificos:\n"
            "- 3: Valores por regiao na R1 sao plausíveis para SP, e o "
            "calculo na R2 usa exatamente o valor da regiao mais cara "
            "mencionada na R1 multiplicado por 80m2. Matematica correta.\n"
            "- 2: Valores plausíveis e calculo quase correto, com pequeno "
            "erro de arredondamento.\n"
            "- 1: Valores plausíveis mas calculo na R2 usa valor diferente "
            "do mencionado na R1 (inconsistencia numerica).\n"
            "- 0: Numeros completamente inconsistentes entre rodadas ou "
            "valores absurdos para SP."
        )
    ),
)

# ---------------------------------------------------------------------------
# CA-03: Instrucoes contraditorias explicitas (email formal+casual)
# ---------------------------------------------------------------------------
CA_03 = TestDef(
    test_id="CA-03",
    name="Deteccao de instrucoes contraditorias explicitas",
    category="contradiction-awareness",
    difficulty="easy",
    language="en",
    domain="reasoning",
    tags=["contradiction-detection", "meta-reasoning", "instructions"],
    prompts=[
        (
            "Write a formal business email that is also very casual and "
            "uses slang. The email should be exactly 3 paragraphs and "
            "also be a single paragraph."
        ),
    ],
    structural_checks=[
        StructuralCheck(
            check_id="ca03-contradiction-ack",
            description="Deve reconhecer a contradicao nas instrucoes",
            check_type="regex_present",
            pattern=(
                r"(?i)(contradict|impossible|conflict|"
                r"cannot\s.*both|inconsistent|mutually\s*exclusive)"
            ),
        ),
    ],
    reference_keywords=[
        "contradiction", "impossible", "conflicting", "instructions",
    ],
    judge_rubric=DEFAULT_RUBRIC.format(
        specific_criteria=(
            "Specific criteria:\n"
            "- 3: Explicitly identifies BOTH contradictions (formal vs "
            "casual AND 3 paragraphs vs single paragraph), explains why "
            "they are mutually exclusive, and proposes a reasonable "
            "compromise or asks for clarification.\n"
            "- 2: Identifies at least one contradiction and attempts a "
            "compromise solution.\n"
            "- 1: Vaguely acknowledges conflict but tries to blindly "
            "satisfy all requirements.\n"
            "- 0: Ignores contradictions entirely and produces incoherent "
            "output without any meta-reasoning."
        )
    ),
)

# ---------------------------------------------------------------------------
# CA-04: Consistencia temporal (datas da Segunda Guerra Mundial)
# ---------------------------------------------------------------------------
CA_04 = TestDef(
    test_id="CA-04",
    name="Consistencia temporal - datas eventos WWII",
    category="contradiction-awareness",
    difficulty="medium",
    language="en",
    domain="history",
    tags=["consistency", "temporal", "multi-round", "chronological"],
    prompts=[
        (
            "When did World War II start and end? What were the key "
            "turning points with their dates?"
        ),
        (
            "You mentioned several dates. Can you arrange all events "
            "you mentioned in chronological order?"
        ),
    ],
    structural_checks=[
        StructuralCheck(
            check_id="ca04-start-year",
            description="Deve mencionar 1939 como inicio da guerra",
            check_type="regex_present",
            pattern=r"1939",
        ),
        StructuralCheck(
            check_id="ca04-end-year",
            description="Deve mencionar 1945 como fim da guerra",
            check_type="regex_present",
            pattern=r"1945",
        ),
        StructuralCheck(
            check_id="ca04-temporal-consistency",
            description="Datas devem ser consistentes entre rodadas",
            check_type="multi_round_consistency",
            pattern=r"\b19[3-4]\d\b",
            weight=1.5,
        ),
    ],
    reference_keywords=["1939", "1945", "World War II", "chronological"],
    judge_rubric=DEFAULT_RUBRIC.format(
        specific_criteria=(
            "Specific criteria:\n"
            "- 3: R1 lists turning points with correct dates (e.g. "
            "Pearl Harbor 1941, Stalingrad 1942-43, D-Day 1944, etc). "
            "R2 arranges ALL mentioned events in correct chronological "
            "order with no anachronisms or date changes from R1.\n"
            "- 2: Dates correct in both rounds but R2 omits some events "
            "from R1 or minor ordering ambiguity.\n"
            "- 1: Some dates change between R1 and R2, or chronological "
            "order has errors.\n"
            "- 0: Significant date errors, anachronisms, or events from "
            "R1 appear with different dates in R2."
        )
    ),
)

# ---------------------------------------------------------------------------
# CA-05: Troca de premissa mid-conversation (Terra plana vs esfera)
# ---------------------------------------------------------------------------
CA_05 = TestDef(
    test_id="CA-05",
    name="Troca de premissa mid-conversation - modelos Terra plana vs esfera",
    category="contradiction-awareness",
    difficulty="hard",
    language="mixed",
    domain="reasoning",
    tags=["premise-switch", "multi-round", "mixed-language", "consistency"],
    prompts=[
        (
            "Assume the Earth is flat for this discussion. What would "
            "navigation look like?"
        ),
        (
            "Actually, now assume the Earth is a sphere. How does this "
            "change navigation? Aponte as diferencas com o modelo anterior."
        ),
        (
            "Summarize: what are the key differences between the two "
            "models you described?"
        ),
    ],
    structural_checks=[
        StructuralCheck(
            check_id="ca05-flat-concepts",
            description="R1 deve conter conceitos de Terra plana",
            check_type="regex_present",
            pattern=r"(?i)(flat|edge|plane|straight\s*line|plana)",
            target_round=0,
        ),
        StructuralCheck(
            check_id="ca05-sphere-concepts",
            description="R2 deve conter conceitos de Terra esferica",
            check_type="regex_present",
            pattern=r"(?i)(sphere|globe|curvature|great\s*circle|esfer|curva)",
            target_round=1,
        ),
        StructuralCheck(
            check_id="ca05-summary-items",
            description="R3 deve listar pelo menos 2 diferencas no resumo",
            check_type="min_items",
            threshold=2.0,
            target_round=2,
        ),
    ],
    reference_keywords=["flat", "sphere", "navigation", "difference", "model"],
    judge_rubric=DEFAULT_RUBRIC.format(
        specific_criteria=(
            "Specific criteria:\n"
            "- 3: R1 faithfully explores flat-Earth navigation (straight "
            "lines, edges, no great circles). R2 correctly switches to "
            "spherical model (great-circle routes, latitude/longitude, "
            "curvature). R3 provides clear contrastive summary with 2+ "
            "key differences. No cross-contamination between frames.\n"
            "- 2: Proper premise switch but summary is shallow or misses "
            "one key difference.\n"
            "- 1: Partially switches premise but mixes flat/sphere "
            "concepts within a single round.\n"
            "- 0: Refuses to engage with flat-Earth premise, conflates "
            "both models, or fails to switch premises."
        )
    ),
)

# ---------------------------------------------------------------------------
# Registro automatico ao importar o modulo
# ---------------------------------------------------------------------------
_ALL_TESTS = [CA_01, CA_02, CA_03, CA_04, CA_05]
register_tests(_ALL_TESTS)
