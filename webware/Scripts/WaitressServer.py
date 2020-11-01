#!/usr/bin/env python3

"""Serve Webware for Python Application using the waitress WSGI server."""

import argparse


def serve(args):
    try:
        from waitress import serve
    except ImportError as e:
        raise RuntimeError('Waitress server is not installed') from e

    if args.browser:
        scheme = args.url_scheme
        host, port = args.host, args.port
        prefix = args.url_prefix.strip('/')
        if prefix:
            prefix += '/'
        url = f'{scheme}://{host}:{port}/{prefix}'

        import time
        import threading
        import webbrowser

        def openBrowser():
            time.sleep(1)
            webbrowser.open(url)

        t = threading.Thread(target=openBrowser)
        t.setDaemon(True)
        t.start()

    if args.reload:
        try:
            import hupper
        except ImportError as e:
            raise RuntimeError(
                'The hupper process monitor is not installed') from e
        if not hupper.is_active():
            print('Running Webware with reloading option...')
            args.browser = args.reload = False
            hupper.start_reloader(
                'webware.Scripts.WaitressServer.serve',
                reload_interval=int(args.reload_interval),
                worker_args=[args])

    development = not args.prod
    from os import environ
    if development:
        environ['WEBWARE_DEVELOPMENT'] = 'true'
    elif 'WEBWARE_DEVELOPMENT' in environ:
        del environ['WEBWARE_DEVELOPMENT']
    try:
        # get application from WSGI script
        with open(args.wsgi_script) as f:
            script = f.read()
        # set development flag in the script
        script = script.replace(
            'development =', f'development = {development} #')
        # do not change working directory in the script
        script = script.replace('workDir =', "workDir = '' #")
        scriptVars = {}
        exec(script, scriptVars)
        application = scriptVars['application']
    except Exception as e:
        raise RuntimeError(
            'Cannot find Webware application.\nIs the current directory'
            ' the application working directory?') from e

    print("Waitress serving Webware application...")
    args = vars(args)
    for arg in 'browser reload reload_interval prod wsgi_script'.split():
        del args[arg]
    if args['trusted_proxy_headers']:
        args['trusted_proxy_headers'] = args[
            'trusted_proxy_headers'].split(',')
    if not args['trusted_proxy']:
        if args['trusted_proxy_count'] == 1:
            del args['trusted_proxy_count']
        if not args['trusted_proxy_headers']:
            del args['trusted_proxy_headers']
    serve(application, **args)


def addArguments(parser):
    """Add command line arguments to the given parser."""
    parser.add_argument(
        '-l', '--host',
        help="Hostname or IP address on which to listen",
        default='127.0.0.1',
    )
    parser.add_argument(
        '-p', '--port',
        help="TCP port on which to listen",
        default='8080',
    )
    parser.add_argument(
        '--url-scheme',
        help="Specifies the scheme portion of the URL",
        default='http',
    )
    parser.add_argument(
        '--url-prefix',
        help="Mount the application using this URL prefix",
        default='',
    )
    parser.add_argument(
        '-r', '--reload',
        action='store_true',
        help="Use auto-restart file monitor",
        default=False,
    )
    parser.add_argument(
        '--reload-interval',
        type=int,
        help="Seconds between checking files",
        default=1,
    )
    parser.add_argument(
        '-b', '--browser',
        action='store_true',
        help="Open a web browser to the running app",
    )
    parser.add_argument(
        '--threads',
        type=int,
        help="Number of threads used to process application logic",
        default=4,
    )
    parser.add_argument(
        '--trusted-proxy',
        help="IP address of a trusted peer passing proxy headers",
        default=None,
    )
    parser.add_argument(
        '--trusted-proxy-count',
        type=int,
        help="How many proxies we trust when chained",
        default=1,
    )
    parser.add_argument(
        '--trusted-proxy-headers',
        help="Comma-separated proxy headers we shall trust",
        default=None,
    )
    parser.add_argument(
        '--prod',
        action='store_true',
        help="Do not set development mode",
        default=False,
    )
    parser.add_argument(
        '--wsgi-script',
        help='The file path of the WSGI script',
        default='Scripts/WSGIScript.py',
    )


def main(args=None):
    """Evaluate the command line arguments and call serve()."""
    parser = argparse.ArgumentParser(
        description="Serve a Webware application using waitress")
    addArguments(parser)
    args = parser.parse_args(args)
    serve(args)


if __name__ == '__main__':
    main()
