import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SSL_DISBALE = False
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    SOCONN_MAIL_SUBJECT = '[SoConn]'
    SOCONN_MAIL_SENDER = 'SoConn Admin <soconn@example.com>'
    SOCONN_ADMIN = os.environ.get('SOCONN_ADMIN')
    POSTS_PER_PAGE = 50
    FOLLOWERS_PER_PAGE = 100
    COMMENTS_PER_PAGE = 50
    SLOW_DB_QUERY_TIME = 0.5

    @staticmethod
    def init_app(app):
        pass


class DevEnvConf(Config):
    DEBUG=True
    SQLALCHEMY_DATABSE_URI = os.environ.get('DEV_DB_URL') or 'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')


class TestEnvConfig(Config):
    TESTING=True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DB_URL') or 'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')
    WTF_CSRF_ENABLED = False


class ProdEnvConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DB_URL') or 'sqlite:///' + os.path.join(basedir, 'data.sqlite')

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # email errors to admins
        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None
        if getattr(cls, 'MAIL_USERNAME', None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_TLS', None):
                secure = ()
        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.SOCONN_MAIL_SENDER,
            toaddrs=[cls.SOCONN_ADMIN],
            subject=cls.SOCONN_MAIL_SUBJECT + 'App Error',
            credentials = credentials,
            secure=secure
        )
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)


class HerokuConfig(ProdEnvConfig):
    SSL_DISABLE = bool(os.environ.get('SSL_DISABLE'))

    @classmethod
    def init_app(cls, app):
        ProdEnvConfig.init_app(app)

        # handler for proxy server headers
        from werkzeug.contrib.fixers import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)

        # log to std err
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.WARNING)
        app.logger.addHandler(file_handler)


class UnixConf(ProdEnvConfig):
    @classmethod
    def init_app(cls, app):
        ProdEnvConfig.init_app(app)

        # log to syslog
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)

config = {
    'dev': DevEnvConf,
    'test': TestEnvConfig,
    'prod': ProdEnvConfig,
    'heroku': HerokuConfig,
    'unix': UnixConf,
    'default': DevEnvConf
}