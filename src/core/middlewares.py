import datetime
import os
from zoneinfo import ZoneInfo

from src.core.prompts import get_prompt_manager
from langchain.agents.middleware import dynamic_prompt, ModelRequest


@dynamic_prompt
def inject_system_prompt(request: ModelRequest) -> str:
    """
    注入系统提示词的时间
    """
    system_msg = get_prompt_manager().get_prompt_template_by_label(name="supervisor/system", label=os.environ.get("ENV", 'dev'))
    current_time = datetime.datetime.now(ZoneInfo("Asia/Shanghai"))
    return system_msg.compile(current_time=current_time.strftime("%Y-%m-%d %H:%M:%S"), timezone=current_time.tzinfo)