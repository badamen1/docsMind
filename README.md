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
