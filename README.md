# Desafio Técnico – ETL com APIs Seguras, Assíncronas, Escaláveis e Processamento em Fila #
 
## Objetivo ##

Desenvolver duas APIs que operam em conjunto para realizar um fluxo completo de ETL, com autenticação, controle de acesso, processamento assíncrono, escalabilidade e uso de fila para garantir a ordem de execução. O sistema também deve registrar e expor inconsistências encontradas durante o processamento dos arquivos, com suporte a rastreabilidade via logs.

## API 1 – Fornecimento de Arquivo com Autenticação ##

**Endpoint: GET /download/{file_id}**

Funcionalidades:
- Autentica o usuário (via JWT, OAuth2 ou token de acesso).
- Verifica se o usuário possui permissão para acessar o arquivo solicitado.
- Disponibiliza o arquivo para download.
- Após o download, envia uma mensagem para uma fila (ex: RabbitMQ, Redis Streams, Kafka) contendo os metadados do arquivo (nome, caminho, timestamp).
- A chamada deve ser assíncrona, garantindo uma resposta rápida ao cliente.
- A API deve ser projetada para escalabilidade horizontal, permitindo que múltiplas instâncias sejam executadas simultaneamente de forma segura e eficiente, sem comprometer a integridade dos dados ou a ordem de processamento.
- Todas as ações relevantes devem ser registradas em logs estruturados, incluindo autenticação, download, envio para fila e erros.

## API 2 – Processamento de Arquivo ##


**Endpoint: POST /process**

Funcionalidades:
- Escuta a fila e processa os arquivos em ordem de chegada (FIFO).
- Lê o conteúdo do arquivo (formato CSV).
- Realiza transformações e validações:
- Normalização de datas e valores numéricos
- Validação de campos obrigatórios
- Remoção de duplicadas
- Insere os dados válidos em um banco de dados relacional (PostgreSQL, MySQL, etc.).
- Registra inconsistências (ex: campos inválidos, linhas corrompidas, dados ausentes) em uma estrutura separada.
- Move o arquivo para uma pasta de arquivos processados ou marca como processado.
- O processamento deve ser implementado de forma assíncrona, utilizando async/await sempre que aplicável (ex: leitura de arquivos, acesso ao banco, envio de mensagens).
Todas as etapas do processamento devem ser registradas em logs estruturados, incluindo início e fim do processamento, erros, número de registros válidos e inválidos, e status final.


**Endpoint: GET /file-inconsistencies?file_id={id}**

Funcionalidades:
- Retorna um JSON com a lista de inconsistências encontradas durante o processamento do arquivo.
- Cada item deve conter:
    - Número da linha
    - Campo afetado
    - Valor inválido
    - Mensagem de erro
 
## Arquivo de Exemplo ##
Será disponibilizado um arquivo CSV com dados fictícios de usuários para facilitar o desenvolvimento e os testes, chamado "usuarios.csv". Fique à vontade para inserir novas informações!
 
## Tecnologias sugeridas ##

- Backend: FastAPI
- Autenticação: OAuth2 com JWT
- Fila: RabbitMQ, Redis Streams ou Kafka
- Banco de dados: PostgreSQL
- Armazenamento de arquivos: Local ou S3
- Containerização: Docker + Docker Compose

## Entregáveis esperados ##
- Código-fonte das duas APIs
- Uso de bibliotecas de terceiros e escolha de um framework cuja escolha deve ser justificada
- Docker Compose com fila, banco e APIs
- Script de criação das tabelas no banco de dados
- Documentação da API (Swagger/OpenAPI)
- Logs e estratégia de retry/falha
- Instruções para escalar horizontalmente as APIs
- Endpoint GET /file-inconsistencies com retorno em JSON
- Uso das melhores práticas para segurança de APIs.

## Pontos que consideramos um bônus: ##
 
- Fazer uso de uma criptografia reversível de dados sensíveis do usuário, como: email, cpf e telefone, antes de persisti-los no banco de dados
- Suas respostas durante o code review
- Sua descrição do que foi feito na sua "pull request"
- Testes funcionais e de integração
- A profundidade da telemetria implementada: qualidade dos logs, cobertura de métricas, e rastreabilidade entre serviços.
- Uso de ferramenta de Observabilidade
