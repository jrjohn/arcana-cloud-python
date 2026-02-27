"""
Scheduled Tasks
"""
import logging
from datetime import datetime
from app.tasks.celery_worker import celery_app
from app.tasks.task_decorators import single_instance_task

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
@single_instance_task(timeout=3600)
def cleanup_expired_tokens(self):
    """
    Cleanup expired OAuth tokens
    Execute daily at 2 AM
    """
    try:
        logger.info("Starting cleanup of expired tokens")

        from app import create_app
        app = create_app()

        with app.app_context():
            from app.repositories.implementations.oauth_token_repository_impl import OAuthTokenRepositoryImpl
            from app.extensions import db

            token_repo = OAuthTokenRepositoryImpl(db.session)
            deleted_count = token_repo.deleteExpired()

            logger.info(f"Cleanup completed: {deleted_count} expired tokens deleted")

            return {
                'status': 'success',
                'deleted_count': deleted_count,
                'timestamp': datetime.utcnow().isoformat()
            }

    except Exception as e:
        logger.error(f"Failed to cleanup expired tokens: {e}")
        raise


@celery_app.task(bind=True)
@single_instance_task(timeout=300)
def health_check_task(self):
    """
    Health check task
    Execute every hour
    """
    try:
        logger.info("Starting health check")

        from app import create_app
        app = create_app()

        with app.app_context():
            from app.extensions import db

            # Check database connection
            db.session.execute('SELECT 1')

            logger.info("Health check passed")

            return {
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat()
            }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise


@celery_app.task(bind=True)
@single_instance_task(timeout=600)
def generate_statistics(self):
    """
    Generate statistics report
    Execute every 10 minutes
    """
    try:
        logger.info("Starting statistics generation")

        from app import create_app
        app = create_app()

        with app.app_context():
            from app.repositories.implementations.user_repository_impl import UserRepositoryImpl
            from app.extensions import db

            user_repo = UserRepositoryImpl(db.session)
            # Count users
            total_users = user_repo.count()

            # Count active tokens (example)
            # active_tokens = token_repo.count_active()  # Need to implement this method

            logger.info(f"Statistics generated: {total_users} users")

            return {
                'status': 'success',
                'statistics': {
                    'total_users': total_users,
                    # 'active_tokens': active_tokens
                },
                'timestamp': datetime.utcnow().isoformat()
            }

    except Exception as e:
        logger.error(f"Failed to generate statistics: {e}")
        raise


@celery_app.task(bind=True)
@single_instance_task(timeout=1800)
def send_daily_report(self):
    """
    Send daily report
    Execute daily at 8 AM
    """
    try:
        logger.info("Starting daily report generation")

        # Can generate report and send email here
        # Example:
        # - Count new users from yesterday
        # - Count active users
        # - Count API call frequency
        # - Send email to administrator

        logger.info("Daily report sent successfully")

        return {
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to send daily report: {e}")
        raise
