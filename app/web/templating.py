from fastapi.templating import Jinja2Templates

from app.lib.format import format_signed, kickoff_date, kickoff_time, season_label, status_label

templates = Jinja2Templates(directory="app/templates")

templates.env.filters["season_label"] = season_label
templates.env.filters["format_signed"] = format_signed
templates.env.filters["kickoff_time"] = kickoff_time
templates.env.filters["kickoff_date"] = kickoff_date
templates.env.filters["status_label"] = status_label
