"""
Testes de Adaptacao de Tarefa (Task Adaptation) -- TA-01 a TA-05.

Avalia a capacidade do modelo de adaptar-se a diferentes formatos de saida,
combinar raciocinio criativo e tecnico, alternar idiomas, seguir restricoes
compostas, e manter coerencia logica em cadeias de deducao multi-round.
"""

from .test_defs import DEFAULT_RUBRIC, StructuralCheck, TestDef, register_tests

# --- TA-01: Opiniao vs Fato - frameworks JS ------------------------------------
TA_01 = TestDef(
    test_id="TA-01",
    name="Opiniao vs Fato - comparacao frameworks JavaScript",
    category="task-adaptation",
    difficulty="medium",
    language="pt",
    domain="software",
    tags=["fact-opinion", "comparison", "structured"],
    prompts=[
        "Compare React, Vue e Angular. Separe claramente fatos objetivos "
        "(performance, tamanho, comunidade) de opinioes pessoais.",
    ],
    structural_checks=[
        StructuralCheck(
            check_id="ta01-react", description="Deve mencionar React",
            check_type="regex_present", pattern=r"(?i)React",
        ),
        StructuralCheck(
            check_id="ta01-vue", description="Deve mencionar Vue",
            check_type="regex_present", pattern=r"(?i)Vue",
        ),
        StructuralCheck(
            check_id="ta01-angular", description="Deve mencionar Angular",
            check_type="regex_present", pattern=r"(?i)Angular",
        ),
        StructuralCheck(
            check_id="ta01-separation-markers",
            description="Deve conter marcadores de separacao fato/opiniao",
            check_type="regex_present",
            pattern=r"(?i)(fato|objetivo|opini[aã]o|subjetivo|pessoal)",
        ),
    ],
    reference_keywords=[
        "React", "Vue", "Angular", "framework", "JavaScript", "fato", "opiniao",
    ],
    judge_rubric=DEFAULT_RUBRIC.format(specific_criteria=(
        "Criterios especificos:\n"
        "- 3: Separa claramente fatos (performance, bundle, comunidade) de "
        "opinioes (preferencia, facilidade subjetiva), cobre os 3 frameworks.\n"
        "- 2: Menciona os 3 e tenta separar, mas divisao parcial ou superficial.\n"
        "- 1: Compara os frameworks mas mistura fatos e opinioes.\n"
        "- 0: Nao compara os 3 ou nao faz distincao fato/opiniao."
    )),
)

# --- TA-02: Calculo com verificacao de passos (trens) --------------------------
TA_02 = TestDef(
    test_id="TA-02",
    name="Calculo com verificacao de passos - problema de trens SP-Rio",
    category="task-adaptation",
    difficulty="hard",
    language="pt",
    domain="mathematics",
    tags=["math", "verification", "multi-round", "step-by-step"],
    prompts=[
        "Um trem parte de Sao Paulo as 8h viajando a 120km/h. Outro "
        "parte do Rio as 9h a 150km/h. A distancia SP-Rio e 430km. "
        "A que horas e onde se encontram?",
        "Mostre a verificacao: substitua o tempo encontrado nas "
        "equacoes de ambos os trens e confirme que as distancias somam 430km.",
    ],
    structural_checks=[
        StructuralCheck(
            check_id="ta02-time-answer",
            description="Deve apresentar horario de encontro (HH:MM ou Hh)",
            check_type="regex_present",
            pattern=r"\d{1,2}[h:]\d{2}", target_round=0,
        ),
        StructuralCheck(
            check_id="ta02-step-by-step",
            description="Resolucao deve ter pelo menos 5 linhas",
            check_type="min_lines", threshold=5.0, target_round=0,
        ),
        StructuralCheck(
            check_id="ta02-verification",
            description="R2 deve conter verificacao ou confirmacao",
            check_type="regex_present",
            pattern=r"(?i)(verifica|confirma|substitui|checking|verify|prova)",
            target_round=1,
        ),
    ],
    reference_keywords=[
        "velocidade", "distancia", "tempo", "encontro",
        "km", "120", "150", "430",
    ],
    judge_rubric=DEFAULT_RUBRIC.format(specific_criteria=(
        "Criterios especificos:\n"
        "- 3: Equacoes corretas (d1=120*t, d2=150*(t-1), d1+d2=430), "
        "horario correto, R2 substitui e confirma soma=430km.\n"
        "- 2: Setup correto mas verificacao incompleta ou com arredondamento.\n"
        "- 1: Abordagem correta mas erro no calculo ou verificacao errada.\n"
        "- 0: Setup errado, resposta incorreta, ou nao tenta verificar."
    )),
)

# --- TA-03: Mudanca de formato mid-task (lista -> tabela) ----------------------
TA_03 = TestDef(
    test_id="TA-03",
    name="Mudanca de formato mid-task - lista para tabela markdown",
    category="task-adaptation",
    difficulty="easy",
    language="en",
    domain="software",
    tags=["format-switch", "multi-round", "markdown", "list-to-table"],
    prompts=[
        "List the top 5 programming languages by popularity with their key features.",
        "Now convert that information into a markdown table with columns: "
        "Language, Popularity Rank, Key Feature, Year Created.",
    ],
    structural_checks=[
        StructuralCheck(
            check_id="ta03-list-items",
            description="R1 deve conter ao menos 5 itens de lista",
            check_type="min_items", threshold=5.0, target_round=0,
        ),
        StructuralCheck(
            check_id="ta03-table-markers",
            description="R2 deve conter marcadores de tabela markdown (pipes)",
            check_type="regex_present",
            pattern=r"\|.*\|", target_round=1,
        ),
        StructuralCheck(
            check_id="ta03-table-lines",
            description="R2 deve ter pelo menos 6 linhas (header+sep+5 rows)",
            check_type="min_lines", threshold=6.0, target_round=1,
        ),
    ],
    reference_keywords=[
        "Python", "JavaScript", "table", "language", "popularity",
    ],
    judge_rubric=DEFAULT_RUBRIC.format(specific_criteria=(
        "Specific criteria:\n"
        "- 3: R1 is a well-formatted list with 5 languages. R2 converts to "
        "valid markdown table with all 4 columns, preserving R1 content.\n"
        "- 2: Both formats present but R2 table missing a column or 1-2 diffs.\n"
        "- 1: Table attempted but invalid markdown or significant content loss.\n"
        "- 0: No format change, or content completely different between rounds."
    )),
)

# --- TA-04: Tarefa criativa com restricoes tecnicas (haiku + ciencia) ----------
TA_04 = TestDef(
    test_id="TA-04",
    name="Tarefa criativa com restricoes tecnicas - haiku quantum computing",
    category="task-adaptation",
    difficulty="medium",
    language="en",
    domain="physics",
    tags=["creative", "technical", "poetry", "quantum"],
    prompts=[
        "Write a haiku about quantum computing. Then explain the "
        "scientific accuracy of each line.",
    ],
    structural_checks=[
        StructuralCheck(
            check_id="ta04-poem-present",
            description="Deve conter estrutura de haiku (poema curto)",
            check_type="regex_present",
            pattern=r"(?i)(haiku|poem|verse|\n.{5,20}\n.{5,20}\n.{5,20})",
        ),
        StructuralCheck(
            check_id="ta04-word-count",
            description="Resposta deve ter entre 50 e 400 palavras",
            check_type="word_count_range",
            threshold=50.0, threshold_max=400.0,
        ),
        StructuralCheck(
            check_id="ta04-quantum-terms",
            description="Explicacao deve conter termos quanticos reais",
            check_type="regex_present",
            pattern=r"(?i)(quantum|qubit|superposition|entanglement|decoherence|wave)",
        ),
    ],
    reference_keywords=["haiku", "quantum", "computing", "syllable", "accurate"],
    judge_rubric=DEFAULT_RUBRIC.format(specific_criteria=(
        "Specific criteria:\n"
        "- 3: Haiku follows 5-7-5 (or close), quantum-related content, each "
        "line explained with scientifically accurate quantum phenomena.\n"
        "- 2: Creative and quantum-related but syllable count off or shallow.\n"
        "- 1: Poem or explanation present but not both, or inaccuracies.\n"
        "- 0: No haiku structure, or explanation is scientifically wrong."
    )),
)

# --- TA-05: Multi-step reasoning com troca de idioma (logica formal) -----------
TA_05 = TestDef(
    test_id="TA-05",
    name="Raciocinio logico multi-step com troca de idioma",
    category="task-adaptation",
    difficulty="hard",
    language="mixed",
    domain="reasoning",
    tags=["logic", "multi-round", "mixed-language", "deduction", "formal"],
    prompts=[
        "All mammals are warm-blooded. All whales are mammals. "
        "All dolphins are mammals. Some warm-blooded animals can fly. "
        "What can you conclude about whales and dolphins?",
        "Agora adicione: 'Nenhum animal aquatico pode voar.' "
        "Isso muda suas conclusoes sobre baleias e golfinhos?",
        "Summarize all valid conclusions in a numbered list.",
    ],
    structural_checks=[
        StructuralCheck(
            check_id="ta05-warm-blooded",
            description="Deve concluir que baleias/golfinhos sao de sangue quente",
            check_type="regex_present",
            pattern=r"(?i)(warm[- ]blooded|sangue quente)",
        ),
        StructuralCheck(
            check_id="ta05-logical-connectors",
            description="Deve usar conectivos logicos formais",
            check_type="regex_present",
            pattern=r"(?i)(therefore|thus|conclude|hence|portanto|logo|conclui)",
        ),
        StructuralCheck(
            check_id="ta05-summary-items",
            description="R3 deve listar pelo menos 3 conclusoes numeradas",
            check_type="min_items", threshold=3.0, target_round=2,
        ),
    ],
    reference_keywords=[
        "mammal", "warm-blooded", "whale", "dolphin",
        "conclude", "fly", "aquatic",
    ],
    judge_rubric=DEFAULT_RUBRIC.format(specific_criteria=(
        "Specific criteria:\n"
        "- 3: R1 deduces warm-blooded (valid), does NOT conclude they can fly. "
        "R2 integrates new premise, concludes whales/dolphins cannot fly. "
        "R3 lists all valid conclusions numbered. Language switch smooth.\n"
        "- 2: Mostly correct but one minor invalid inference or R3 incomplete.\n"
        "- 1: Some valid deductions but also invalid inferences (e.g. can fly).\n"
        "- 0: Invalid logic, false conclusions, or fails to integrate R2 premise."
    )),
)

# --- Registro automatico ao importar o modulo ----------------------------------
_ALL_TESTS = [TA_01, TA_02, TA_03, TA_04, TA_05]
register_tests(_ALL_TESTS)
