"""
    Copyright (C) 2026 KevinCrrl

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; only version 2 of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, see <https://www.gnu.org/licenses/>.
"""

from .io import IO
from evillimiter_ng.common import globals as bg

MAIN_BANNER = f"""{IO.BOLD_LIGHTRED}
 ███████╗██╗   ██╗██╗██╗      ██╗      ██╗███╗   ███╗██╗████████╗███████╗██████╗         ███╗   ██╗ ██████╗
 ██╔════╝██║   ██║██║██║      ██║      ██║████╗ ████║██║╚══██╔══╝██╔════╝██╔══██╗        ████╗  ██║██╔════╝
 █████╗  ██║   ██║██║██║      ██║      ██║██╔████╔██║██║   ██║   █████╗  ██████╔╝        ██╔██╗ ██║██║  ███╗
 ██╔══╝  ╚██╗ ██╔╝██║██║      ██║      ██║██║╚██╔╝██║██║   ██║   ██╔══╝  ██╔══██╗  ████  ██║╚██╗██║██║   ██║
 ███████╗ ╚████╔╝ ██║███████╗ ███████╗ ██║██║ ╚═╝ ██║██║   ██║   ███████╗██║  ██║        ██║ ╚████║╚██████╔╝
 ╚══════╝  ╚═══╝  ╚═╝╚══════╝ ╚══════╝ ╚═╝╚═╝     ╚═╝╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝        ╚═╝  ╚═══╝ ╚═════╝
                {IO.END_BOLD_LIGHTRED}by bitbrute  ~  limit devices on your network :3
                KevinCrrl    ~  Next Generation
                                    v{bg.VERSION}

"""
