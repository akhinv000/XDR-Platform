from logcollector.parser import parse_auth_log
from logcollector.updater import update_logs


def collect_logs():

    logs = parse_auth_log("logcollector/auth.log")

    update_logs(logs)

    return len(logs)