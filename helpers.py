import os


def check_path(abs_path):
    """
        Checking URL to avoid LFI
    """
    return (not os.path.exists(abs_path) or
            not abs_path.startswith(os.path.abspath(os.getcwd())) or
            any([abs_path.startswith(i) for i in deprecated]) or
            os.path.isdir(abs_path))


def alert_if_need(path, host, port, tm):
    if path not in alert_list:
        return
    tkn = os.getenv("SLACK_TOKEN")
    mes = f"Peer `{host}` accessed endpoint `{path}` at {asctime()}."
    url = f"https://slack.com/api/chat.postMessage?token={tkn}&" + \
          f"channel=@aivanov&text={mes}&username=secrets_tracker&" + \
          f"as_user=secrets_tracker&pretty=1"

    ses = requests.Session()
    response = ses.get(url)
    code = response.status_code
    log(get_time_record(), f"{host}:{port} alerted ({code})\n", LINE_SEPARATOR)
