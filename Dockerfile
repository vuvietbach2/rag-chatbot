FROM python:3.11

RUN apt-get update && apt-get install -y curl gnupg2 apt-transport-https ca-certificates && \
    curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /usr/share/keyrings/microsoft.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/debian/11/prod bullseye main" > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 mssql-tools

ENV PATH="$PATH:/opt/mssql-tools/bin"

WORKDIR /app

COPY . /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY init_and_run.sh /app/init_and_run.sh
RUN chmod +x /app/init_and_run.sh

EXPOSE 8000

CMD ["/app/init_and_run.sh"]
