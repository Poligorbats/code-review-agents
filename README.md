# Многоагентная система анализа и рефакторинга кода

Многоагентная система для автоматического анализа и рефакторинга Python-кода на базе LangChain и Ollama (локальные LLM без API-ключей).

## Архитектура

```
Входной код
    │
    ▼
┌─────────────┐
│ Оркестратор │  управляет пайплайном агентов
└──────┬──────┘
       │
  ┌────┴──────────────────────────────────┐
  ▼          ▼            ▼              ▼
Анализатор  Критик    Рефактор       Тестировщик
  │           │           │               │
  │    CoT    │           │   запускает   │
  │ рассужд.  │           │    тесты      │
  └─────┬─────┘           └───────┬───────┘
        │   Внешние инструменты:  │
        ├── StaticAnalysisTool    │
        ├── DocSearchTool (RAG)   │
        └── CodeExecutorTool ─────┘
```

### Агенты

| Агент | Модель | Роль |
|---|---|---|
| **Analyzer** (Анализатор) | codellama:13b | Находит баги, code smells, нарушения стиля через AST + pylint + LLM |
| **Critic** (Критик) | llama3:8b | Расставляет приоритеты проблем с помощью Chain-of-Thought рассуждений |
| **Refactorer** (Рефактор) | codellama:13b | Генерирует улучшенный, чистый код |
| **Tester** (Тестировщик) | codellama:13b | Генерирует pytest-тесты и запускает их |

### Инструменты

| Инструмент | Описание |
|---|---|
| `StaticAnalysisTool` | Парсинг AST + pylint + метрики сложности через radon |
| `CodeExecutorTool` | Безопасное выполнение кода в sandbox с ограничением импортов |
| `DocSearchTool` | RAG по базе знаний Python best practices (ChromaDB + Ollama embeddings) |

## Установка

### 1. Установить Ollama

Скачать с https://ollama.ai и загрузить необходимые модели:

```bash
ollama pull codellama:13b
ollama pull llama3:8b
ollama pull nomic-embed-text   # для RAG-эмбеддингов
```

### 2. Установить зависимости Python

```bash
pip install -r requirements.txt
```

### 3. Настроить окружение

```bash
cp .env.example .env
# При необходимости отредактировать .env (по умолчанию работает с Ollama на localhost)
```

## Использование

### Анализ файла

```bash
python main.py --file examples/bad_code_1.py
```

### Сохранить отчёт в файл

```bash
python main.py --file examples/bad_code_1.py --output report.txt
```

### Пропустить генерацию тестов (быстрее)

```bash
python main.py --file examples/bad_code_1.py --skip-tests
```

### Вывод в формате JSON (для интеграции)

```bash
python main.py --file examples/bad_code_2.py --json
```

### Чтение кода из stdin

```bash
cat mycode.py | python main.py --stdin
```

## Пример вывода

```
============================================================
CODE REVIEW & REFACTORING REPORT
============================================================

## ANALYSIS
1. CRITICAL ISSUES
   - Строка 4: Изменяемый аргумент по умолчанию `numbers=[]` — общее состояние между вызовами
   - Строка 17: Нет защиты от пустого списка — ZeroDivisionError

2. WARNINGS
   - Строки 6-8: Используется range(len()) вместо enumerate() или прямой итерации
   ...

## CRITIQUE & PRIORITIES
### MUST FIX
- Mutable default argument: приводит к трудноуловимым багам → CRITICAL
...

## REFACTORED CODE
```python
def calculate_stats(numbers: list[float] | None = None) -> dict:
    ...
```

## TEST RESULTS
Тестов пройдено: 5 | Тестов провалено: 0
```

## Структура проекта

```
code-review-agents/
├── agents/
│   ├── analyzer.py       # Поиск проблем: статический анализ + LLM
│   ├── critic.py         # Приоритизация через Chain-of-Thought
│   ├── refactorer.py     # Генерация улучшенного кода
│   ├── tester.py         # Генерация и запуск тестов
│   └── orchestrator.py   # Координация пайплайна, формирование отчёта
├── tools/
│   ├── static_analysis.py  # AST + pylint + radon
│   ├── code_executor.py    # Sandbox для выполнения кода
│   └── doc_search.py       # RAG по документации
├── examples/
│   ├── bad_code_1.py     # Mutable defaults, bare except, стиль
│   ├── bad_code_2.py     # Высокая сложность, глобальное состояние
│   └── bad_code_3.py     # Баги в алгоритмах, производительность
├── tests/
│   └── test_agents.py    # pytest-тесты для инструментов
├── main.py               # CLI точка входа
├── requirements.txt
└── .env.example
```

## Применяемые техники

- **Многоагентная координация** через LangChain + кастомный оркестратор
- **Chain-of-Thought рассуждения** в агенте-критике для приоритизации проблем
- **RAG (Retrieval-Augmented Generation)** для поиска по базе best practices
- **Использование внешних инструментов** — агенты вызывают AST-анализ и выполнение кода
- **Локальный инвертор LLM** через Ollama (API-ключи не нужны)
- **Безопасное выполнение кода** с ограничением импортов и таймаутом

## Запуск тестов

```bash
pytest tests/
```
