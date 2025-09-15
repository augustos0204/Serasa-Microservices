# Escalabilidade Horizontal - Sistema ETL

Este documento descreve como escalar horizontalmente os microserviços do sistema ETL para atender a maiores volumes de processamento e requisições.

## Visão Geral

O sistema ETL foi projetado para escalabilidade horizontal através de:
- **Docker Compose** para orquestração de containers
- **Nginx Load Balancer** para distribuição de carga
- **RabbitMQ** para balanceamento automático de processamento
- **PostgreSQL compartilhado** para persistência centralizada

## Arquitetura Escalável

```
Internet → Nginx Load Balancer (Port 80)
    ├── Auth Service (múltiplas instâncias)
    ├── File Manager Service (múltiplas instâncias)
    └── Data Processor Service (múltiplas instâncias)
            ↓
    PostgreSQL (único) + RabbitMQ (único)
```

## Configuração do Load Balancer

### 1. Criar Diretório de Configuração
```bash
mkdir -p nginx
```

### 2. Configuração do Nginx (`nginx/nginx.conf`)
```nginx
events {
    worker_connections 1024;
}

http {
    # Load balancing com least connections
    upstream auth_backend {
        least_conn;
        server auth-service:8003 max_fails=3 fail_timeout=30s;
    }

    upstream file_manager_backend {
        least_conn;
        server file-manager-service:8001 max_fails=3 fail_timeout=30s;
    }

    upstream data_processor_backend {
        least_conn;
        server data-processor-service:8002 max_fails=3 fail_timeout=30s;
    }

    server {
        listen 80;
        client_max_body_size 100M;

        # Auth Service Routes
        location /auth/ {
            proxy_pass http://auth_backend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # File Manager Service Routes
        location /files/ {
            proxy_pass http://file_manager_backend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Data Processor Service Routes
        location /process/ {
            proxy_pass http://data_processor_backend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # File Inconsistencies API
        location /file-inconsistencies/ {
            proxy_pass http://data_processor_backend/file-inconsistencies/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health Checks
        location /health/auth {
            proxy_pass http://auth_backend/health;
        }

        location /health/files {
            proxy_pass http://file_manager_backend/health;
        }

        location /health/processor {
            proxy_pass http://data_processor_backend/health;
        }

        # Load Balancer Status
        location /health {
            return 200 'Load Balancer OK';
            add_header Content-Type text/plain;
        }

        # Root - Service Info
        location / {
            return 200 'ETL System - Auth: /auth/, Files: /files/, Process: /process/';
            add_header Content-Type text/plain;
        }

        # Nginx Stats (opcional)
        location /nginx-status {
            stub_status on;
            access_log off;
            allow 127.0.0.1;
            allow 172.16.0.0/12;
            deny all;
        }
    }
}
```

### 3. Atualizar Docker Compose

Modifique o serviço nginx no `docker-compose.yml`:

```yaml
# Nginx Load Balancer
nginx:
  image: nginx:alpine
  container_name: etl_nginx
  ports:
    - "80:80"
  volumes:
    - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
  depends_on:
    - auth-service
    - file-manager-service
    - data-processor-service
  networks:
    - etl_network
  restart: unless-stopped
```

## Comandos de Escalabilidade

### 1. Iniciar Sistema Base
```bash
# Subir infraestrutura base
docker-compose up postgres rabbitmq -d

# Verificar se serviços base estão rodando
docker-compose ps
```

### 2. Escalar Serviços Individualmente
```bash
# Auth Service - 2 instâncias
docker-compose up --scale auth-service=2 -d

# File Manager Service - 3 instâncias
docker-compose up --scale file-manager-service=3 -d

# Data Processor Service - 2 instâncias
docker-compose up --scale data-processor-service=2 -d
```

### 3. Escalar Todos os Serviços de Uma Vez
```bash
# Escalar todos simultaneamente
docker-compose up --scale auth-service=2 --scale file-manager-service=3 --scale data-processor-service=2 -d

# Verificar instâncias escaladas
docker-compose ps
```

### 4. Escalar Durante Execução (Zero Downtime)
```bash
# Sistema já rodando - escalar sem parar
docker-compose up --scale file-manager-service=5 -d

# Reduzir instâncias
docker-compose up --scale file-manager-service=2 -d
```

## Monitoramento de Instâncias

### Verificar Status das Instâncias
```bash
# Ver todas as instâncias rodando
docker-compose ps

# Ver logs de um serviço específico
docker-compose logs -f file-manager-service

# Ver logs de todas as instâncias de um serviço
docker-compose logs --tail=50 data-processor-service
```

### Health Checks via Load Balancer
```bash
# Status do load balancer
curl http://localhost/health

# Health de cada serviço via load balancer
curl http://localhost/health/auth
curl http://localhost/health/files
curl http://localhost/health/processor

# Verificar distribuição de carga
for i in {1..10}; do curl -s http://localhost/auth/health; done
```

## Estratégias de Scaling por Serviço

### Auth Service
**Cenário**: Muitos usuários fazendo login simultaneamente
```bash
# Escalar para 3 instâncias
docker-compose up --scale auth-service=3 -d

# Monitorar performance
docker stats $(docker-compose ps -q auth-service)
```

### File Manager Service
**Cenário**: Upload massivo de arquivos CSV
```bash
# Escalar para 4 instâncias
docker-compose up --scale file-manager-service=4 -d

# Verificar volume compartilhado
docker exec -it $(docker-compose ps -q file-manager-service | head -1) ls -la /app/uploads
```

### Data Processor Service
**Cenário**: Backlog de processamento de arquivos
```bash
# Escalar para 5 instâncias (mais consumers)
docker-compose up --scale data-processor-service=5 -d

# Monitorar fila RabbitMQ
curl -u admin:admin123 http://localhost:15672/api/queues
```

## Load Balancer - Configuração Avançada

### Algoritmo de Balanceamento
O nginx usa `least_conn` (menos conexões ativas):
- **round_robin** (padrão): Distribui em sequência
- **least_conn**: Direciona para servidor com menos conexões ativas
- **ip_hash**: Mantém sessão por IP (sticky sessions)

### Health Check e Failover
```nginx
server auth-service:8003 max_fails=3 fail_timeout=30s;
```
- `max_fails=3`: Marca servidor como inativo após 3 falhas
- `fail_timeout=30s`: Tenta reconectar após 30 segundos

### Rotas do Load Balancer
- `http://localhost/auth/*` → Auth Service
- `http://localhost/files/*` → File Manager Service
- `http://localhost/process/*` → Data Processor Service
- `http://localhost/file-inconsistencies/*` → Data Processor Service

## RabbitMQ e Escalabilidade

### Queue Processing
O RabbitMQ automaticamente distribui mensagens entre múltiplas instâncias do Data Processor:
```bash
# Ver consumidores ativos
docker exec etl_rabbitmq rabbitmqctl list_consumers

# Monitorar fila via management UI
open http://localhost:15672
```

### Filas Utilizadas
- `file_processing` - Processamento principal (FIFO)
- `file_processing_retry` - Retry com delay
- `file_processing_failed` - Dead letter queue

## Cenários de Uso Recomendados

### Desenvolvimento
```bash
# 1 instância de cada
docker-compose up -d
```

### Teste/Staging
```bash
# 2 instâncias de cada
docker-compose up --scale auth-service=2 --scale file-manager-service=2 --scale data-processor-service=2 -d
```

### Produção
```bash
# Escalar baseado na demanda
docker-compose up --scale auth-service=3 --scale file-manager-service=5 --scale data-processor-service=4 -d
```

## Monitoramento e Troubleshooting

### Verificar Configuração do Nginx
```bash
# Testar configuração
docker exec etl_nginx nginx -t

# Recarregar configuração
docker exec etl_nginx nginx -s reload

# Ver logs do nginx
docker-compose logs nginx
```

### Monitoramento de Recursos
```bash
# CPU e memória por container
docker stats

# Connections de banco
docker exec etl_postgres psql -U etl_user -d etl_database -c "SELECT count(*) FROM pg_stat_activity;"
```

### Script de Auto-scaling (Exemplo)
```bash
#!/bin/bash
# auto_scale.sh

QUEUE_SIZE=$(curl -s -u admin:admin123 http://localhost:15672/api/queues/%2F/file_processing | jq '.messages')

if [ "$QUEUE_SIZE" -gt 100 ]; then
    docker-compose up --scale data-processor-service=5 -d
    echo "Escalado para 5 instâncias - Queue: $QUEUE_SIZE"
elif [ "$QUEUE_SIZE" -lt 10 ]; then
    docker-compose up --scale data-processor-service=2 -d
    echo "Reduzido para 2 instâncias - Queue: $QUEUE_SIZE"
fi
```

## Próximos Passos

Para ambientes de produção, considere:
- **Kubernetes** para orquestração avançada
- **PostgreSQL Read Replicas** para distribuir leitura
- **RabbitMQ Cluster** para alta disponibilidade
- **Prometheus + Grafana** para monitoramento
- **Auto-scaling** baseado em métricas