# docsMind

Este proyecto contiene el frontend (Next.js) y backend (Django) para la aplicación. Está configurado para ejecutarse fácilmente en entornos de desarrollo usando Docker Compose.

## Requisitos Previos

- [Docker](https://docs.docker.com/get-docker/) instalado.
- [Docker Compose](https://docs.docker.com/compose/install/) instalado (usualmente incluido con Docker Desktop).

## Instrucciones para ejecutar el proyecto

Sigue estos pasos para levantar tanto el frontend como el backend y la base de datos de forma local:

1. **Abre una terminal** en la carpeta principal del proyecto (donde se encuentra el archivo `docker-compose.yml`).

2. **(Opcional) Configura las variables de entorno**:
   Si es necesario, asegúrate de tener el archivo `.env` dentro de la carpeta `backend/`.

3. **Construye y levanta los contenedores**:
   Ejecuta el siguiente comando para construir las imágenes y levantar todos los servicios:
   ```bash
   docker-compose up --build
   ```

4. **Accede a la aplicación**:
   Una vez que los contenedores estén corriendo, podrás acceder a:
   - **Frontend**: [http://localhost:3000](http://localhost:3000)
   - **Backend**: [http://localhost:8000](http://localhost:8000)

   *Nota: La base de datos PostgreSQL se levanta automáticamente en el puerto 5432 y no requiere configuración manual.*

5. **Para detener el proyecto**:
   Presiona `Ctrl + C` en la terminal donde está corriendo, o ejecuta:
   ```bash
   docker-compose down
   ```