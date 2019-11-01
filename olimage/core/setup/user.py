import logging

from olimage.core.utils import Utils

logger = logging.getLogger(__name__)


class User(object):
    @staticmethod
    def __call__(username, password, path, groups=None):
        # Root user is always present. Only change password for it.
        if username == 'root':
            Utils.shell.chroot(
                "/bin/bash -c '(echo {}; echo {};) | passwd root'".format(password, password),
                path, logger,
                ignore_fail=True
            )
        else:
            Utils.shell.chroot(
                "/bin/bash -c '(echo {}; echo {};) | adduser --gecos {} {}'".format(
                    password, password, username, username
                ),
                path, logger,
                ignore_fail=True
            )

        if groups:
            if not isinstance(groups, list):
                groups = [groups]
            for group in groups:
                Utils.shell.chroot(
                    "/bin/bash -c 'usermod -a -G {} {}'".format(group, username),
                    path, logger,
                    ignore_fail=True
                )
