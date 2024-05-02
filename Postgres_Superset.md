# Инструкция по установке Postgres и Superset

## Установка Docker на виртуальной машине

1. Устанавливаем Docker в соответствии со Step 1 из [инструкции](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-22-04).
2. Если работаете **не** из под пользователя `root`, то выполняем Step 2 из инструкции выше. 

## Настройка Docker-контейнеров

1. Создаем сеть для двух контейнеров: 
    ```
    docker network create app_net
    ```

2. Создаем хранилище (volume) для контейнера с БД: 
    ```
    docker volume create postgres_1_vol
    ```

3. Запускаем контейнер с PostgresDB:
    ```
    docker run -d \
        --name postgres_1 \
        -e POSTGRES_USER=postgres \
        -e POSTGRES_PASSWORD='123' \
        -e POSTGRES_DB=test_app \
        -v postgres_1_vol:/var/lib/postgresql \
        postgres:15
    ```
    `POSTGRES_USER`, `POSTGRES_PASSWORD` нужно запомнить – они понадобятся для подключения. 

4. Запускаем контейнер Superset:
    ```
    docker run --rm -d \
        -p 8080:8088 \
        -e "SUPERSET_SECRET_KEY=$(openssl rand -base64 42)" \
        --name superset \
        apache/superset
    ```

5. Последовательно запускаем команды для настройки Superset: создание пользователя, обновление внутренней базы, инициализация сервиса: 

    ```
    docker exec -it superset superset fab create-admin \
                --username admin \
                --firstname Superset \
                --lastname Admin \
                --email admin@superset.com \
                --password admin
    ```
    `username`, `password` понадобятся для авторизации в Superset. 

    Обновляем внутреннюю БД Superset:
    ```
    docker exec -it superset superset db upgrade
    ```

    Запускаем сервер Superset:
    ```
    docker exec -it superset superset init
    ```

6. Подключаем контейнеры в созданную сеть: 

    ```
    docker network connect <имя вашей сети> <имя контейнера postgres>
    ```

    ```
    docker network connect <имя вашей сети> <имя контейнера superset>
    ```

## Создание и добавление БД в контейнер с Postgres

1. `docker exec -it postgres_1 bash` 
- Заходим в контейнер и открываем bash

2. `apt-get install -y wget`

3. `cd /var/lib/postgresql` 

- Заходим в папку, куда перенесли файл

4. `wget https://9c579ca6-fee2-41d7-9396-601da1103a3b.selstorage.ru/credit_clients.csv`

- Скачиваем файл с данными для БД

5. `ls` 

- Проверяем скачался ли файл

6. `exit`
- Выходим в root@...

7. `psql -U postgres`

8. `CREATE DATABASE my_database;`
9. `\l`
- Проверяем создалась ли наша БД
10. `su - postgres`
11. `psql -d my_database`
12. `CREATE TABLE credit_clients (
  Date DATE,
  CustomerId BIGINT PRIMARY KEY,
  Surname VARCHAR(255),
  CreditScore INT,
  Geography VARCHAR(50),
  Gender VARCHAR(10),
  Age INT,
  Tenure INT,
  Balance FLOAT8,
  NumOfProducts INT,
  HasCrCard INT,
  IsActiveMember INT,
  EstimatedSalary FLOAT8,
  Exited INT
);`
13. `COPY credit_clients FROM '/var/lib/postgresql/credit_clients.csv' DELIMITER ',' CSV HEADER;`
14. `\d credit_clients`
- проверяем структуру загруженных данных

15. `exit`
16. В локальном терминале прокидываем соединение: 
    ```
    ssh -L  8080:localhost:8080 <user_name>@<ip-address>
    ```

### Подключение из Superset

При подключении к базе данных из Superset необходимы IP, логин и пароль. Логин и пароль берём из п. 3, а IP адрес можно выяснить с помощью команды `docker inspect <имя_сети>` (имя сети из п. 1). В результате будет примерно такой вывод: 

```
[
    {
        "Name": "net",
        "Id": "02b4e751159f77fa32bca34b900e70d350626dea34945ef20821d690afd4ae3b",
        "Created": "2024-04-26T10:51:53.392607628Z",
        "Scope": "local",
        "Driver": "bridge",
        "EnableIPv6": false,
        "IPAM": {
            "Driver": "default",
            "Options": {},
            "Config": [
                {
                    "Subnet": "172.18.0.0/16",
                    "Gateway": "172.18.0.1"
                }
            ]
        },
        "Internal": false,
        "Attachable": false,
        "Ingress": false,
        "ConfigFrom": {
            "Network": ""
        },
        "ConfigOnly": false,
        "Containers": {
            "9744269b182fc725fa64c53d58f2f30c070ccf14e2a222c773ec1f9e0150d6d6": {
                "Name": "superset",
                "EndpointID": "fbebf49e3c0e4887db5aa4d048a5f092c73b940c0cad8572d3801705dfb68eb1",
                "MacAddress": "02:42:ac:12:00:03",
                "IPv4Address": "172.18.0.3/16",
                "IPv6Address": ""
            },
            "af3c5704879a209c421697c8467e69d01cd21f8e232539d1341108853ecb23ce": {
                "Name": "postgres_1",
                "EndpointID": "0f7103b4c9013c25c23aaacaefacd4dee97e653c96be105321f504075a75b93a",
                "MacAddress": "02:42:ac:12:00:02", 
                "IPv4Address": "172.18.0.2/16",<--------------
                "IPv6Address": ""
            }
        },
        "Options": {},
        "Labels": {}
    }
]
```

В конфигурации выше нужно найти контейнер с именем целевого сервиса (в нашем случае Postgres) и скопировать IP-адрес.