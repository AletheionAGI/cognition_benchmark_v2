"""
Testes de Fundamentacao Factual (Factual Grounding) -- FG-01 a FG-05.

Avalia a capacidade do modelo de fornecer informacoes factuais precisas,
com numeros verificaveis, distinguindo dados confirmados de estimativas,
e evitando fabricacao de fontes ou valores sem hedging adequado.
"""

from .test_defs import DEFAULT_RUBRIC, StructuralCheck, TestDef, register_tests

# ---------------------------------------------------------------------------
# FG-01: 5 fatos do sistema solar com numeros
# ---------------------------------------------------------------------------
FG_01 = TestDef(
    test_id="FG-01",
    name="Fatos do sistema solar com numeros verificaveis",
    category="factual-grounding",
    difficulty="medium",
    language="pt",
    domain="astronomy",
    tags=["factual", "numeric", "astronomy", "list"],
    prompts=[
        (
            "Liste 5 fatos sobre o sistema solar incluindo numeros "
            "especificos (distancias, temperaturas, tamanhos)."
        ),
    ],
    structural_checks=[
        StructuralCheck(
            check_id="fg01-min-items",
            description="Deve listar pelo menos 5 fatos",
            check_type="min_items",
            threshold=5.0,
        ),
        StructuralCheck(
            check_id="fg01-word-count",
            description="Resposta deve ter entre 100 e 600 palavras",
            check_type="word_count_range",
            threshold=100.0,
            threshold_max=600.0,
        ),
    ],
    reference_keywords=["Sol", "planeta", "Terra", "Jupiter", "orbita"],
    reference_numeric_ranges={
        "dist_terra_sol_km": (140e6, 155e6),
        "planetas": (8, 8),
    },
    ground_truth=(
        "O sistema solar possui 8 planetas. A distancia media da Terra "
        "ao Sol e de aproximadamente 149.6 milhoes de km."
    ),
    judge_rubric=DEFAULT_RUBRIC.format(
        specific_criteria=(
            "Criterios especificos:\n"
            "- 3: Lista 5+ fatos com numeros precisos e verificaveis "
            "(distancias, temperaturas, tamanhos), todos corretos ou "
            "dentro de margens razoaveis.\n"
            "- 2: Lista 5 fatos mas alguns numeros sao imprecisos ou "
            "faltam dados numericos em 1-2 itens.\n"
            "- 1: Menos de 5 fatos ou numeros significativamente errados.\n"
            "- 0: Fatos inventados ou numeros completamente incorretos."
        )
    ),
)

# ---------------------------------------------------------------------------
# FG-02: Velocidade da luz e constantes fisicas
# ---------------------------------------------------------------------------
FG_02 = TestDef(
    test_id="FG-02",
    name="Velocidade da luz e constantes fisicas fundamentais",
    category="factual-grounding",
    difficulty="medium",
    language="en",
    domain="physics",
    tags=["factual", "numeric", "physics", "constants"],
    prompts=[
        (
            "What is the speed of light in vacuum? Also mention Planck's "
            "constant and Boltzmann's constant with their values."
        ),
    ],
    structural_checks=[
        StructuralCheck(
            check_id="fg02-speed-of-light",
            description="Deve mencionar valor da velocidade da luz",
            check_type="regex_present",
            pattern=r"299|3.*10\^?8|300,?000",
        ),
        StructuralCheck(
            check_id="fg02-planck",
            description="Deve mencionar constante de Planck",
            check_type="regex_present",
            pattern=r"(?i)planck|6\.626",
        ),
    ],
    reference_keywords=[
        "speed of light", "299792458", "Planck", "Boltzmann",
        "constant", "m/s",
    ],
    reference_numeric_ranges={
        "speed_of_light_ms": (299792000, 299793000),
    },
    ground_truth=(
        "Speed of light = 299,792,458 m/s. "
        "Planck's constant = 6.626e-34 J*s. "
        "Boltzmann's constant = 1.381e-23 J/K."
    ),
    judge_rubric=DEFAULT_RUBRIC.format(
        specific_criteria=(
            "Specific criteria:\n"
            "- 3: All three constants correct with proper units "
            "(c=299792458 m/s, h=6.626e-34 J*s, k_B=1.381e-23 J/K). "
            "Clear explanation of each.\n"
            "- 2: Two of three constants correct with units.\n"
            "- 1: Only one constant correct or values without units.\n"
            "- 0: Values wrong or constants confused/fabricated."
        )
    ),
)

# ---------------------------------------------------------------------------
# FG-03: Cadeia de fatos geograficos verificaveis (5 maiores paises)
# ---------------------------------------------------------------------------
FG_03 = TestDef(
    test_id="FG-03",
    name="5 maiores paises do mundo em area territorial",
    category="factual-grounding",
    difficulty="easy",
    language="pt",
    domain="geography",
    tags=["factual", "numeric", "geography", "list", "ranking"],
    prompts=[
        (
            "Quais sao os 5 maiores paises do mundo em area territorial? "
            "Inclua a area aproximada de cada um."
        ),
    ],
    structural_checks=[
        StructuralCheck(
            check_id="fg03-min-items",
            description="Deve listar pelo menos 5 paises",
            check_type="min_items",
            threshold=5.0,
        ),
        StructuralCheck(
            check_id="fg03-russia",
            description="Deve mencionar Russia como maior pais",
            check_type="regex_present",
            pattern=r"(?i)R[uú]ssia",
        ),
        StructuralCheck(
            check_id="fg03-canada",
            description="Deve mencionar Canada",
            check_type="regex_present",
            pattern=r"(?i)Canad[aá]",
        ),
        StructuralCheck(
            check_id="fg03-others",
            description="Deve mencionar China, Brasil ou EUA",
            check_type="regex_present",
            pattern=r"(?i)China|Brasil|Estados Unidos",
        ),
    ],
    reference_keywords=[
        "Russia", "Canada", "China", "Estados Unidos", "Brasil",
        "area", "km",
    ],
    reference_numeric_ranges={
        "russia_area_km2": (16e6, 18e6),
        "canada_area_km2": (9e6, 10.5e6),
    },
    judge_rubric=DEFAULT_RUBRIC.format(
        specific_criteria=(
            "Criterios especificos:\n"
            "- 3: Lista correta dos 5 maiores (Russia, Canada, "
            "EUA/China, China/EUA, Brasil) com areas aproximadas "
            "razoaveis para cada um.\n"
            "- 2: Ranking correto mas areas imprecisas ou faltando "
            "para 1-2 paises.\n"
            "- 1: Ranking parcialmente errado ou areas muito imprecisas.\n"
            "- 0: Ranking errado ou paises inventados no top 5."
        )
    ),
)

# ---------------------------------------------------------------------------
# FG-04: Dados economicos com fonte vs fabricacao (GDP top 3)
# ---------------------------------------------------------------------------
FG_04 = TestDef(
    test_id="FG-04",
    name="GDP das 3 maiores economias com transparencia de fonte",
    category="factual-grounding",
    difficulty="hard",
    language="en",
    domain="economics",
    tags=["factual", "numeric", "economics", "sourcing", "anti-hallucination"],
    anti_hallucination=True,
    prompts=[
        (
            "What are the GDP values of the top 3 economies in the world? "
            "Cite your sources or indicate if these are approximate values."
        ),
    ],
    structural_checks=[
        StructuralCheck(
            check_id="fg04-usa",
            description="Deve mencionar Estados Unidos",
            check_type="regex_present",
            pattern=r"(?i)United States|US[A ]",
        ),
        StructuralCheck(
            check_id="fg04-china",
            description="Deve mencionar China",
            check_type="regex_present",
            pattern=r"(?i)China",
        ),
        StructuralCheck(
            check_id="fg04-uncertainty",
            description="Deve indicar natureza aproximada dos dados",
            check_type="regex_present",
            pattern=r"(?i)approximate|estimated|as of|according to",
        ),
    ],
    reference_keywords=["GDP", "United States", "China", "trillion", "economy"],
    judge_rubric=DEFAULT_RUBRIC.format(
        specific_criteria=(
            "Specific criteria:\n"
            "- 3: Correct top 3 ranking (US, China, Japan/Germany), "
            "GDP values in reasonable range, explicit hedging about "
            "data recency, mentions source or states approximation.\n"
            "- 2: Correct ranking with values but hedging is minimal.\n"
            "- 1: Ranking mostly correct but presents fabricated precise "
            "GDP figures as definitive facts.\n"
            "- 0: Wrong ranking, wildly inaccurate values, or fabricated "
            "sources. STRONGLY penalize fabricated precise GDP numbers "
            "presented without any hedging or uncertainty markers."
        )
    ),
)

# ---------------------------------------------------------------------------
# FG-05: Fatos biologicos multi-dominio (DNA, celulas, evolucao)
# ---------------------------------------------------------------------------
FG_05 = TestDef(
    test_id="FG-05",
    name="Fatos biologicos multi-dominio - genoma, celulas, genes",
    category="factual-grounding",
    difficulty="hard",
    language="mixed",
    domain="biology",
    tags=["factual", "numeric", "biology", "multi-round", "anti-hallucination"],
    anti_hallucination=True,
    prompts=[
        (
            "How many base pairs does the human genome contain? "
            "How many cells are in the human body?"
        ),
        (
            "Agora me diga: quantos genes codificadores de proteina "
            "existem no genoma humano?"
        ),
    ],
    structural_checks=[
        StructuralCheck(
            check_id="fg05-base-pairs",
            description="Deve mencionar ~3 bilhoes de pares de bases",
            check_type="regex_present",
            pattern=r"3.*bilh|3.*billion|3\.2|3\.1",
        ),
        StructuralCheck(
            check_id="fg05-cells",
            description="Deve mencionar ~37 trilhoes de celulas",
            check_type="regex_present",
            pattern=r"trilh|trillion|37",
        ),
        StructuralCheck(
            check_id="fg05-protein-genes",
            description="Deve mencionar ~20.000 genes codificadores",
            check_type="regex_present",
            pattern=r"20.?000|21.?000|19.?000",
            target_round=1,
        ),
    ],
    reference_keywords=[
        "genome", "base pairs", "billion", "cells", "trillion",
        "genes", "protein",
    ],
    reference_numeric_ranges={
        "base_pairs_billion": (3.0, 3.3),
        "cells_trillion": (30, 40),
        "protein_genes_thousands": (19, 22),
    },
    ground_truth=(
        "Human genome: ~3.2 billion base pairs. "
        "Human body: ~37 trillion cells. "
        "Protein-coding genes: ~20,000-21,000."
    ),
    judge_rubric=DEFAULT_RUBRIC.format(
        specific_criteria=(
            "Specific criteria:\n"
            "- 3: All three values correct (~3.2B base pairs, ~37T cells, "
            "~20-21k protein-coding genes), handles language switch "
            "naturally, uses appropriate hedging for estimates.\n"
            "- 2: Two of three values correct, or all three present but "
            "one slightly outside expected range.\n"
            "- 1: Only one value correct or values given without context.\n"
            "- 0: Values fabricated, wildly inaccurate, or fails to "
            "address the multi-round prompts. STRONGLY penalize "
            "hallucinated precise numbers without hedging."
        )
    ),
)

# ---------------------------------------------------------------------------
# Registro automatico ao importar o modulo
# ---------------------------------------------------------------------------
_ALL_TESTS = [FG_01, FG_02, FG_03, FG_04, FG_05]
register_tests(_ALL_TESTS)
