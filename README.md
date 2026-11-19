# SIGA - Sistema Integrado de Gestión Académica

Este es el repositorio principal del Sistema Integrado de Gestión Académica (SIGA) para el Instituto de Educación Superior Tecnológico Público (IESTP).

Toda la documentación arquitectónica, técnica y de negocio oficial se encuentra centralizada en la carpeta `docs/`.

👉 **[Ver Documentación Principal (Índice Maestro)](docs/00-INDICE.md)**

Para conocer el estado actual y los siguientes pasos, revisa el [Informe de Estado](_estado.md).

## Contribuir
Ver [CONTRIBUTING.md](CONTRIBUTING.md). Configuración local: copiar `siga_backend/.env.example` a `.env`.

## Vista clon para la compañera (otro dominio)
Usa `npx vercel` (no requiere instalación global) y la sesión activa de Vercel. Desde la raíz:

```powershell
.\scripts\create-companera-view.ps1
```

Crea el proyecto `siga-suiza-2026` (sin `-f-d`), copia las variables `VITE_*` del proyecto actual, conecta el repo de GitHub (rama `main`) y despliega el clon usando la misma DB/backend de Railway. URL publicada: `https://siga-suiza-2026-gamma.vercel.app` (el alias `siga-suiza-2026.vercel.app` ya está ocupado globalmente). Para dominio propio: `-CustomDomain 'siga.tudominio.com'`.
