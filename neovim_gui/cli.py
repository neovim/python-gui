"""CLI for accessing the gtk/tickit UIs implemented by this package."""
import os
import resource
import sys
import shlex

import click
import yaml

from .ui_bridge import UIBridge
from neovim import attach
from neovim.compat import IS_PYTHON3


CONFIG_FILES = (
    '.pynvim.yaml',
    '~/.pynvim.yaml',
    '~/.config/pynvim/config.yaml'
)


def load_config(config_file):
    """Load config values from yaml."""

    if config_file:
        with open(config_file) as f:
            return yaml.load(f)

    else:
        for config_file in CONFIG_FILES:
            try:
                with open(os.path.expanduser(config_file)) as f:
                    return yaml.load(f)

            except IOError:
                pass

    return {}


# http://code.activestate.com/recipes/278731-creating-a-daemon-the-python-way/
def detach_proc(workdir='.', umask=0):
    """Detach a process from the controlling terminal and run it in the
    background as a daemon.
    """

    # Default maximum for the number of available file descriptors.
    MAXFD = 1024

    # The standard I/O file descriptors are redirected to /dev/null by default.
    if (hasattr(os, "devnull")):
        REDIRECT_TO = os.devnull
    else:
        REDIRECT_TO = "/dev/null"

    try:
        pid = os.fork()
    except OSError, e:
        raise Exception, "%s [%d]" % (e.strerror, e.errno)

    if (pid == 0):
        os.setsid()

        try:
            pid = os.fork()

        except OSError, e:
            raise Exception, "%s [%d]" % (e.strerror, e.errno)

        if (pid == 0):
            os.chdir(workdir)
            os.umask(umask)
        else:
            os._exit(0)
    else:
        os._exit(0)

        maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
        if (maxfd == resource.RLIM_INFINITY):
            maxfd = MAXFD

            # Iterate through and close all file descriptors.
            for fd in range(0, maxfd):
                try:
                    os.close(fd)
                except OSError:
                    pass

    os.open(REDIRECT_TO, os.O_RDWR)

    os.dup2(0, 1)
    os.dup2(0, 2)

    return(0)


@click.command(context_settings=dict(allow_extra_args=True))
@click.option('--prog')
@click.option('--notify', '-n', default=False, is_flag=True)
@click.option('--listen', '-l')
@click.option('--connect', '-c')
@click.option('--profile',
              default='disable',
              type=click.Choice(['ncalls', 'tottime', 'percall', 'cumtime',
                                 'name', 'disable']))
@click.option('config_file', '--config', type=click.Path(exists=True))
@click.option('--detach/--no-detach', default=True, is_flag=True)
@click.pass_context
def main(ctx, prog, notify, listen, connect, profile, config_file, detach):
    """Entry point."""

    if detach:
        exit_code = detach_proc()

    address = connect or listen

    if address:
        import re
        p = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?:\:\d{1,5})?$')

        if p.match(address):
            args = ('tcp',)
            kwargs = {'address': address}
        else:
            args = ('socket',)
            kwargs = {'path': address}

    if connect:
        # connect to existing instance listening on address
        nvim = attach(*args, **kwargs)
    elif listen:
        # spawn detached instance listening on address and connect to it
        import os
        import time
        from subprocess import Popen
        os.environ['NVIM_LISTEN_ADDRESS'] = address
        nvim_argv = shlex.split(prog or 'nvim --headless') + ctx.args
        # spawn the nvim with stdio redirected to /dev/null.
        dnull = open(os.devnull)
        p = Popen(nvim_argv, stdin=dnull, stdout=dnull, stderr=dnull)
        dnull.close()
        while p.poll() or p.returncode is None:
            try:
                nvim = attach(*args, **kwargs)
                break
            except IOError:
                # socket not ready yet
                time.sleep(0.050)
    else:
        # spawn embedded instance
        nvim_argv = shlex.split(prog or 'nvim --embed') + ctx.args
        nvim = attach('child', argv=nvim_argv)

    from .gtk_ui import GtkUI
    config = load_config(config_file)
    ui = GtkUI(config)
    bridge = UIBridge()
    bridge.connect(nvim, ui, profile if profile != 'disable' else None, notify)

    if detach:
        sys.exit(exit_code)


if __name__ == '__main__':
    main()
