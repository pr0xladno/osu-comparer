import sys
import asyncio
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QProgressBar,
    QMessageBox,
    QHeaderView,
)
from PyQt6.QtCore import Qt
from qasync import QEventLoop, asyncSlot
from osu_comparer.api import (
    fetch_beatmap_info,
    get_top_plays,
    get_user_id_by_name,
    get_user_score_on_beatmap,
)
from osu_comparer.compare import compare_scores
from osu_comparer.models import Comparison
from osu_comparer.utils import make_score_url, mods_to_str

DEFAULT_LIMIT = 100


class OsuComparerGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("osu! Score Comparer")
        self.resize(1600, 900)

        layout = QVBoxLayout()

        # Input fields
        input_layout = QHBoxLayout()
        self.user_a_input = QLineEdit()
        self.user_a_input.setPlaceholderText("Username A")
        self.user_b_input = QLineEdit()
        self.user_b_input.setPlaceholderText("Username B")
        self.limit_input = QLineEdit(str(DEFAULT_LIMIT))
        self.limit_input.setPlaceholderText("Limit")
        self.compare_btn = QPushButton("Compare")
        self.compare_btn.clicked.connect(self.on_compare_clicked)

        input_layout.addWidget(QLabel("User A:"))
        input_layout.addWidget(self.user_a_input)
        input_layout.addWidget(QLabel("User B:"))
        input_layout.addWidget(self.user_b_input)
        input_layout.addWidget(QLabel("Limit:"))
        input_layout.addWidget(self.limit_input)
        input_layout.addWidget(self.compare_btn)

        layout.addLayout(input_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # Results table
        self.table = QTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels(
            [
                "Beatmap",
                "Difficulty",
                "User A PP",
                "User A Accuracy",
                "User A Mods",
                "User B PP",
                "User B Accuracy",
                "User B Mods",
                "Status",
                "Links",
            ]
        )
        layout.addWidget(self.table)

        self.setLayout(layout)

        for col in range(self.table.columnCount()):
            self.table.horizontalHeader().setSectionResizeMode(
                col, QHeaderView.ResizeMode.Interactive
        )
        self.table.horizontalHeader().setMaximumSectionSize(300) 

    def append_table_row(self, comp: Comparison, username_a, username_b):
        row = self.table.rowCount()
        self.table.insertRow(row)

        score_a = comp.score_a
        score_b = comp.score_b
        bm = score_b.beatmap
        bmset = comp.beatmapset

        # Beatmap info
        self.table.setItem(row, 0, QTableWidgetItem(f"{bmset.artist} - {bmset.title}"))

        self.table.setItem(row, 1, QTableWidgetItem(f"[{bm.version}]"))

        # User A
        self.table.setItem(
            row, 2, QTableWidgetItem(f"{score_a.pp:.2f}" if score_a else "N/A")
        )
        self.table.setItem(
            row,
            3,
            QTableWidgetItem(f"{score_a.accuracy*100:.2f}%" if score_a else "N/A"),
        )
        self.table.setItem(
            row, 4, QTableWidgetItem(mods_to_str(score_a) if score_a else "N/A")
        )

        # User B
        self.table.setItem(row, 5, QTableWidgetItem(f"{score_b.pp:.2f}"))
        self.table.setItem(row, 6, QTableWidgetItem(f"{score_b.accuracy*100:.2f}%"))
        self.table.setItem(
            row, 7, QTableWidgetItem(mods_to_str(score_b) if score_b else "N/A")
        )

        # Status
        self.table.setItem(row, 8, QTableWidgetItem(comp.type))

        # Links (QLabel with HTML)
        links_html = ""
        if score_a:
            links_html += f'<a href="{make_score_url(score_a)}">{username_a}</a> '
        links_html += f'<a href="{make_score_url(score_b)}">{username_b}</a> '
        links_html += f'<a href="https://osu.ppy.sh/b/{bm.id}">Beatmap</a>'

        link_label = QLabel()
        link_label.setTextFormat(Qt.TextFormat.RichText)
        link_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextBrowserInteraction
        )
        link_label.setOpenExternalLinks(True)
        link_label.setText(links_html)

        self.table.setCellWidget(row, 9, link_label)

    @asyncSlot()
    async def on_compare_clicked(self):
        username_a = self.user_a_input.text().strip()
        username_b = self.user_b_input.text().strip()
        try:
            limit = int(self.limit_input.text())
        except ValueError:
            limit = DEFAULT_LIMIT

        if not username_a or not username_b:
            QMessageBox.warning(self, "Input Error", "Please enter both usernames.")
            return

        self.compare_btn.setEnabled(False)
        self.table.setRowCount(0)
        self.progress_bar.setValue(0)

        await self.run_comparison(username_a, username_b, limit)

    async def run_comparison(self, username_a, username_b, limit):
        try:
            user_id_a = await get_user_id_by_name(username_a)
            user_id_b = await get_user_id_by_name(username_b)
        except ValueError as e:
            QMessageBox.critical(self, "Error", str(e))
            self.compare_btn.setEnabled(True)
            return

        scores_b = await get_top_plays(user_id_b, limit=limit)
        beatmaps_b = [score.beatmap for score in scores_b]

        total_steps = len(beatmaps_b) * 2
        self.progress_bar.setMaximum(total_steps)
        self.progress_bar.setValue(0)

        async def run_with_index(idx, coro):
            result = await coro
            self.progress_bar.setValue(self.progress_bar.value() + 1)
            return idx, result

        tasks_scores = [
            run_with_index(i, get_user_score_on_beatmap(user_id_a, bm.id))
            for i, bm in enumerate(beatmaps_b)
        ]
        scores_a = [None] * len(tasks_scores)
        for coro in asyncio.as_completed(tasks_scores):
            idx, score = await coro
            scores_a[idx] = score

        comparisons = await compare_scores(scores_a, scores_b)

        beatmap_tasks = [
            run_with_index(i, fetch_beatmap_info(comp.score_b.beatmap))
            for i, comp in enumerate(comparisons)
        ]
        beatmap_results = await asyncio.gather(*beatmap_tasks)

        for (_, bmset), comp in zip(beatmap_results, comparisons):
            comp.beatmapset = bmset

        for comp in comparisons:
            self.append_table_row(comp, username_a, username_b)

        self.table.resizeColumnsToContents()
        self.progress_bar.setValue(0)
        self.compare_btn.setEnabled(True)


def main():
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = OsuComparerGUI()
    window.show()

    with loop:
        try:
            loop.run_forever()
        finally:
            loop.close()


if __name__ == "__main__":
    main()
