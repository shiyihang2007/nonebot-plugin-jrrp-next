import datetime
import random

from nonebot import CommandGroup, get_plugin_config, logger, require
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageEvent, Message, MessageSegment
from nonebot.params import CommandArg
from nonebot.typing import T_State
from nonebot.plugin import PluginMetadata

from .configs import Config, LocalConfig
from .draw_img import draw_img
from .draw_rank import draw_rank
from .rank_data import RankData
from .utils import get_jrrp


require("nonebot_plugin_localstore")

import nonebot_plugin_localstore as store  # noqa: E402

config = LocalConfig(
    store.get_config_file(
        plugin_name="nonebot_plugin_jrrp_next", filename="config.json"
    ),
    get_plugin_config(Config).jrrp_next,
)
rankDataFile = store.get_data_file(
    plugin_name="nonebot_plugin_jrrp_next", filename="ranks.json"
)
rankDataFoolishFile = store.get_data_file(
    plugin_name="nonebot_plugin_jrrp_next", filename="ranksFool.json"
)
rankData: RankData = RankData(rankDataFile)
rankDataFoolish: RankData = RankData(rankDataFoolishFile)

# 命令注册
__plugin_meta__ = PluginMetadata(
    name="jrrp",
    description="今日人品",
    usage=(
        "  jrrp 查询今日人品\n"
        "  jrrp.rank <style[2]> <color[#0066CC]> 查询人品排行\n"
        "  jrrp.help 显示帮助列表\n"
    ),
    type="application",
    homepage="https://www.github.com/shiyihang2007/nonebot-plugin-jrrp-next/",
    config=Config,
    supported_adapters={"~onebot.v11"},
    extra={
        "unique_name": "nonebot_plugin_jrrp_next_m",
        "example": "",
        "author": "shiyihang <467557146@qq.com>",
        "version": "0.0.1",
    },
)


async def is_enabled(event: GroupMessageEvent) -> bool:
    _, group_id, user_id = event.get_session_id().split("_")
    # 不回复黑名单用户
    if user_id in config["ban_user"]:
        return False
    # 在允许的群聊中启用
    if group_id in config["groups_enabled"]:
        return True
    return False


async def is_admin(bot: Bot, event: MessageEvent, state: T_State) -> bool:
    if not await to_me()(bot, event, state):
        return False
    user_id: str = event.get_user_id()
    if isinstance(event, GroupMessageEvent):
        group_id: str = str(event.group_id)
        user_info: dict = await bot.call_api(
            "get_group_member_info", **{"group_id": group_id, "user_id": user_id}
        )
        user_role: str = user_info["role"]
        # 只允许管理员使用
        if user_role in ["owner", "admin"]:
            return True
        return False
    # 禁用私聊
    return False

RP_COMMAND_GROUP = CommandGroup("jrrp", priority=config["command_priority"], prefix_aliases=True)
JRRP_COMMAND = RP_COMMAND_GROUP.command(
    tuple(), aliases={"今日人品", "rp"}, rule=is_enabled)
RANK_COMMAND = RP_COMMAND_GROUP.command(
    "rank", aliases={"人品排行", "rk"}, rule=is_enabled)
FOOL_MODE_COMMAND = RP_COMMAND_GROUP.command(
    "fool", aliases={"愚人节模式"}, rule=is_enabled)
FOOL_RP_COMMAND = RP_COMMAND_GROUP.command(
    "foolrank", aliases={"指定人品"}, rule=is_enabled)

ENABLE_COMMAND = RP_COMMAND_GROUP.command(
    "enable", aliases={"启用"}, rule=is_admin)
DISABLE_COMMAND = RP_COMMAND_GROUP.command(
    "disable", aliases={"禁用"}, rule=is_admin)


@ENABLE_COMMAND.handle()
async def _(event: GroupMessageEvent):
    global config
    group_id = str(event.group_id)
    if group_id in config["groups_enabled"]:
        await ENABLE_COMMAND.finish(f"群聊 {group_id} 已在白名单中")
    config["groups_enabled"].add(group_id)
    await ENABLE_COMMAND.send(f"群聊 {group_id} 加入了白名单")


@DISABLE_COMMAND.handle()
async def _(event: GroupMessageEvent):
    global config
    group_id = str(event.group_id)
    if group_id not in config["groups_enabled"]:
        await DISABLE_COMMAND.finish(f"群聊 {group_id} 不在白名单中")
    config["groups_enabled"].remove(group_id)
    await DISABLE_COMMAND.send(f"群聊 {group_id} 退出了白名单")


@JRRP_COMMAND.handle()
async def _(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    global rankData
    global rankDataFoolish

    args = arg.extract_plain_text().split()
    _jrrp: int = 0
    group_id = event.group_id

    if len(args) == 0:
        user_id = event.user_id
        _jrrp = get_jrrp(str(user_id))
    else:
        user_id = int(args[0])
        _jrrp = get_jrrp(str(user_id))

    if config["fool_mode"] and str(user_id) in config["fool_rp"]:
        _jrrp = config["fool_rp"][str(user_id)]

    USER_DATA: dict = await bot.call_api("get_stranger_info", **{"user_id": user_id})
    nickname = str(USER_DATA.get("nickname"))
    localtime = datetime.datetime.now()
    url = random.choice(config["image_url_list"])
    try:
        image = await draw_img(user_id, _jrrp, nickname, url, localtime)
    except Exception as e:
        logger.warning(f"Error at draw_img: {e}")
        image = "Bot出了点问题, 返回文字版:\n您今天的人品值是: " + str(_jrrp)
    # image = await draw_img(user_id, _jrrp, nickname, url, localtime)
    if config["fool_mode"]:
        rankDataFoolish.insert(str(group_id), (str(user_id), nickname, _jrrp))
    else:
        rankData.insert(str(group_id), (str(user_id), nickname, _jrrp))
    await JRRP_COMMAND.finish(image)


@RANK_COMMAND.handle()
async def _(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    group_id = str(event.group_id)
    args = arg.extract_plain_text().split()

    style: int = 2
    color: tuple[int, int, int] = (0, 102, 204)
    if len(args) >= 1:
        style: int = int(args[0])
    if len(args) >= 2:
        color: tuple[int, int, int] = (
            int(args[1][0:2], base=16),
            int(args[1][2:4], base=16),
            int(args[1][4:6], base=16),
        )

    rankRecord = (
        rankData.load_rank(group_id)
        if not config["fool_mode"]
        else rankDataFoolish.load_rank(group_id)
    )
    await RANK_COMMAND.finish(
        (
            await draw_rank(
                rankRecord,
                style,
                color,
            )
        )
        if len(rankRecord) > 0
        else "暂无记录, 无法显示"
    )


@FOOL_MODE_COMMAND.handle()
async def _(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    global config
    args: list[str] = arg.extract_plain_text().split()

    config["fool_mode"] = args[0] if len(args) > 0 else not config["fool_mode"]
    await FOOL_MODE_COMMAND.finish(
        f'愚人节模式 {"已启用" if config["fool_mode"] else "已禁用"}'
    )


@FOOL_RP_COMMAND.handle()
async def _(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    global config
    global rankDataFoolish

    if not config["fool_mode"]:
        await FOOL_RP_COMMAND.finish("请先启用愚人节模式!")
    args: list[str] = arg.extract_plain_text().split()

    if len(args) < 2:
        await FOOL_RP_COMMAND.finish("请指定 user_id 和 rp")
    user_id: str = args[0]
    group_id = str(event.group_id)
    USER_DATA: dict = await bot.call_api("get_stranger_info", **{"user_id": user_id})
    nickname = str(USER_DATA.get("nickname"))

    try:
        rp = int(args[1])
    except Exception as e:
        await FOOL_RP_COMMAND.finish(f"错误: {e}")
    config["fool_rp"][user_id] = rp
    rankDataFoolish.insert(group_id, (user_id, nickname, rp))
    await FOOL_RP_COMMAND.finish(MessageSegment.at(user_id) + f" 的 RP 已设为 {rp}")
