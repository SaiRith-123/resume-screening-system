"""Configurable skill taxonomy (spec §7).

Provides alias -> canonical mapping, category families, and family-to-family
relatedness so that related-but-distinct technologies receive *partial* semantic
credit without ever being treated as identical (spec §7).
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Canonical skill -> (category, [aliases...])
# category: programming_language | framework | database | cloud | tool | soft | domain
# ---------------------------------------------------------------------------
SKILL_LIBRARY: dict[str, tuple[str, list[str]]] = {
    # Programming languages
    "Python": ("programming_language", ["python3", "py", "python 3"]),
    "JavaScript": ("programming_language", ["js", "java script", "es6", "ecmascript"]),
    "TypeScript": ("programming_language", ["ts", "type script"]),
    "Java": ("programming_language", ["java8", "java 8", "java11"]),
    "C++": ("programming_language", ["cpp", "c plus plus"]),
    "C#": ("programming_language", ["csharp", "c sharp", ".net c#", "dotnet c#"]),
    "Go": ("programming_language", ["golang", "go lang"]),
    "Rust": ("programming_language", ["rustlang"]),
    "Ruby": ("programming_language", ["ruby on rails lang"]),
    "PHP": ("programming_language", ["php7", "php8"]),
    "R": ("programming_language", ["r language", "rlang"]),
    "Scala": ("programming_language", []),
    "Kotlin": ("programming_language", []),
    "Swift": ("programming_language", []),
    "SQL": ("programming_language", ["ansi sql", "structured query language"]),
    "Bash": ("programming_language", ["shell", "shell scripting", "sh", "bash scripting"]),
    # Frameworks / libraries
    "React": ("framework", ["reactjs", "react.js", "react js"]),
    "Angular": ("framework", ["angularjs", "angular.js", "angular 2"]),
    "Vue": ("framework", ["vuejs", "vue.js"]),
    "Node.js": ("framework", ["node", "nodejs", "node js"]),
    "Django": ("framework", ["django rest framework", "drf"]),
    "Flask": ("framework", []),
    "FastAPI": ("framework", ["fast api"]),
    "Spring": ("framework", ["spring boot", "springboot"]),
    "Express": ("framework", ["expressjs", "express.js"]),
    ".NET": ("framework", ["dotnet", "asp.net", "net core"]),
    "PyTorch": ("framework", ["torch", "pytorch framework"]),
    "TensorFlow": ("framework", ["tf", "tensorflow 2"]),
    "Keras": ("framework", []),
    "scikit-learn": ("framework", ["sklearn", "scikit learn"]),
    "Pandas": ("framework", ["pandas library"]),
    "NumPy": ("framework", ["numpy library"]),
    "Hugging Face Transformers": ("framework", ["transformers", "huggingface", "hf transformers"]),
    "spaCy": ("framework", ["spacy nlp"]),
    "LangChain": ("framework", ["lang chain"]),
    # Databases
    "PostgreSQL": ("database", ["postgres", "psql", "pg"]),
    "MySQL": ("database", ["my sql"]),
    "MongoDB": ("database", ["mongo", "mongo db"]),
    "Redis": ("database", ["redis cache"]),
    "Elasticsearch": ("database", ["elastic search", "elastic"]),
    "SQLite": ("database", ["sql lite"]),
    "Oracle": ("database", ["oracle db", "oracle database"]),
    "SQL Server": ("database", ["mssql", "microsoft sql server", "t-sql"]),
    "Cassandra": ("database", ["apache cassandra"]),
    "Neo4j": ("database", ["neo4j graph"]),
    # Cloud / infra
    "AWS": ("cloud", ["amazon web services", "amazon aws", "aws cloud"]),
    "Azure": ("cloud", ["microsoft azure", "ms azure"]),
    "GCP": ("cloud", ["google cloud", "google cloud platform"]),
    "Docker": ("cloud", ["docker containers", "containerization"]),
    "Kubernetes": ("cloud", ["k8s", "kube"]),
    "Terraform": ("cloud", ["tf infra"]),
    "Jenkins": ("cloud", ["jenkins ci"]),
    "GitHub Actions": ("cloud", ["gh actions", "github ci"]),
    "CI/CD": ("cloud", ["cicd", "continuous integration", "continuous delivery"]),
    "Airflow": ("cloud", ["apache airflow"]),
    "Kafka": ("cloud", ["apache kafka"]),
    "RabbitMQ": ("cloud", ["rabbit mq"]),
    "Celery": ("cloud", ["celery workers"]),
    # Tools
    "Git": ("tool", ["git scm", "version control"]),
    "Linux": ("tool", ["unix", "ubuntu", "bash linux"]),
    "JIRA": ("tool", ["jira software"]),
    "Figma": ("tool", []),
    "Tableau": ("tool", []),
    "Power BI": ("tool", ["powerbi"]),
    "Excel": ("tool", ["ms excel", "spreadsheets"]),
    "Postman": ("tool", []),
    "Swagger": ("tool", ["openapi", "open api"]),
    # Domain / concepts
    "Machine Learning": ("domain", ["ml", "machine-learning"]),
    "Deep Learning": ("domain", ["dl", "neural networks", "deep-learning"]),
    "NLP": ("domain", ["natural language processing", "nlp engineering"]),
    "Computer Vision": ("domain", ["cv", "image processing"]),
    "Data Science": ("domain", ["data analytics", "data analysis"]),
    "REST APIs": ("domain", ["rest api development", "restful api", "rest api", "rest", "api development"]),
    "GraphQL": ("domain", ["graph ql"]),
    "Microservices": ("domain", ["micro services", "microservice architecture"]),
    "MLOps": ("domain", ["ml ops", "ml lifecycle"]),
    "ETL": ("domain", ["etl pipelines", "data pipelines"]),
    "Agile": ("soft", ["scrum", "agile methodology"]),
    "Leadership": ("soft", ["team leadership"]),
    "Communication": ("soft", ["communication skills"]),
    "Problem Solving": ("soft", []),
    "Collaboration": ("soft", ["teamwork"]),
    "Project Management": ("soft", ["pm skills"]),
}

# Build reverse alias index
ALIAS_TO_CANONICAL: dict[str, str] = {}
for _canon, (_cat, _aliases) in SKILL_LIBRARY.items():
    ALIAS_TO_CANONICAL[_canon.lower()] = _canon
    for _a in _aliases:
        ALIAS_TO_CANONICAL[_a.lower()] = _canon

# Family groupings: skills that are *related* but NOT identical (spec §7).
# Value = partial-credit relatedness (0..1) applied only to non-identical skills.
RELATED_GROUPS: list[tuple[set[str], float]] = [
    ({"React", "Angular", "Vue"}, 0.35),                       # front-end frameworks
    ({"PyTorch", "TensorFlow", "Keras"}, 0.5),                 # DL frameworks
    ({"PostgreSQL", "MySQL", "SQLite", "SQL Server", "Oracle"}, 0.4),  # relational DBs
    ({"MongoDB", "Cassandra", "Neo4j"}, 0.35),                 # NoSQL DBs
    ({"AWS", "Azure", "GCP"}, 0.4),                            # cloud providers
    ({"Django", "Flask", "FastAPI", "Express", "Spring"}, 0.4),  # web frameworks
    ({"Machine Learning", "Deep Learning", "NLP", "Computer Vision"}, 0.45),
    ({"Docker", "Kubernetes"}, 0.4),
    ({"Jenkins", "GitHub Actions", "CI/CD"}, 0.5),
    ({"JavaScript", "TypeScript"}, 0.55),
]
# Explicitly UNRELATED pairs that naive similarity would wrongly equate (spec §7).
UNRELATED_PAIRS: set[frozenset] = {
    frozenset({"Python", "Java"}),
    frozenset({"React", "Angular"}),
    frozenset({"PostgreSQL", "MongoDB"}),
    frozenset({"AWS", "Azure"}),
}


def category_of(canonical: str) -> str:
    entry = SKILL_LIBRARY.get(canonical)
    return entry[0] if entry else "other"


def relatedness(a: str, b: str) -> float:
    """Return 0..1 relatedness between two canonical skill names."""
    if a == b:
        return 1.0
    if frozenset({a, b}) in UNRELATED_PAIRS:
        # even if grouped, keep explicit unrelated pairs at low credit
        return 0.1
    for group, score in RELATED_GROUPS:
        if a in group and b in group:
            return score
    # same category but not grouped -> mild shared credit (not identity)
    if category_of(a) == category_of(b) and category_of(a) != "other":
        return 0.15
    return 0.0
