import cv2
import time

from bot.recog.image_matcher import image_match
from module.umamusume.context import UmamusumeContext
from module.umamusume.script.cultivate_task.ai import get_operation
from module.umamusume.asset.point import *
from module.umamusume.asset.template import *
import bot.base.log as logger

log = logger.get_logger(__name__)


def before_hook(ctx: UmamusumeContext):
    img = cv2.cvtColor(ctx.current_screen, cv2.COLOR_BGR2GRAY)
    if image_match(img, REF_HOME_GIFT).find_match:
        ctx.ctrl.click(552, 1082, "resume 1")
        time.sleep(1)
        img = cv2.cvtColor(ctx.ctrl.get_screen(), cv2.COLOR_BGR2GRAY)
        if image_match(img, REF_RESUME_CAREER).find_match:
            ctx.ctrl.click(505, 908, "resume 2")
        return
    if image_match(img, REF_RESUME_CAREER).find_match:
        ctx.ctrl.click(505, 908, "resume 2")
        return



def after_hook(ctx: UmamusumeContext):
    img = cv2.cvtColor(ctx.current_screen, cv2.COLOR_BGR2GRAY)
    if image_match(img, BTN_SKIP).find_match:
        ctx.ctrl.click_by_point(SKIP)
    if image_match(img, BTN_SKIP_OFF).find_match:
        ctx.ctrl.click_by_point(SCENARIO_SKIP_OFF)
    if image_match(img, BTN_SKIP_SPEED_1).find_match:
        ctx.ctrl.click_by_point(SCENARIO_SKIP_SPEED_1)
    if ctx.cultivate_detail and ctx.cultivate_detail.turn_info is not None:
        if ctx.cultivate_detail.turn_info.parse_train_info_finish and ctx.cultivate_detail.turn_info.parse_main_menu_finish:
            if not ctx.cultivate_detail.turn_info.turn_info_logged:
                ctx.cultivate_detail.turn_info.log_turn_info(ctx.task.detail.scenario)
                ctx.cultivate_detail.turn_info.turn_info_logged = True
            if ctx.cultivate_detail.turn_info.turn_operation is None:
                # Only get operation if we haven't already decided on training
                # This prevents AI from overriding training decisions with race decisions
                # Also check if we're in training selection screen - don't override training decisions there
                from module.umamusume.asset.template import UI_CULTIVATE_TRAINING_SELECT
                in_training_select = image_match(img, UI_CULTIVATE_TRAINING_SELECT).find_match
                
                if not in_training_select:
                    log.info(f"🔍 Not in training selection screen - calling AI decision")
                    log.info(f"🔍 Extra race list: {ctx.cultivate_detail.extra_race_list}")
                    log.info(f"🔍 Debut race win status: {ctx.cultivate_detail.debut_race_win}")
                    ctx.cultivate_detail.turn_info.turn_operation = get_operation(ctx)
                    ctx.cultivate_detail.turn_info.turn_operation.log_turn_operation()
                else:
                    log.info("🔍 In training selection screen - skipping AI decision to avoid overriding training")




