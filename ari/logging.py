import pathlib
import sys
from datetime import datetime # What?? dont get it but it works


import logging.handlers
from logging import LogRecord


import rich
from rich.theme import Theme
from rich.style import Style
from rich.console import group
from rich.traceback import PathHighlighter, Traceback
from rich.logging import RichHandler
from rich._log_render import LogRender
from rich.text import Text
from rich.highlighter import NullHighlighter
from rich.syntax import ANSISyntaxTheme, PygmentsSyntaxTheme  # DEP-WARN

from typing import List, Tuple, Optional

from pygments.styles.monokai import MonokaiStyle  # DEP-WARN
from pygments.token import (
    Comment,
    Error,
    Keyword,
    Name,
    Number,
    Operator,
    String,
    Token,
)
SYNTAX_THEME = {
    Token: Style(),
    Comment: Style(color="bright_black"),
    Keyword: Style(color="cyan", bold=True),
    Keyword.Constant: Style(color="bright_magenta"),
    Keyword.Namespace: Style(color="bright_red"),
    Operator: Style(bold=True),
    Operator.Word: Style(color="cyan", bold=True),
    Name.Builtin: Style(bold=True),
    Name.Builtin.Pseudo: Style(color="bright_red"),
    Name.Exception: Style(bold=True),
    Name.Class: Style(color="bright_green"),
    Name.Function: Style(color="bright_green"),
    String: Style(color="yellow"),
    Number: Style(color="cyan"),
    Error: Style(bgcolor="red"),
}



class RotatingFileHandler(logging.handlers.RotatingFileHandler):
    

    def __init__(
        self,
        stem: str,
        directory: pathlib.Path,
        maxBytes: int = 0,
        backupCount: int = 0,
        encoding: Optional[str] = None,
    ) -> None:
        self.baseStem = stem
        self.directory = directory.resolve()
        # Scan for existing files in directory, append to last part of existing log
        log_part_re = re.compile(rf"{stem}-part(?P<partnum>\d)\.log")
        highest_part = 0
        for path in directory.iterdir():
            match = log_part_re.match(path.name)
            if match and int(match["partnum"]) > highest_part:
                highest_part = int(match["partnum"])
        if highest_part:
            filename = directory / f"{stem}-part{highest_part}.log"
        else:
            filename = directory / f"{stem}.log"
        super().__init__(
            filename,
            mode="a",
            maxBytes=maxBytes,
            backupCount=backupCount,
            encoding=encoding,
            delay=False,
        )

    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None
        initial_path = self.directory / f"{self.baseStem}.log"
        if self.backupCount > 0 and initial_path.exists():
            initial_path.replace(self.directory / f"{self.baseStem}-part1.log")

        match = re.match(
            rf"{self.baseStem}(?:-part(?P<part>\d))?\.log", pathlib.Path(self.baseFilename).name
        )
        latest_part_num = int(match.groupdict(default="1").get("part", "1"))
        if self.backupCount < 1:
            # No backups, just delete the existing log and start again
            pathlib.Path(self.baseFilename).unlink()
        elif latest_part_num > self.backupCount:
            # Rotate files down one
            # red-part2.log becomes red-part1.log etc, a new log is added at the end.
            for i in range(1, self.backupCount + 1):
                next_log = self.directory / f"{self.baseStem}-part{i + 1}.log"
                if next_log.exists():
                    prev_log = self.directory / f"{self.baseStem}-part{i}.log"
                    next_log.replace(prev_log)
        else:
            # Simply start a new file
            self.baseFilename = str(
                self.directory / f"{self.baseStem}-part{latest_part_num + 1}.log"
            )

        self.stream = self._open()



class FixedMonokaiStyle(MonokaiStyle):
    styles = {**MonokaiStyle.styles, Token: "#f8f8f2"}

class AriTraceBack(Traceback):
    # Dep-WARN
    @group()
    def _render_stack(self, stack):
        for obj in super().render_stack.__wrapped__(self, stack):
            if obj != "":
                yield obj

class AriLogRender(LogRender):
    
    def __call__(
            self,
            console,
            renderables,
            log_time=None,
            time_format=None,
            level="",
            path=None,
            line_no=None,
            link_path=None,
            logger_name=None,
    ):
        output = Text()
        # Time Rendering
        if self.show_time:
            log_time = log_time or console.get_datetime()
            log_time_display = log_time.strtime(time_format or self.time_format)
            if log_time_display == self._last_time:
                output.append(" " * (len(log_time_display) + 1))
            else:
                output.append(f"{log_time_display} ", style="log.time")
                self._last_time = log_time_display

        #Log Level Rendering
        if self.show_level:
            output.append(level)
            output.append(" ")

        #Logger Name Rendering
        if logger_name:
            output.append(f"[{logger_name}] ", style="bright_black")

        #Main Content Rendering
        output.append(*renderables)

        #Path Rendering
        if self.show_path and path:
            path_text = Text()
            path_text.append(path, tyle=f"link file://{link_path}" if link_path else "")
            if line_no:
                path_text.append(f":{line_no}")
            output.append(path_text)

        return output

class AriRichHandler(RichHandler):
    """Adaptation of Rich's RichHandler to manually adjust the path to a logger name"""
    
    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs)
        self._log_render = AriLogRender(
            show_time=self._log_render.show_time,
            show_level=self._log_render.show_level,
            show_path=self._log_render.show_path,
            level_width=self._log_render.level_width,
        )
    
    def get_level_text(self, record: LogRecord) -> Text:
        """Get the level name from the record.

        Args:
            record (LogRecord): LogRecord instance.

        Returns:
            Text: A tuple of the style and level name.
        """
        level_text = super().get_level_text(record)
        level_text.stylize("bold")
        return level_text

    def emit(self, record: LogRecord) -> None:
        """Invoked by logging"""
        path = pathlib.Path(record.pathname).name
        level = self.get_level_text(record)
        message = self.format(record)
        time_format = None if self.formatter is None else self.formatter.datefmt
        log_time = datetime.fromtimestamp(record.created)
        traceback = None

        if self.rich_tracebacks and record.exc_info and record.exc_info != (None, None, None):
            exc_type, exc_value, exc_traceback = record.exc_info
            assert exc_type is not None
            assert exc_value is not None
            # Where is this coming from?? will research more
            traceback = AriTraceBack.from_exception(
                exc_type,
                exc_value,
                exc_traceback,
                width=self.tracebacks_width,
                extra_lines=self.tracebacks_extra_lines,
                theme=self.tracebacks_theme,
                word_wrap=self.tracebacks_word_wrap,
                show_locals=self.tracebacks_show_locals,
                locals_max_length=self.locals_max_length,
                locals_max_string=self.locals_max_string,
                indent_guides=False,
            )
            message = record.getMessage()
        
        use_markup = getattr(record, "markup") if hasattr(record, "markup") else self.markup

        if use_markup:
            message_text = Text.from_markup(message)
        else:
            message_text = Text(message)
        if self.highlighter:
            message_text = self.highlighter(message_text)
        if self.KEYWORDS:
            message_text.highlight_words(self.KEYWORDS, "logging.keyword")

        self.console.print(
             self._log_render(
                self.console,
                [message_text],
                log_time=log_time,
                time_format=time_format,
                level=level,
                path=path,
                line_no=record.lineno,
                link_path=record.pathname if self.enable_link_path else None,
                logger_name=record.name,
            ),
            soft_wrap=True,
        )
        if traceback:
            self.console.print(traceback)    


def init_logging(level: int, location: pathlib.Path) -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    dpy_logger = logging.getLogger("discord")
    dpy_logger.setLevel(logging.INFO)

    rich_console = rich.get_console()
    rich_console.push_theme(
        Theme(
            {
                "log.time": Style(dim=True),
                "logging.level.warning": Style(color="yellow"),
                "logging.level.critical": Style(color="white", bgcolor="red"),
                "logging.level.verbose": Style(color="magenta", italic=True, dim=True),
                "logging.level.trace": Style(color="white", italic=True, dim=True),
                "repr.number": Style(color="cyan"),
                "repr.url": Style(underline=True, italic=True, bold=False, color="cyan"),
            }
        )
    )

    # Grab from config if the logger is active or not
    # default true
    enable_rich_logging = True

    rich_console.file = sys.stdout

    PathHighlighter.highlights = []

    file_formatter = logging.Formatter(
        "[{asctime}] [{levelname}] {name}: {message}", datefmt="%Y-%m-%d %H:%M:%S", style="{"
    )

    if enable_rich_logging is True:
        rich_formatter = logging.Formatter("{message}", datefmt="[%X]", style="{")

        stdout_handler = AriRichHandler(
            rich_tracebacks=True,
            show_path=False,
            highlighter=NullHighlighter(),
            tracebacks_extra_lines=3,
            tracebacks_show_locals=True,
            tracebacks_theme=(
                PygmentsSyntaxTheme(FixedMonokaiStyle)
                if rich_console.color_system == "truecolor"
                else ANSISyntaxTheme(SYNTAX_THEME)
            ),
        )
        stdout_handler.setFormatter(rich_formatter)
        
    else:
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(file_formatter)
    
    root_logger.addHandler(stdout_handler)
    logging.captureWarnings(True)

    #TODO: Implement log files such as critical error or banned/ muted users for logging

