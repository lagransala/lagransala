# Evals con MLflow y Optimización DSPy

**Fecha:** 2026-04-27
**Estado:** Aprobado

## Objetivo

Dos fases independientes:

1. **Fase 1** — Framework de evaluación con MLflow para comparar modelos (cloud vs local Ollama)
2. **Fase 2** — Reescribir el extractor usando DSPy y optimizar con BootstrapFewShot

MLflow es dependencia exclusiva de `evals/` (dev/experimentación). La aplicación principal no lo importa.

---

## Fase 1: MLflow Evals

### Estructura

```
evals/
├── data/
│   ├── annotated/          # ejemplos .json anotados manualmente (30-80)
│   └── schema.py           # Pydantic models para formato de anotación
├── metrics/
│   ├── event_matching.py   # fuzzy match evento esperado vs extraído
│   └── field_accuracy.py   # accuracy por campo
├── annotate.py             # descarga página → muestra markdown → guarda anotación
├── run_eval.py             # lanza extractor contra dataset, loguea en MLflow
└── README.md
```

### Formato de anotación

```json
{
  "url": "https://venue.com/agenda",
  "venue_slug": "lagransala",
  "content_markdown": "...",
  "expected": {
    "events": [
      {
        "title": "Título del evento",
        "schedule": ["2026-04-28T20:00:00"],
        "category": "cine",
        "price": "8.00",
        "author": null,
        "duration": null,
        "description": "...",
        "tags": []
      }
    ],
    "empty_reason": null
  },
  "annotated_at": "2026-04-27"
}
```

### Métrica combinada

```
score = 0.5 × event_f1 + 0.5 × field_accuracy
```

**event_f1:** precision y recall sobre eventos encontrados.
- Matching: `rapidfuzz.fuzz.token_sort_ratio(title_a, title_b) >= 80`
- Sin tolerancia de fechas en el matching — las fechas se evalúan en field_accuracy
- TP: evento esperado con match en extraídos
- FP: evento extraído sin match en esperados
- FN: evento esperado sin match en extraídos

**field_accuracy:** para cada par (esperado, extraído) matched, media de campos correctos:

| Campo | Criterio |
|-------|----------|
| `title` | token_sort_ratio ≥ 80 |
| `schedule` | cada datetime exacto (set intersection / union) |
| `category` | exact enum match |
| `price` | exact Decimal match |
| `author` | token_sort_ratio ≥ 80, o ambos null |
| `duration` | exact timedelta match, o ambos null |
| `description` | token_sort_ratio ≥ 60 |

### MLflow runs

Cada ejecución de `run_eval.py` crea un run con:

- **params:** `model`, `extractor_type`, `dataset_size`, `dataset_version`
- **metrics:** `event_precision`, `event_recall`, `event_f1`, `field_accuracy`, `score`
- **artifacts:** tabla CSV con resultados por ejemplo (url, score, errores)

Comparativa objetivo en Fase 1:

| Run | modelo | extractor_type |
|-----|--------|----------------|
| baseline-cloud | groq/gpt-oss-120b | groq |
| baseline-local | ollama/qwen2.5:7b | litellm |

---

## Fase 2: DSPy + BootstrapFewShot

### Módulo DSPy

Nuevo extractor `DSPyEventExtractor` en `src/lagransala/extractor/infrastructure/`. Implementa el Protocol `EventExtractor` existente — cero cambios en el pipeline principal.

```python
class EventExtractionSignature(dspy.Signature):
    """Extract all events from venue webpage content in markdown format.
    Return only events from the current month onwards."""
    content: str = dspy.InputField(desc="Venue webpage content in markdown")
    first_day: str = dspy.InputField(desc="First day of current month, YYYY-MM-DD")
    extraction: EventExtraction = dspy.OutputField()

class DSPyEventExtractorModule(dspy.Module):
    def __init__(self):
        self.extract = dspy.TypedPredictor(EventExtractionSignature)

    def forward(self, content: str, first_day: str) -> dspy.Prediction:
        return self.extract(content=content, first_day=first_day)
```

### Carga del programa compilado

```python
class DSPyEventExtractor:
    def __init__(self, program_path: str, model: str):
        dspy.settings.configure(lm=dspy.LM(model))
        self.module = DSPyEventExtractorModule()
        self.module.load(program_path)

    @classmethod
    def from_compiled(cls, program_path: str, model: str) -> "DSPyEventExtractor":
        return cls(program_path=program_path, model=model)

    async def extract(
        self, content: SourcedContent, context: dict[str, str] | None = None
    ) -> SourcedEventExtraction:
        first_day = date.today().replace(day=1).isoformat()
        result = self.module(content=content.content, first_day=first_day)
        return SourcedEventExtraction(
            **result.extraction.model_dump(),
            model=dspy.settings.lm.model,
            source_url=content.url,
            dt=datetime.now(),
        )
```

Configuración en `.env`:

```bash
EVENT_EXTRACTOR_PROGRAM=evals/programs/champion.json
EVENT_EXTRACTOR_MODEL=ollama/qwen2.5:7b
```

Carga en `__main__.py`:

```python
program_path = os.getenv("EVENT_EXTRACTOR_PROGRAM")
model = os.getenv("EVENT_EXTRACTOR_MODEL", "groq/gpt-oss-120b")

if program_path:
    event_extractor = DSPyEventExtractor.from_compiled(program_path, model)
else:
    event_extractor = initialize_groq_extractor()  # fallback actual
```

### Optimización

```
evals/
├── optimize.py             # script de optimización
└── programs/
    ├── qwen2.5-7b-2026-04.json   # programas compilados por modelo/fecha
    └── champion.json             # symlink al programa en producción
```

Flujo de `optimize.py`:

```
annotated/*.json
    → split 80/20 train/val
    → dspy.BootstrapFewShot(metric=combined_score, max_bootstrapped_demos=4)
    → compilar sobre trainset  (~150-250 forward passes, 3-8h en CPU local)
    → evaluar sobre valset
    → MLflow run con params + métricas + artifact (programa .json)
    → guardar programa en evals/programs/<model>-<date>.json
```

Promover a producción (manual):

```bash
ln -sf qwen2.5-7b-2026-04.json evals/programs/champion.json
# o actualizar .env con la ruta directa
```

### Comparativa MLflow Fase 2

| Run | modelo | extractor_type | DSPy |
|-----|--------|----------------|------|
| baseline-local | ollama/qwen2.5:7b | litellm | no |
| dspy-optimized | ollama/qwen2.5:7b | dspy | BootstrapFewShot |

---

## Dependencias nuevas

### Dev / evals únicamente (`pyproject.toml` grupo `[dev]` o grupo `[evals]`)

- `mlflow`
- `dspy`
- `rapidfuzz`

### Runtime (si se usa DSPy extractor)

- `dspy` — solo si `EVENT_EXTRACTOR_PROGRAM` está configurado

---

## Secuencia de implementación

### Fase 1
1. Añadir dependencias mlflow, rapidfuzz al grupo dev
2. Implementar `evals/data/schema.py`
3. Implementar `evals/metrics/event_matching.py` y `field_accuracy.py`
4. Implementar `evals/annotate.py`
5. Implementar `evals/run_eval.py`
6. Anotar 30-80 ejemplos manualmente
7. Ejecutar evals baseline (groq cloud vs ollama local)

### Fase 2
1. Añadir dependencia dspy
2. Implementar `DSPyEventExtractorModule` y `DSPyEventExtractor`
3. Añadir carga dinámica en `__main__.py`
4. Implementar `evals/optimize.py`
5. Ejecutar optimización overnight
6. Comparar en MLflow: baseline-local vs dspy-optimized
7. Promover champion si hay mejora
