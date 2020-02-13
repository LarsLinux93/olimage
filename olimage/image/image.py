import logging
import os

import olimage.environment as env

from olimage.core.bootloaders import Bootloader
from olimage.core.io import Console
from olimage.core.parsers import (Board, Boards, Partitions)
from olimage.core.setup import Setup
from olimage.core.utils import Utils

from .mount import Mounter

logger = logging.getLogger(__name__)


class Image(object):
    def __init__(self, boards: Boards, partitions: Partitions):

        # Initialize dependency
        self._board: Board = boards.get_board(env.options['board'])
        self._partitions = partitions

        # Global data
        self._output = env.options['output']

    def generate(self) -> None:
        """
        Generate black image

        :return: None
        """

        size = 0
        for _dir, _, file in os.walk(env.paths['debootstrap']):
            for f in file:
                fp = os.path.join(_dir, f)

                if not os.path.islink(fp):
                    size += os.path.getsize(fp)

        # Get size and add 500MiB size
        size = max((size >> 20) + 500, env.options['size'])

        with Console("Generating black image with size: {}MiB".format(size)):
            Utils.qemu.img(self._output, size)

    def partition(self) -> None:
        """
        Partition the output blank image

        :return: None
        """

        # Create label
        with Console("Creating msdos partition table"):
            Utils.shell.run('parted -s {} mklabel msdos'.format(self._output))

        # Create partitions
        for partition in self._partitions:
            with Console("Creating partition: \'{}\'".format(str(partition))):
                Utils.shell.run(
                    'parted -s {} mkpart primary {} {} {}'.format(
                        self._output, partition.parted.type,
                        partition.parted.start,
                        partition.parted.end
                    )
            )

    def format(self):

        with Mounter.map(self._output, self._partitions) as m:
            for partition in self._partitions:
                with Console("Formating partition: \'{}\'".format(str(partition))):
                    # Get parted related information
                    device = m.device(partition)

                    opts = ''
                    if partition.fstab.type == 'ext4':
                        opts = '-O ^64bit,^metadata_csum'

                    # Make filesystem
                    Utils.shell.run('mkfs.{} {} {}'.format(partition.fstab.type, opts, device))
                    Utils.shell.run('udevadm trigger {}'.format(device))
                    Utils.shell.run('udevadm settle'.format(device))

    def bootloader(self):
        with Console("Writing bootloader"):
            Bootloader.install(self._board, self._output)

    def configure(self):
        with Mounter.mount(self._output, self._partitions) as m:
            with Console("Generating /etc/fstab"):
                # Append UUID
                for partition in self._partitions:
                    partition.fstab.uuid = m.uuid(partition)

                # TODO: This need a fix
                Setup.fstab(self._partitions, m.mountpoint('rootfs'))

    def copy(self, source):
        exclude = ['/dev/*', '/proc/*', '/run/*', '/tmp/*', '/sys/*']

        with Mounter.mount(self._output, self._partitions) as m:
            for partition in self._partitions:
                with Console("Copying partition: \'{}\'".format(str(partition))):
                    x = ""
                    for e in exclude:
                        x += '--exclude={} '.format(e)
                    Utils.shell.run('rsync -aHWXh {} {}/ {}/'.format(
                        x,
                        env.paths['debootstrap'] + partition.fstab.mount,
                        m.mountpoint(partition)
                    ))
