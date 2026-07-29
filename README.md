# Frutand Chronos — Sistema de Liquidación y Asistencia Biométrica

Aplicación de escritorio local desarrollada en Python (`CustomTkinter` + `SQLite` + `Pandas`) para la automatización del procesamiento de marcaciones biométricas, liquidación de horas extras, recargos y novedades de asistencia bajo la legislación laboral colombiana para la empresa **Frutand**.

## 🚀 Requisitos Previos

- Python 3.11 o superior.
- Git.

## 📦 Instalación

```bash
# Crear entorno virtual
python -m venv .venv

# Activar entorno virtual (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r project/requirements.txt
```

## 🖥️ Ejecución

```bash
python project/src/main.py
```

## 🧪 Pruebas Unitarias

```bash
pytest project/tests
```

## 🏗️ Metodología de Desarrollo

Este proyecto sigue la metodología **ASDD (Agentic Spec-Driven Development)** bajo el ecosistema Gemini / Antigravity. Toda especificación y ADR se encuentra documentada en `docs/`.
