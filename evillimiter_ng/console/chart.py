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


class BarChart:
    def __init__(self, draw_char="▇", max_bar_length=30):
        self.draw_char = draw_char
        self.max_bar_length = max_bar_length

        self._data = []

    def add_value(self, value, prefix, suffix=""):
        self._data.append({"value": value, "prefix": prefix, "suffix": suffix})

    def get(self, reverse=False):
        def remap(n, old_min, old_max, new_min, new_max):
            return (
                ((n - old_min) * (new_max - new_min)) / (old_max - old_min)
            ) + new_min

        self._data.sort(reverse=reverse, key=lambda x: x["value"])

        max_value = self._data[0]["value"] if reverse else self._data[-1]["value"]
        max_prefix_length = max([len(x["prefix"]) for x in self._data]) + 1

        chart = ""

        for value in self._data:
            if max_value == 0:
                bar_length = 0
            else:
                bar_length = round(
                    remap(value["value"], 0, max_value, 0, self.max_bar_length)
                )

            chart += f"{value['prefix']}{' ' * (max_prefix_length - len(value['prefix']))}: {self.draw_char * bar_length} {value['suffix']}\n"

        return chart[:-1]
