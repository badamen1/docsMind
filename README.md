# docsMind

Este proyecto contiene el frontend (Next.js) y backend (Django REST Framework) para la aplicación. Está configurado para ejecutarse usando Docker Compose. La arquitectura está dividida en un Cliente (SPA) y un Servidor (API REST conectada a PostgreSQL).

## Rutas Principales
- **Ruta Principal (Frontend / Usuario Final):** [http://localhost:3000](http://localhost:3000)
- **Ruta Administrador (Base de Datos):** [http://localhost:8000/admin](http://localhost:8000/admin)

---

## 🚀 Instrucciones de Ejecución

Siguiendo las instrucciones del Entregable 1, el proyecto corre íntegramente de manera automatizada en un entorno Dockerizado.

1. **Abre una terminal** en la raíz del repositorio (donde está este `README.md`).
2. **Levanta y Construye el Proyecto** ejecutando el siguiente comando:
   ```bash
   docker compose up -d --build
   ```
3. El proyecto descargará PostgreSQL, configurará el motor de Python y la plataforma de Node.js. Cuando finalice, abre tu navegador.

### Probando el Login o el Servidor Administrador
La plataforma cuenta con un sistema robusto de Gestión y Autenticación de Usuarios.
Para acceder como administrador y ver los registros de la base de datos (Backend):
- Ingresa a: `http://localhost:8000/admin`
- Inicia sesión con la cuenta (o créala si la BD está limpia mediante shell).

Para acceder a la plataforma como Cliente/Estudiante:
- Ingresa a la interfaz principal `http://localhost:3000` y regístrate en el apartado "Iniciar Sesión -> Registrarse".

### Detener el proyecto
Para bajar el servidor correctamente desde tu terminal:
```bash
docker compose down
```
## Arquitectura 
<img width="1621" height="971" alt="Arquitectura drawio" src="https://github.com/user-attachments/assets/7d4af970-dd69-413d-91f3-5a802c1d16a4" />

## Diagrama de clase
<img width="3751" height="1672" alt="Diagrama de clase Docsmind drawio" src="https://github.com/user-attachments/assets/6aec4b2e-4caa-4c79-8023-023c3fedd602" />

Enlace
https://drive.google.com/file/d/1hRbfSvhPr1GIO130XFI5Ce9BzLwtxlc-/view?usp=sharing


