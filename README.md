# 🌱 SmartGardenSchool – Guía de Ejecución del Proyecto

Este proyecto corresponde al sistema **SmartGardenSchool**, desarrollado con **FastAPI** y arquitectura hexagonal para monitoreo inteligente de un huerto escolar.

---

# 📦 Requisitos previos

Antes de ejecutar el proyecto asegúrate de tener instalado:

- Python 3.10 o superior
- Visual Studio Code (recomendado)
- Entorno virtual `venv`

---

# 📂 Estructura del proyecto

El proyecto utiliza arquitectura hexagonal:

application/
domain/
infrastructure/
tests/
config.py
requirements.txt

---

# 🚀 Pasos para ejecutar el proyecto

## 1️⃣ Abrir la carpeta del proyecto

Abrir en VS Code:

SmartGardenSchool/

---

## 2️⃣ Activar entorno virtual

En PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Si no existe el entorno virtual:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

---

## 3️⃣ Instalar dependencias

```powershell
pip install -r requirements.txt
pip install aiosqlite
```

---

## 4️⃣ Configuración de base de datos (modo local SQLite)

Editar archivo:

config.py

Debe contener:

```python
DATABASE_URL: str = "sqlite+aiosqlite:///./smartgarden.db"
```

Esto permite ejecutar el sistema sin PostgreSQL ni Docker.

---

## 5️⃣ Ejecutar el servidor FastAPI

Desde la raíz del proyecto:

```powershell
python -m uvicorn infrastructure.adapters.input.api:app --reload --app-dir application
```

Si todo está correcto aparecerá:

```
Application startup complete
Uvicorn running on http://127.0.0.1:8000
```

---

# 🌐 Acceso al sistema

Abrir en navegador:

Swagger UI (documentación interactiva):

http://127.0.0.1:8000/docs

Health check del sistema:

http://127.0.0.1:8000/health

---

# 🧪 Ejecutar pruebas unitarias

Desde la raíz del proyecto:

```powershell
pytest
```

---

# 📊 Endpoints disponibles

Principales endpoints:

POST /lecturas
GET /huerto/estado
GET /lecturas/historial
GET /alertas
POST /experimentos
GET /experimentos

---

# 🏗️ Arquitectura utilizada

El proyecto implementa:

- Arquitectura Hexagonal
- FastAPI
- SQLAlchemy async
- SQLite (modo local)
- Motor de reglas IA para recomendaciones

---

# 👨‍💻 Autor

Proyecto académico – SmartGardenSchool
Ingeniería de Software
