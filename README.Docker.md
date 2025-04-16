## Configuration Docker pour ProEvent

Ce projet utilise Docker pour faciliter le déploiement et la configuration des services nécessaires.

### Services configurés

- **PostgreSQL**: Base de données principale (port 5460)
- **RabbitMQ**: Broker de messages pour Celery (port 5673 pour AMQP, port 15673 pour l'interface d'administration)
- **Redis**: Backend de résultats pour Celery (port 6380)

### Instructions de démarrage

1. Assurez-vous que Docker et Docker Compose sont installés sur votre système

2. Pour démarrer tous les services:

   ```bash
   cd tests
   docker-compose up -d
   ```

3. Pour arrêter les services:
   ```bash
   cd tests
   docker-compose down
   ```

### Accès aux services

- **PostgreSQL**:

  - Host: localhost
  - Port: 5460
  - User: proevent
  - Password: proevent
  - Database: db_proevent

- **RabbitMQ Management**:

  - URL: http://localhost:15673
  - User: proevent
  - Password: proevent

- **Redis**:
  - Host: localhost
  - Port: 6380

### Notes importantes

- Les noms des conteneurs ont été renommés pour éviter les conflits avec d'autres projets:

  - `rabbitmq_proevent` au lieu de `rabbitmq`
  - `redis_proevent` au lieu de `redis`

- Les ports ont également été modifiés:

  - RabbitMQ: 5673 au lieu de 5672, et 15673 au lieu de 15672
  - Redis: 6380 au lieu de 6379

- Si vous utilisez ces services dans votre application, assurez-vous de mettre à jour les paramètres de connexion en conséquence.

### Building and running your application

When you're ready, start your application by running:
`docker compose up --build`.

Your application will be available at http://localhost:8000.

### Deploying your application to the cloud

First, build your image, e.g.: `docker build -t myapp .`.
If your cloud uses a different CPU architecture than your development
machine (e.g., you are on a Mac M1 and your cloud provider is amd64),
you'll want to build the image for that platform, e.g.:
`docker build --platform=linux/amd64 -t myapp .`.

Then, push it to your registry, e.g. `docker push myregistry.com/myapp`.

Consult Docker's [getting started](https://docs.docker.com/go/get-started-sharing/)
docs for more detail on building and pushing.

### References

- [Docker's Python guide](https://docs.docker.com/language/python/)
