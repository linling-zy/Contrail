import logging
from logging.config import fileConfig

from flask import current_app

from alembic import context

# 这是 Alembic 配置对象，提供对正在使用的 .ini 文件中值的访问
config = context.config

# 为 Python 日志记录解释配置文件
# 这行代码基本上设置了日志记录器
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')


def get_engine():
    try:
        # 这适用于 Flask-SQLAlchemy<3 和 Alchemical
        return current_app.extensions['migrate'].db.get_engine()
    except (TypeError, AttributeError):
        # 这适用于 Flask-SQLAlchemy>=3
        return current_app.extensions['migrate'].db.engine


def get_engine_url():
    try:
        return get_engine().url.render_as_string(hide_password=False).replace(
            '%', '%%')
    except AttributeError:
        return str(get_engine().url).replace('%', '%%')


# 在此处添加模型的 MetaData 对象
# 用于 'autogenerate' 支持
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
config.set_main_option('sqlalchemy.url', get_engine_url())
target_db = current_app.extensions['migrate'].db

# 可以根据 env.py 的需要从配置中获取其他值：
# my_important_option = config.get_main_option("my_important_option")
# ... 等等


def get_metadata():
    if hasattr(target_db, 'metadatas'):
        return target_db.metadatas[None]
    return target_db.metadata


def run_migrations_offline():
    """在 'offline' 模式下运行迁移。

    这仅使用 URL 配置上下文，而不使用 Engine，
    尽管 Engine 在这里也是可以接受的。通过跳过 Engine 创建，
    我们甚至不需要 DBAPI 可用。

    这里对 context.execute() 的调用会将给定的字符串发送到脚本输出。

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=get_metadata(), literal_binds=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """在 'online' 模式下运行迁移。

    在这种情况下，我们需要创建一个 Engine
    并将连接与上下文关联。

    """

    # 此回调用于在模式没有更改时防止生成自动迁移
    # 参考：http://alembic.zzzcomputing.com/en/latest/cookbook.html
    def process_revision_directives(context, revision, directives):
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info('No changes in schema detected.')

    conf_args = current_app.extensions['migrate'].configure_args
    if conf_args.get("process_revision_directives") is None:
        conf_args["process_revision_directives"] = process_revision_directives

    connectable = get_engine()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=get_metadata(),
            **conf_args
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
