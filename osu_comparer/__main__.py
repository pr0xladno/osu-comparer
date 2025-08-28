import sys
import logging
from osu_comparer import gui, cli

if "--debug" in sys.argv:
    logging_level = logging.DEBUG
elif "--info" in sys.argv:
    logging_level = logging.INFO
else:
    logging_level = logging.CRITICAL

logging.basicConfig(
    level=logging_level,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

if "--cli" in sys.argv:
    from . import cli
    import asyncio

    asyncio.run(cli.main())
else:
    from . import gui

    gui.main()
