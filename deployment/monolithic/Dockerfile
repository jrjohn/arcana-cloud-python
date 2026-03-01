# ============================================================================
# Arcana Cloud - Monolithic Deployment
# ============================================================================
# Single container with all application layers:
# - Controllers (API endpoints)
# - Services (Business logic)
# - Repositories (Data access)
# ============================================================================

FROM arcanacloud/arcana-cloud-base:1.0.0 AS monolithic

# Set deployment layer
ENV DEPLOYMENT_LAYER=monolithic \
    SERVICE_NAME=arcana-cloud-monolithic \
    SERVICE_PORT=5000

# Expose API port
EXPOSE 5000

# Run database migrations on startup (optional - use init container in k8s)
# COPY docker/entrypoint-monolithic.sh /usr/local/bin/entrypoint.sh
# RUN chmod +x /usr/local/bin/entrypoint.sh
# ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# Start Gunicorn server with appropriate worker configuration
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "4", \
     "--threads", "2", \
     "--worker-class", "gthread", \
     "--worker-tmp-dir", "/dev/shm", \
     "--timeout", "60", \
     "--graceful-timeout", "30", \
     "--keep-alive", "5", \
     "--log-level", "info", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--access-logformat", "%({X-Forwarded-For}i)s %(l)s %(u)s %(t)s \"%(r)s\" %(s)s %(b)s \"%(f)s\" \"%(a)s\" %(D)s", \
     "wsgi:app"]
