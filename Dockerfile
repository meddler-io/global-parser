FROM defectdojo/defectdojo-django:2.37.1


USER root

COPY  ./patch/  /app/


RUN pip install --upgrade pip
RUN pip install pydantic pydantic-django pika pymongo==4.0.1 tldextract nats-py aiohttp --no-cache-dir  

USER root
ENV DD_DATABASE_ENGINE django.db.backends.sqlite3
ENV DJANGO_SETTINGS_MODULE dojo.settings.settings
# ENV DD_DATABASE_NAME /opt/db3
ENV DD_DATABASE_NAME /app/db3

ENV DD_DATABASE_USER root
ENV DD_DATABASE_HOST localhost
ENV DD_SECRET_KEY NOTASECRET


# Cofigurabl env
ENV TOOL_PARSER default-tool
ENV INPUT_DIRECTORY /tmp
ENV INPUT_FILENAME dummy-report.xml
ENV INPUT_DIRECTORY /tmp
ENV OUTPUT_DIRECTORY /tmp
ENV PROCESS_DIRECTORY /tmp
ENV OUTPUT_FILENAME reports.json
ENV OUTPUT_FILEFORMAT jsonl
ENV BUNDLE_PARSER false



# RUN python3 manage.py makemigrations dojo
RUN python3 manage.py migrate
RUN python3 manage.py flush --no-input

ENTRYPOINT [ "python3" ]
CMD [ "lib.py" ]




