import json
import time
import threading

import numpy as np

from bot.base.task import TaskStatus, EndTaskReason
from module.umamusume.asset.point import *
from module.umamusume.types import TurnInfo, TurnOperationType, TurnOperation
from module.umamusume.script.cultivate_task.const import SKILL_LEARN_PRIORITY_LIST
from module.umamusume.script.cultivate_task.event.manifest import get_event_choice
from module.umamusume.script.cultivate_task.parse import *

log = logger.get_logger(__name__)


def script_cultivate_main_menu(ctx: UmamusumeContext):
    img = ctx.current_screen
    current_date = parse_date(img, ctx)
    if current_date == -1:
        log.warning("Failed to parse date")
        return
    # If entering a new turn, record old turn info and create new one
    if ctx.cultivate_detail.turn_info is None or current_date != ctx.cultivate_detail.turn_info.date:
        if ctx.cultivate_detail.turn_info is not None:
            ctx.cultivate_detail.turn_info_history.append(ctx.cultivate_detail.turn_info)
        ctx.cultivate_detail.turn_info = TurnInfo()
        ctx.cultivate_detail.turn_info.date = current_date

    # Parse main interface
    if not ctx.cultivate_detail.turn_info.parse_main_menu_finish:
        parse_cultivate_main_menu(ctx, img)
        
        # Check for recreation friend notification if prioritize_recreation is enabled
        if ctx.cultivate_detail.prioritize_recreation:
            img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            from module.umamusume.asset.template import UI_RECREATION_FRIEND_NOTIFICATION
            result = image_match(img_gray, UI_RECREATION_FRIEND_NOTIFICATION)
            log.info(f"🔍 Recreation friend notification detection: {result.find_match}")
            
            if result.find_match:
                log.info("🏖️ Recreation friend notification detected - prioritizing trip")
                # Set trip operation to prioritize recreation
                ctx.cultivate_detail.turn_info.turn_operation = TurnOperation()
                ctx.cultivate_detail.turn_info.turn_operation.turn_operation_type = TurnOperationType.TURN_OPERATION_TYPE_TRIP
                
            ctx.cultivate_detail.turn_info.parse_main_menu_finish = True

    from module.umamusume.asset.race_data import get_races_for_period
    # Check if there are extra races available for current time period
    available_races = get_races_for_period(ctx.cultivate_detail.turn_info.date)
    has_extra_race = len([race_id for race_id in ctx.cultivate_detail.extra_race_list 
                         if race_id in available_races]) != 0

    # 意外情况处理
    if not ctx.cultivate_detail.turn_info.turn_learn_skill_done and ctx.cultivate_detail.learn_skill_done:
        ctx.cultivate_detail.reset_skill_learn()

    # Check if we should skip automatic skill learning
    # Only skip when manual purchase is enabled AND we're at cultivate finish
    skip_auto_skill_learning = (ctx.task.detail.manual_purchase_at_end and ctx.cultivate_detail.cultivate_finish)
    
    # Debug logging
    log.debug(f"🔍 Skill learning check - Skill points: {ctx.cultivate_detail.turn_info.uma_attribute.skill_point}, Threshold: {ctx.cultivate_detail.learn_skill_threshold}")
    log.debug(f"🔍 Manual purchase enabled: {ctx.task.detail.manual_purchase_at_end}, Cultivate finish: {ctx.cultivate_detail.cultivate_finish}")
    log.debug(f"🔍 Skip auto skill learning: {skip_auto_skill_learning}")
    
    # Automatic skill learning during normal cultivation (not at cultivate finish)
    if (ctx.cultivate_detail.turn_info.uma_attribute.skill_point > ctx.cultivate_detail.learn_skill_threshold
            and not ctx.cultivate_detail.turn_info.turn_learn_skill_done
            and not skip_auto_skill_learning):
        log.info(f"🎯 Auto-learning skills - Skill points: {ctx.cultivate_detail.turn_info.uma_attribute.skill_point}")
        if len(ctx.cultivate_detail.learn_skill_list) > 0 or not ctx.cultivate_detail.learn_skill_only_user_provided:
            ctx.ctrl.click_by_point(CULTIVATE_SKILL_LEARN)
        else:
            ctx.cultivate_detail.learn_skill_done = True
            ctx.cultivate_detail.turn_info.turn_learn_skill_done = True
        ctx.cultivate_detail.turn_info.parse_main_menu_finish = False
        return
    else:
        ctx.cultivate_detail.reset_skill_learn()

    # Check for trip operation first (prioritize recreation)
    turn_operation = ctx.cultivate_detail.turn_info.turn_operation
    if turn_operation is not None and turn_operation.turn_operation_type == TurnOperationType.TURN_OPERATION_TYPE_TRIP:
        log.info("🏖️ Executing prioritized trip operation")
        ctx.ctrl.click_by_point(CULTIVATE_TRIP)
        return

    if not ctx.cultivate_detail.turn_info.parse_train_info_finish:
        if has_extra_race or ctx.cultivate_detail.turn_info.remain_stamina < 48:
            ctx.cultivate_detail.turn_info.parse_train_info_finish = True
            return
        else:
            ctx.ctrl.click_by_point(TO_TRAINING_SELECT)
            return

    # Check other turn operations
    if turn_operation is not None:
        if turn_operation.turn_operation_type == TurnOperationType.TURN_OPERATION_TYPE_TRAINING:
            ctx.ctrl.click_by_point(TO_TRAINING_SELECT)
        elif turn_operation.turn_operation_type == TurnOperationType.TURN_OPERATION_TYPE_REST:
            ctx.ctrl.click_by_point(CULTIVATE_REST)
        elif turn_operation.turn_operation_type == TurnOperationType.TURN_OPERATION_TYPE_MEDIC:
            if 36 < ctx.cultivate_detail.turn_info.date <= 40 or 60 < ctx.cultivate_detail.turn_info.date <= 64:
                ctx.ctrl.click_by_point(CULTIVATE_MEDIC_SUMMER)
            else:
                ctx.ctrl.click_by_point(CULTIVATE_MEDIC)
        elif turn_operation.turn_operation_type == TurnOperationType.TURN_OPERATION_TYPE_TRIP:
            ctx.ctrl.click_by_point(CULTIVATE_TRIP)
        elif turn_operation.turn_operation_type == TurnOperationType.TURN_OPERATION_TYPE_RACE:
            # Check if this is a URA race operation
            race_id = turn_operation.race_id
            if race_id in [2381, 2382, 2385, 2386, 2387]:
                # For URA races, check if the URA race UI is available first
                img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                from module.umamusume.asset.template import UI_CULTIVATE_URA_RACE_1, UI_CULTIVATE_URA_RACE_2, UI_CULTIVATE_URA_RACE_3
                
                # Determine which URA race template to check based on race ID
                ura_race_available = False
                ura_phase = ""
                
                if race_id == 2381:  # Qualifier
                    ura_race_available = image_match(img_gray, UI_CULTIVATE_URA_RACE_1).find_match
                    ura_phase = "Qualifier"
                elif race_id == 2382:  # Semi-final
                    ura_race_available = image_match(img_gray, UI_CULTIVATE_URA_RACE_2).find_match
                    ura_phase = "Semi-final"
                elif race_id in [2385, 2386, 2387]:  # Final
                    ura_race_available = image_match(img_gray, UI_CULTIVATE_URA_RACE_3).find_match
                    ura_phase = "Final"
                
                if ura_race_available:
                    log.info(f"🏆 URA {ura_phase} UI detected - proceeding to race")
                    if 36 < ctx.cultivate_detail.turn_info.date <= 40 or 60 < ctx.cultivate_detail.turn_info.date <= 64:
                        ctx.ctrl.click_by_point(CULTIVATE_RACE_SUMMER)
                    else:
                        ctx.ctrl.click_by_point(CULTIVATE_RACE)
                else:
                    log.info(f"⏳ URA {ura_phase} not yet available - continuing with normal flow")
                    # Continue with normal flow - let AI decide what to do next
                    # This will trigger the normal AI logic for training/rest/recreation
                    if not ctx.cultivate_detail.turn_info.parse_train_info_finish:
                        ctx.cultivate_detail.turn_info.parse_train_info_finish = True
                        return
                    else:
                        # Let the AI decide what to do (training, rest, etc.)
                        ctx.ctrl.click_by_point(TO_TRAINING_SELECT)
            else:
                # Regular race - proceed normally
                if 36 < ctx.cultivate_detail.turn_info.date <= 40 or 60 < ctx.cultivate_detail.turn_info.date <= 64:
                    ctx.ctrl.click_by_point(CULTIVATE_RACE_SUMMER)
                else:
                    ctx.ctrl.click_by_point(CULTIVATE_RACE)


def script_cultivate_training_select(ctx: UmamusumeContext):
    if ctx.cultivate_detail.turn_info is None:
        log.warning("Turn information not initialized")
        ctx.ctrl.click_by_point(RETURN_TO_CULTIVATE_MAIN_MENU)
        return

    if ctx.cultivate_detail.turn_info.turn_operation is not None:
        if (ctx.cultivate_detail.turn_info.turn_operation.turn_operation_type ==
                TurnOperationType.TURN_OPERATION_TYPE_TRAINING):
            ctx.ctrl.click_by_point(
                TRAINING_POINT_LIST[ctx.cultivate_detail.turn_info.turn_operation.training_type.value - 1])
            time.sleep(0.5)
            ctx.ctrl.click_by_point(
                TRAINING_POINT_LIST[ctx.cultivate_detail.turn_info.turn_operation.training_type.value - 1])
            time.sleep(3)
            return
        elif (ctx.cultivate_detail.turn_info.turn_operation.turn_operation_type ==
                TurnOperationType.TURN_OPERATION_TYPE_RACE):
            # For race operations, let the AI decide what to do (training, rest, etc.)
            log.info("🏁 Race operation detected - letting AI decide next action")
            # Force AI to make a decision based on current state
            from module.umamusume.script.cultivate_task.ai import get_operation
            new_operation = get_operation(ctx)
            if new_operation and new_operation.turn_operation_type != TurnOperationType.TURN_OPERATION_TYPE_RACE:
                # AI decided to do something else (training, rest, etc.)
                log.info(f"🤖 AI decided to do {new_operation.turn_operation_type.name} instead of race")
                ctx.cultivate_detail.turn_info.turn_operation = new_operation
                # Continue with normal flow to execute the AI decision
            else:
                # AI still wants to race, proceed with race
                log.info("🏁 AI confirmed race operation - proceeding with race")
                return
        else:
            ctx.ctrl.click_by_point(RETURN_TO_CULTIVATE_MAIN_MENU)
            return

    if not ctx.cultivate_detail.turn_info.parse_train_info_finish:
        def _parse_training_in_thread(ctx, img, train_type):
            """Helper function to run parsing in a separate thread."""
            parse_training_result(ctx, img, train_type)
            parse_training_support_card(ctx, img, train_type)
        
        def _clear_training(ctx: UmamusumeContext, train_type: TrainingType):
            ctx.cultivate_detail.turn_info.training_info_list[train_type.value - 1].speed_incr = 0
            ctx.cultivate_detail.turn_info.training_info_list[train_type.value - 1].stamina_incr = 0
            ctx.cultivate_detail.turn_info.training_info_list[train_type.value - 1].power_incr = 0
            ctx.cultivate_detail.turn_info.training_info_list[train_type.value - 1].will_incr = 0
            ctx.cultivate_detail.turn_info.training_info_list[train_type.value - 1].intelligence_incr = 0
            ctx.cultivate_detail.turn_info.training_info_list[train_type.value - 1].skill_point_incr = 0
            ctx.cultivate_detail.turn_info.training_info_list[train_type.value - 1].support_card_info_list = []
            
        
        threads :list[threading.Thread] = []

        # Get extra weight for current year
        date = ctx.cultivate_detail.turn_info.date
        if date == 0:
            extra_weight = [0, 0, 0, 0, 0]
        elif date <= 24:
            extra_weight = ctx.cultivate_detail.extra_weight[0]
        elif date <= 48:
            extra_weight = ctx.cultivate_detail.extra_weight[1]
        else:
            extra_weight = ctx.cultivate_detail.extra_weight[2]

        img = ctx.current_screen
        train_type = parse_train_type(ctx, img)
        if train_type == TrainingType.TRAINING_TYPE_UNKNOWN:
            return
        viewed = train_type.value
        # Only start parsing when weight is not -1, otherwise clear
        if extra_weight[viewed-1] > -1:
            thread = threading.Thread(target=_parse_training_in_thread,
                                            args=(ctx, img, train_type))
            threads.append(thread)
            thread.start()
        else:
            _clear_training(ctx, train_type)

        for i in range(5):
            if i != (viewed - 1):
                if extra_weight[i] > -1:
                    retry = 0
                    max_retry = 3
                    ctx.ctrl.click_by_point(TRAINING_POINT_LIST[i])
                    img = ctx.ctrl.get_screen()
                    while parse_train_type(ctx, img) != TrainingType(i + 1) and retry < max_retry:
                        if retry > 2:
                            ctx.ctrl.click_by_point(TRAINING_POINT_LIST[i])
                        time.sleep(0.2)
                        img = ctx.ctrl.get_screen()
                        retry += 1
                    if retry == max_retry:
                        return
                    
                    thread = threading.Thread(target=_parse_training_in_thread,
                                            args=(ctx, img, TrainingType(i + 1)))
                    threads.append(thread)
                    thread.start()
                else:
                    _clear_training(ctx, TrainingType(i + 1))

        for thread in threads:
            thread.join()

        ctx.cultivate_detail.turn_info.parse_train_info_finish = True
    
    # Now actually perform the selected training (normal behavior)
    if ctx.cultivate_detail.turn_info.turn_operation is not None:
        if (ctx.cultivate_detail.turn_info.turn_operation.turn_operation_type ==
                TurnOperationType.TURN_OPERATION_TYPE_TRAINING):
            # Perform the selected training
            training_type = ctx.cultivate_detail.turn_info.turn_operation.training_type
            log.info(f"🏋️ Performing selected training: {training_type.name}")
            ctx.ctrl.click_by_point(
                TRAINING_POINT_LIST[training_type.value - 1])
            time.sleep(0.5)
            ctx.ctrl.click_by_point(
                TRAINING_POINT_LIST[training_type.value - 1])
            time.sleep(3)
            return
        elif (ctx.cultivate_detail.turn_info.turn_operation.turn_operation_type ==
                TurnOperationType.TURN_OPERATION_TYPE_RACE):
            # For race operations, let the AI decide what to do
            log.info("🏁 Race operation - letting AI decide based on current state")
            # Let the AI decide based on stamina, motivation, etc.
            # The AI will choose the best action (training, rest, medic, trip)
            return
    else:
        # No operation decided yet - go back to main menu to let AI decide
        log.info("🤔 No operation decided yet - returning to main menu for AI decision")
        ctx.ctrl.click_by_point(RETURN_TO_CULTIVATE_MAIN_MENU)
        return
    
    if not ctx.cultivate_detail.turn_info.parse_main_menu_finish:
        ctx.ctrl.click_by_point(RETURN_TO_CULTIVATE_MAIN_MENU)
        return


def script_main_menu(ctx: UmamusumeContext):
    if ctx.cultivate_detail.cultivate_finish:
        ctx.task.end_task(TaskStatus.TASK_STATUS_SUCCESS, EndTaskReason.COMPLETE)
        return
    ctx.ctrl.click_by_point(TO_CULTIVATE_SCENARIO_CHOOSE)


def script_scenario_select(ctx: UmamusumeContext):
    target_scenario = ctx.cultivate_detail.scenario.scenario_type()
    time.sleep(3) # If network is very poor, this might not wait enough

    for i in range(1, len(ScenarioType)):
        img = ctx.ctrl.get_screen(to_gray=True)

        if image_match(img, UI_SCENARIO[target_scenario]).find_match:
            log.info(f"Found target cultivation scenario {ctx.cultivate_detail.scenario.scenario_name()}")
            ctx.ctrl.click_by_point(TO_CULTIVATE_PREPARE_NEXT)
            return

        log.debug(f"Scenario does not match, checking next scenario")
        ctx.ctrl.swipe(x1=400, y1=600, x2=500, y2=600, duration=300, name="swipe right")
        time.sleep(1)

    log.error(f"Could not find specified scenario")
    ctx.task.end_task(TaskStatus.TASK_STATUS_FAILED, EndTaskReason.SCENARIO_NOT_FOUND)


def script_umamusume_select(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(TO_CULTIVATE_PREPARE_NEXT)


def script_extend_umamusume_select(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(TO_CULTIVATE_PREPARE_NEXT)


def script_support_card_select(ctx: UmamusumeContext):
    img = ctx.ctrl.get_screen(to_gray=True)
    if image_match(img, REF_CULTIVATE_SUPPORT_CARD_EMPTY).find_match:
        ctx.ctrl.click_by_point(TO_FOLLOW_SUPPORT_CARD_SELECT)
        return
    ctx.ctrl.click_by_point(TO_CULTIVATE_PREPARE_NEXT)


def script_follow_support_card_select(ctx: UmamusumeContext):
    img = ctx.ctrl.get_screen()
    while True:
        selected = find_support_card(ctx, img)
        if selected:
            break
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        if compare_color_equal(img[1096, 693], [125, 120, 142]):
            while True:
                img = cv2.cvtColor(ctx.ctrl.get_screen(), cv2.COLOR_BGR2RGB)
                if compare_color_equal(img[127, 697], [211, 209, 219]):
                    ctx.ctrl.swipe(x1=350, y1=400, x2=350, y2=1000, duration=200, name="")
                else:
                    break
            ctx.ctrl.click_by_point(FOLLOW_SUPPORT_CARD_SELECT_REFRESH)
            return
        ctx.ctrl.swipe(x1=350, y1=1000, x2=350, y2=400, duration=1000, name="")
        time.sleep(1)
        img = ctx.ctrl.get_screen()


def script_cultivate_final_check(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(CULTIVATE_FINAL_CHECK_START)


def script_cultivate_event(ctx: UmamusumeContext):
    img = ctx.ctrl.get_screen()
    event_name, selector_list = parse_cultivate_event(ctx, img)
    log.debug("Current event: %s", event_name)
    if len(selector_list) > 0:  # If we have any dialogue options at all
        time.sleep(0.5)
        # Avoid incomplete options, re-parse once here
        img = ctx.ctrl.get_screen()
        event_name, selector_list = parse_cultivate_event(ctx, img)
        choice_index = get_event_choice(ctx, event_name)
        # Exception tolerance
        if choice_index - 1 >= len(selector_list):  # Fixed: >= instead of >
            choice_index = 1
        ctx.ctrl.click(selector_list[choice_index - 1][0], selector_list[choice_index - 1][1],
                       "Event option-" + str(choice_index))
    else:
        log.debug("No options found")

def script_aoharuhai_race(ctx: UmamusumeContext):
    img = ctx.ctrl.get_screen(to_gray=True)
    if image_match(img, UI_AOHARUHAI_RACE_1).find_match:
        race_index = 0
    elif image_match(img, UI_AOHARUHAI_RACE_2).find_match:
        race_index = 1
    elif image_match(img, UI_AOHARUHAI_RACE_3).find_match:
        race_index = 2
    elif image_match(img, UI_AOHARUHAI_RACE_4).find_match:
        race_index = 3
    elif image_match(img, UI_AOHARUHAI_RACE_5).find_match:
        race_index = 4
    else:
        ctx.ctrl.click(360, 1180, "Confirm race result")
        return
    
    ctx.cultivate_detail.turn_info.aoharu_race_index = race_index
    ctx.ctrl.click(360, 1080, "Start Youth Cup battle")

def script_aoharuhai_race_final_start(ctx: UmamusumeContext):
    ctx.ctrl.click(360, 980, "Confirm final opponent")

def script_aoharuhai_race_select_oponent(ctx: UmamusumeContext):
    def select_opponent (race_index: int):
        match race_index:
            case 1:
                ctx.ctrl.click(360, 290, "Select first opponent")
            case 2:
                ctx.ctrl.click(360, 560, "Select second opponent")
            case 3:
                ctx.ctrl.click(360, 830, "Select third opponent")
        time.sleep(2)
        ctx.ctrl.click(360, 1080, "Start battle")
    select_opponent(ctx.task.detail.scenario_config.aoharu_config.get_opponent(ctx.cultivate_detail.turn_info.aoharu_race_index))

def script_aoharuhai_race_confirm(ctx: UmamusumeContext):
    ctx.ctrl.click(520, 920, "Confirm battle")

def script_aoharuhai_race_inrace(ctx: UmamusumeContext):
    ctx.ctrl.click(520, 1180, "View battle result")

def script_aoharuhai_race_end(ctx: UmamusumeContext):
    ctx.ctrl.click(350, 1110, "Confirm race end")

def script_aoharuhai_race_schedule(ctx: UmamusumeContext):
    ctx.ctrl.click(360, 1100, "End Youth Cup race")

def script_cultivate_goal_race(ctx: UmamusumeContext):
    log.info("�� Entering goal race function")
    img = ctx.current_screen
    current_date = parse_date(img, ctx)
    if current_date == -1:
        log.warning("Failed to parse date")
        return
    # 如果进入新的一回合，记录旧的回合信息并创建新的
    if ctx.cultivate_detail.turn_info is None or current_date != ctx.cultivate_detail.turn_info.date:
        if ctx.cultivate_detail.turn_info is not None:
            ctx.cultivate_detail.turn_info_history.append(ctx.cultivate_detail.turn_info)
        ctx.cultivate_detail.turn_info = TurnInfo()
        ctx.cultivate_detail.turn_info.date = current_date
    
    # Check if this is actually a URA race (championship)
    if ctx.cultivate_detail.turn_info.turn_operation:
        race_id = ctx.cultivate_detail.turn_info.turn_operation.race_id
        log.info(f"🏁 Current race ID: {race_id}")
        if race_id in [2381, 2382, 2385, 2386, 2387]:
            log.info("🏆 This is a URA championship race - proceeding directly to start")
            ctx.ctrl.click_by_point(CULTIVATE_GOAL_RACE_INTER_2)  # Start the race directly
        else:
            log.info(f"🎯 This is a regular race (ID: {race_id}) - entering detail interface")
            ctx.ctrl.click_by_point(CULTIVATE_GOAL_RACE_INTER_1)  # Enter detail interface first
    else:
        log.warning("No turn operation found - cannot determine race type")
        ctx.ctrl.click_by_point(CULTIVATE_GOAL_RACE_INTER_1)  # Default to detail interface


def script_cultivate_race_list(ctx: UmamusumeContext):
    time.sleep(2)
    if ctx.cultivate_detail.turn_info is None:
        log.warning("Turn information not initialized")
        ctx.ctrl.click_by_point(RETURN_TO_CULTIVATE_MAIN_MENU)
        return
    img = cv2.cvtColor(ctx.current_screen, cv2.COLOR_BGR2GRAY)
    
    # Debug template matching
    goal_match = image_match(img, REF_RACE_LIST_GOAL_RACE).find_match
    ura_match = image_match(img, REF_RACE_LIST_URA_RACE).find_match
    
    log.info(f"🔍 Template matching - Goal Race: {goal_match}, URA Race: {ura_match}")
    
    if goal_match:
        log.info("🎯 Found Goal Race - clicking to enter detail interface")
        ctx.ctrl.click_by_point(CULTIVATE_GOAL_RACE_INTER_1)
    elif ura_match:
        log.info("🏆 Found URA Race - clicking to enter detail interface")
        ctx.ctrl.click_by_point(CULTIVATE_GOAL_RACE_INTER_1)
    else:
        # Special handling for URA races - if we're in race list after URA race click, just click the race button
        if ctx.cultivate_detail.turn_info.turn_operation is None:
            log.warning("No turn operation - returning to main menu")
            ctx.ctrl.click_by_point(RETURN_TO_CULTIVATE_MAIN_MENU)
            return
        else:
            # Log the turn operation type to debug
            log.info(f"🔍 Turn operation type: {ctx.cultivate_detail.turn_info.turn_operation.turn_operation_type}")
            # For URA races, we might have a turn operation but still need to click the race button
            if ctx.cultivate_detail.turn_info.turn_operation.turn_operation_type == TurnOperationType.TURN_OPERATION_TYPE_RACE:
                race_id = ctx.cultivate_detail.turn_info.turn_operation.race_id
                log.info(f"🔍 Race operation with ID: {race_id}")
                # If it's a URA race ID or 0 (unknown), try clicking the race button
                if race_id in [2381, 2382, 2385, 2386, 2387] or race_id == 0:
                    log.info("🏆 Detected URA race operation - clicking race button directly")
                    ctx.ctrl.click(510, 1082, "URA Race Button")
                    time.sleep(1)
                    return
        if ctx.cultivate_detail.turn_info.turn_operation.turn_operation_type == TurnOperationType.TURN_OPERATION_TYPE_RACE:
            swiped = False
            while True:
                img = cv2.cvtColor(ctx.ctrl.get_screen(), cv2.COLOR_BGR2RGB)
                if not compare_color_equal(img[705, 701], [211, 209, 219]):
                    if swiped is True:
                        time.sleep(1.5)
                    break
                ctx.ctrl.swipe(x1=20, y1=850, x2=20, y2=1000, duration=200, name="")
                swiped = True
            img = ctx.ctrl.get_screen()
            while True:
                race_id = ctx.cultivate_detail.turn_info.turn_operation.race_id
                log.info(f"🔍 Looking for race ID: {race_id}")
                selected = find_race(ctx, img, race_id)
                if selected:
                    log.info(f"✅ Found race ID: {race_id}")
                    time.sleep(1)
                    ctx.ctrl.click_by_point(CULTIVATE_GOAL_RACE_INTER_1)
                    time.sleep(1)
                    return
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                if not compare_color_equal(img[1006, 701], [211, 209, 219]):
                    log.warning(f"❌ Target Race Not Found - Race ID: {race_id}")
                    # No suitable race found, use backup operation
                    if ctx.cultivate_detail.turn_info.turn_operation.race_id == 0:
                        ctx.cultivate_detail.turn_info.turn_operation.turn_operation_type = ctx.cultivate_detail.turn_info.turn_operation.turn_operation_type_replace
                    ctx.ctrl.click_by_point(RETURN_TO_CULTIVATE_MAIN_MENU)
                    break
                ctx.ctrl.swipe(x1=20, y1=1000, x2=20, y2=850, duration=1000, name="")
                time.sleep(1)
                img = ctx.ctrl.get_screen()
        else:
            ctx.ctrl.click_by_point(RETURN_TO_CULTIVATE_MAIN_MENU)


def script_cultivate_before_race(ctx: UmamusumeContext):
    img = cv2.cvtColor(ctx.current_screen, cv2.COLOR_BGR2RGB)
    p_check_skip = img[1175, 330]

    date = ctx.cultivate_detail.turn_info.date
    if date != -1:
        tactic_check_point_list = [img[668, 480], img[668, 542], img[668, 600], img[668, 670]]
        if date <= 72:
            p_check_tactic = tactic_check_point_list[ctx.cultivate_detail.tactic_list[int((date - 1) / 24)] - 1]
        else:
            p_check_tactic = tactic_check_point_list[ctx.cultivate_detail.tactic_list[2] - 1]
        if compare_color_equal(p_check_tactic, [170, 170, 170]):
            ctx.ctrl.click_by_point(BEFORE_RACE_CHANGE_TACTIC)
            return

    if p_check_skip[0] < 200 and p_check_skip[1] < 200 and p_check_skip[2] < 200:
        ctx.ctrl.click_by_point(BEFORE_RACE_START)
    else:
        ctx.ctrl.click_by_point(BEFORE_RACE_SKIP)


def script_cultivate_in_race_uma_list(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(IN_RACE_UMA_LIST_CONFIRM)


def script_in_race(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(IN_RACE_SKIP)


def script_cultivate_race_result(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(RACE_RESULT_CONFIRM)


def script_cultivate_race_reward(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(RACE_REWARD_CONFIRM)


def script_cultivate_goal_achieved(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(GOAL_ACHIEVE_CONFIRM)


def script_cultivate_goal_failed(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(GOAL_FAIL_CONFIRM)


def script_cultivate_next_goal(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(NEXT_GOAL_CONFIRM)


def script_cultivate_extend(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(CULTIVATE_EXTEND_CONFIRM)


def script_cultivate_result(ctx: UmamusumeContext):
    log.info("🏆 Cultivation Result detected - clicking confirm button")
    ctx.ctrl.click_by_point(CULTIVATE_RESULT_CONFIRM)

# 限时: 富士奇石的表演秀
def script_fujikiseki_show_result_1(ctx: UmamusumeContext):
    ctx.ctrl.click(360, 1180, "Confirm Fuji Kiseki Show mode result")

def script_fujikiseki_show_result_2(ctx: UmamusumeContext):
    ctx.ctrl.click(360, 1120, "Confirm Fuji Kiseki Show mode result")

# 1.878s 2s 0.649s (the first one is actually correct lol i didnt test the rest)
def script_cultivate_catch_doll(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(CULTIVATE_CATCH_DOLL_START, hold_duration=1888) 


def script_cultivate_catch_doll_result(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(CULTIVATE_CATCH_DOLL_RESULT_CONFIRM)


def script_cultivate_finish(ctx: UmamusumeContext):
    if not ctx.task.detail.manual_purchase_at_end:
        if not ctx.cultivate_detail.learn_skill_done or not ctx.cultivate_detail.cultivate_finish:
            ctx.cultivate_detail.cultivate_finish = True
            ctx.ctrl.click_by_point(CULTIVATE_FINISH_LEARN_SKILL)
        else:
            ctx.ctrl.click_by_point(CULTIVATE_FINISH_CONFIRM)
    else:
        # Manual purchase mode - show notification and wait for user
        if not ctx.cultivate_detail.manual_purchase_completed:
            # Check if user has clicked "Learn Skills" button (indicating they want to purchase manually)
            if not hasattr(ctx.cultivate_detail, 'manual_purchase_initiated'):
                log.info("🔧 Manual purchase mode enabled - showing web notification to user")
                try:
                    # Send web notification to UAT interface
                    import requests
                    import json
                    
                    # Send notification to web interface
                    notification_data = {
                        "type": "manual_skill_purchase",
                        "message": "Please learn skills manually, then press confirm when done",
                        "timestamp": time.time()
                    }
                    
                    try:
                        # Send to local UAT web server
                        response = requests.post(
                            "http://localhost:8071/api/manual-skill-notification",
                            json=notification_data,
                            timeout=1
                        )
                        log.info("✅ Web notification sent successfully")
                        
                        # Wait for user confirmation via web interface
                        while True:
                            try:
                                status_response = requests.get(
                                    "http://localhost:8071/api/manual-skill-notification-status",
                                    timeout=1
                                )
                                status_data = status_response.json()
                                
                                if status_data.get("confirmed"):
                                    log.info("✅ User confirmed manual skill purchase via web interface")
                                    # Mark manual purchase as completed
                                    ctx.cultivate_detail.manual_purchase_completed = True
                                    # Reset the notification state
                                    requests.post("http://localhost:8071/api/manual-skill-notification-cancel")
                                    break
                                elif status_data.get("cancelled"):
                                    log.info("❌ User cancelled manual skill purchase")
                                    # Reset the notification state
                                    requests.post("http://localhost:8071/api/manual-skill-notification-cancel")
                                    return
                                
                                time.sleep(0.5)  # Check every 500ms
                            except requests.exceptions.RequestException:
                                # If web interface is not available, fall back to console
                                break
                        
                    except requests.exceptions.RequestException as e:
                        log.warning(f"⚠️ Web notification failed: {e}")
                        # Fallback to console notification
                        print("\n" + "🔔" * 50)
                        print("🔔 MANUAL SKILL PURCHASE REQUIRED 🔔")
                        print("🔔" * 50)
                        print("Please learn skills manually, then press confirm when done.")
                        print("Press Enter in the console when you're ready to continue...")
                        print("🔔" * 50)
                        input()  # Wait for user input
                    
                    log.info("✅ User acknowledged manual purchase notification")
                except Exception as e:
                    log.error(f"❌ Failed to show notification: {e}")
                    # Fallback to simple console message
                    print("\n" + "="*50)
                    print("🔧 MANUAL SKILL PURCHASE REQUIRED")
                    print("="*50)
                    print("Please learn skills manually, then press confirm when done.")
                    print("Press Enter in the console when you're ready to continue...")
                    print("="*50)
                    input()  # Wait for user input
                
                ctx.cultivate_detail.manual_purchase_initiated = True
                # Don't click anything - let user handle manually
                return
            else:
                # User has been notified, wait for them to complete manual purchase
                # The completion will be detected in script_cultivate_learn_skill when they return
                return
        else:
            # User has completed manual skill purchase, proceed with confirmation
            log.info("✅ User completed manual skill purchase - proceeding with cultivation finish")
            ctx.cultivate_detail.learn_skill_done = True
            ctx.cultivate_detail.cultivate_finish = True
            ctx.ctrl.click_by_point(CULTIVATE_FINISH_CONFIRM)


def script_cultivate_learn_skill(ctx: UmamusumeContext):
    # Safety mechanism: If manual purchase is enabled AND we're at cultivate finish, 
    # and the user has confirmed manual purchase, immediately return to finish UI
    if (ctx.task.detail.manual_purchase_at_end and 
        ctx.cultivate_detail.cultivate_finish and 
        hasattr(ctx.cultivate_detail, 'manual_purchase_completed') and 
        ctx.cultivate_detail.manual_purchase_completed):
        log.info("🔧 Manual purchase completed - returning to cultivate finish UI")
        ctx.cultivate_detail.learn_skill_done = True
        ctx.ctrl.click_by_point(RETURN_TO_CULTIVATE_FINISH)
        return
        
    # If manual purchase is enabled AND we're at cultivate finish, handle manual purchase completion
    if ctx.task.detail.manual_purchase_at_end and ctx.cultivate_detail.cultivate_finish:
        log.info("🔧 Manual purchase mode enabled - returning to cultivate finish UI")
        # Mark manual purchase as completed since user has returned from skill menu
        ctx.cultivate_detail.manual_purchase_completed = True
        ctx.cultivate_detail.learn_skill_done = True
        ctx.ctrl.click_by_point(RETURN_TO_CULTIVATE_FINISH)
        return
        
    if ctx.cultivate_detail.learn_skill_done:
        # If skills are already learned and confirmed, exit skill learning
        log.info("✅ Skills already learned and confirmed - exiting skill learning")
        ctx.ctrl.click_by_point(RETURN_TO_CULTIVATE_FINISH)
        # Reset flags to prevent re-entering
        ctx.cultivate_detail.learn_skill_selected = False
        return
    learn_skill_list: list[list[str]]
    learn_skill_blacklist: list[str] = ctx.cultivate_detail.learn_skill_blacklist
    if ctx.cultivate_detail.cultivate_finish or not ctx.cultivate_detail.learn_skill_only_user_provided:
        if len(ctx.cultivate_detail.learn_skill_list) == 0:
            learn_skill_list = SKILL_LEARN_PRIORITY_LIST
        else:
            # If user customizes skill priority, no longer use preset priority
            learn_skill_list = ctx.cultivate_detail.learn_skill_list
    else:
        if len(ctx.cultivate_detail.learn_skill_list) == 0:
            ctx.ctrl.click_by_point(RETURN_TO_CULTIVATE_FINISH)
            ctx.cultivate_detail.learn_skill_done = True
            ctx.cultivate_detail.turn_info.turn_learn_skill_done = True
            return
        else:
            learn_skill_list = ctx.cultivate_detail.learn_skill_list

    # Traverse entire page, find all clickable skills
    skill_list = []
    while ctx.task.running():
        # Safety check: If manual purchase was confirmed, immediately return
        if (ctx.task.detail.manual_purchase_at_end and 
            ctx.cultivate_detail.cultivate_finish and 
            hasattr(ctx.cultivate_detail, 'manual_purchase_completed') and 
            ctx.cultivate_detail.manual_purchase_completed):
            log.info("🔧 Manual purchase confirmed during skill scanning - returning to finish UI")
            ctx.cultivate_detail.learn_skill_done = True
            ctx.ctrl.click_by_point(RETURN_TO_CULTIVATE_FINISH)
            return
            
        img = ctx.ctrl.get_screen()
        current_screen_skill_list = get_skill_list(img, learn_skill_list,learn_skill_blacklist)
        # Avoid duplicate counting (will occur when page turning is incomplete at page end)
        for i in current_screen_skill_list:
            if i not in skill_list:
                skill_list.append(i)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        if not compare_color_equal(img[1006, 701], [211, 209, 219]):
            break
        ctx.ctrl.swipe(x1=23, y1=1000, x2=23, y2=636, duration=1000, name="")
        time.sleep(1)
        
        # Additional safety check after each swipe
        if (ctx.task.detail.manual_purchase_at_end and 
            ctx.cultivate_detail.cultivate_finish and 
            hasattr(ctx.cultivate_detail, 'manual_purchase_completed') and 
            ctx.cultivate_detail.manual_purchase_completed):
            log.info("🔧 Manual purchase confirmed after swipe - returning to finish UI")
            ctx.cultivate_detail.learn_skill_done = True
            ctx.ctrl.click_by_point(RETURN_TO_CULTIVATE_FINISH)
            return

    log.debug("Current skill state: " + str(skill_list))

    # Bind gold skills with their subsequent skills
    for i in range(len(skill_list)):
        if i != (len(skill_list) - 1) and skill_list[i]["gold"] is True:
            skill_list[i]["subsequent_skill"] = skill_list[i + 1]["skill_name"]

    # Sort by priority
    skill_list = sorted(skill_list, key=lambda x: x["priority"])
    # TODO: Temporarily no way to handle a skill that can be clicked multiple times
    img = ctx.ctrl.get_screen()
    total_skill_point_text = re.sub("\\D", "", ocr_line(img[400: 440, 490: 665]))
    if total_skill_point_text == "":
        total_skill_point = 0
    else:
        total_skill_point = int(total_skill_point_text)
    target_skill_list = []
    target_skill_list_raw = []
    curr_point = 0
    for i in range(len(learn_skill_list) + 1):
        if (i > 0 and ctx.cultivate_detail.learn_skill_only_user_provided is True and
                not ctx.cultivate_detail.cultivate_finish):
            break
        for j in range(len(skill_list)):
            if skill_list[j]["priority"] != i or skill_list[j]["available"] is False:
                continue
            if curr_point + skill_list[j]["skill_cost"] <= total_skill_point:
                curr_point += skill_list[j]["skill_cost"]
                target_skill_list.append(skill_list[j]["skill_name"])
                target_skill_list_raw.append(skill_list[j]["skill_name_raw"])
                # If clicking a gold skill, set its bound lower skill as unclickable
                if skill_list[j]["gold"] is True and skill_list[j]["subsequent_skill"] != '':
                    for k in range(len(skill_list)):
                        if skill_list[k]["skill_name"] == skill_list[j]["subsequent_skill"]:
                            skill_list[k]["available"] = False

    # If it's URA, mark learned skills, may be used to reset inspiration event weights
    # Since skill points were calculated above, can ensure all skills in list will be learned
    if ctx.task.detail.scenario == ScenarioType.SCENARIO_TYPE_URA:
        for skill in target_skill_list:
            ctx.task.detail.scenario_config.ura_config.removeSkillFromList(skill)

    # Move up to align
    ctx.ctrl.swipe(x1=23, y1=950, x2=23, y2=968, duration=100, name="")
    time.sleep(1)

    # Remove already learned skills
    for skill in target_skill_list_raw:
        for prioritylist in ctx.cultivate_detail.learn_skill_list:
            if prioritylist.__contains__(skill):
                prioritylist.remove(skill)
    for skill in skill_list:
        for prioritylist in ctx.cultivate_detail.learn_skill_list:
            if skill['available'] is False and prioritylist.__contains__(skill['skill_name_raw']):
                prioritylist.remove(skill['skill_name_raw'])
    # If a priority is completely empty, delete it directly
    ctx.cultivate_detail.learn_skill_list = [x for x in ctx.cultivate_detail.learn_skill_list if x != []]

    # Safety check before starting skill clicking
    if (ctx.task.detail.manual_purchase_at_end and 
        ctx.cultivate_detail.cultivate_finish and 
        hasattr(ctx.cultivate_detail, 'manual_purchase_completed') and 
        ctx.cultivate_detail.manual_purchase_completed):
        log.info("🔧 Manual purchase confirmed before skill clicking - returning to finish UI")
        ctx.cultivate_detail.learn_skill_done = True
        ctx.ctrl.click_by_point(RETURN_TO_CULTIVATE_FINISH)
        return

    # Click skills
    while True:
        # Safety check: If manual purchase was confirmed, immediately return
        if (ctx.task.detail.manual_purchase_at_end and 
            ctx.cultivate_detail.cultivate_finish and 
            hasattr(ctx.cultivate_detail, 'manual_purchase_completed') and 
            ctx.cultivate_detail.manual_purchase_completed):
            log.info("🔧 Manual purchase confirmed during skill clicking - returning to finish UI")
            ctx.cultivate_detail.learn_skill_done = True
            ctx.ctrl.click_by_point(RETURN_TO_CULTIVATE_FINISH)
            return
            
        img = ctx.ctrl.get_screen()
        find_skill(ctx, img, target_skill_list, learn_any_skill=False)
        if len(target_skill_list) == 0:
            break
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        if not compare_color_equal(img[488, 701], [211, 209, 219]):
            break
        ctx.ctrl.swipe(x1=23, y1=636, x2=23, y2=1000, duration=1000, name="")
        time.sleep(1)

    log.debug("Skills to learn: " + str(ctx.cultivate_detail.learn_skill_list))
    log.debug("Skills learned: " + str([skill['skill_name'] for skill in skill_list if not skill['available']]))

    # Safety check before final confirm button click
    if (ctx.task.detail.manual_purchase_at_end and 
        ctx.cultivate_detail.cultivate_finish and 
        hasattr(ctx.cultivate_detail, 'manual_purchase_completed') and 
        ctx.cultivate_detail.manual_purchase_completed):
        log.info("🔧 Manual purchase confirmed before final confirm - returning to finish UI")
        ctx.cultivate_detail.learn_skill_done = True
        ctx.ctrl.click_by_point(RETURN_TO_CULTIVATE_FINISH)
        return

    ctx.cultivate_detail.learn_skill_done = True
    ctx.cultivate_detail.turn_info.turn_learn_skill_done = True
    
    # After learning skills, click the confirm button first, then back button
    log.info("✅ Skills learned - clicking confirm button first")
    ctx.ctrl.click_by_point(CULTIVATE_LEARN_SKILL_CONFIRM)


def script_not_found_ui(ctx: UmamusumeContext):
    """Enhanced NOT_FOUND_UI handler with goal screen fallback detection"""
    
    # Debug: Log current screen info
    if ctx.current_screen is not None:
        log.debug(f"🔍 NOT_FOUND_UI - Screen shape: {ctx.current_screen.shape}")
        
        # Try direct template matching for cultivate_result_1.png first
        try:
            import cv2
            from bot.recog.image_matcher import image_match
            from module.umamusume.asset.template import UI_CULTIVATE_RESULT_1
            
            img = ctx.current_screen
            img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            result = image_match(img_gray, UI_CULTIVATE_RESULT_1)
            
            if result.find_match:
                log.info("🏆 Cultivate Result 1 template matched! Clicking confirm button")
                ctx.ctrl.click_by_point(CULTIVATE_RESULT_CONFIRM)
                return
            else:
                log.debug("🔍 Cultivate Result 1 template not found")
                
        except Exception as e:
            log.debug(f"Template matching failed: {str(e)}")
        
        # Try to detect if this might be a cultivation result screen via OCR
        try:
            from bot.recog.ocr import ocr_line
            
            img = ctx.current_screen
            # Sample areas where cultivation result text might appear
            title_area = img[200:400, 100:620]
            title_text = ocr_line(title_area).lower()
            
            # Debug: Log what text was detected
            log.debug(f"🔍 OCR detected text: '{title_text[:100]}...'")
            
            # Check for cultivation result keywords - specifically "REWARDS" screen
            result_keywords = ['rewards', 'result', 'cultivation', '完成', '结果', '培育', '奖励']
            if any(keyword in title_text for keyword in result_keywords):
                log.info(f"🏆 Potential cultivation result detected: '{title_text[:50]}...'")
                log.info("🏆 Attempting to click cultivation result confirm button")
                ctx.ctrl.click_by_point(CULTIVATE_RESULT_CONFIRM)
                return
                
            # Also check for "Bond Level" and "Total Fans" which are specific to this rewards screen
            bond_area = img[400:600, 100:620]
            bond_text = ocr_line(bond_area).lower()
            log.debug(f"🔍 Bond area OCR: '{bond_text[:100]}...'")
            if 'bond level' in bond_text or 'total fans' in bond_text:
                log.info(f"🏆 Rewards screen detected via bond/fans text: '{bond_text[:50]}...'")
                log.info("🏆 Attempting to click cultivation result confirm button")
                ctx.ctrl.click_by_point(CULTIVATE_RESULT_CONFIRM)
                return
                
        except Exception as e:
            log.debug(f"Cultivation result detection failed: {str(e)}")
    
    # Try to detect goal screens through OCR/text detection as fallback
    try:
        import cv2
        from bot.recog.ocr import ocr_line
        
        img = ctx.current_screen
        if img is not None:
            # Convert to grayscale for OCR
            img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Sample common areas where goal text might appear
            # Top center area (typical for goal titles)
            title_area = img_gray[200:400, 100:620]  # Adjust based on screen resolution
            title_text = ocr_line(title_area).lower()
            
            # Middle area (for goal descriptions/buttons)
            middle_area = img_gray[800:1000, 200:560]
            middle_text = ocr_line(middle_area).lower()
            
            # Check for goal-related keywords (both English and Chinese)
            goal_keywords = ['goal', 'complete', 'achieved', 'failed', 'next', 'finish', 'target', 
                           'objective', '目标', '达成', '完成', '失败', '下一个']
            
            combined_text = f"{title_text} {middle_text}"
            
            # Detect goal screens
            if any(keyword in combined_text for keyword in goal_keywords):
                log.info(f"🎯 Fallback goal screen detected: '{combined_text[:50]}...'")
                
                # Determine goal type and click appropriate position
                if any(word in combined_text for word in ['complete', 'achieved', '达成', '完成']):
                    log.info(f"✅ Goal Achieved detected - clicking confirmation")
                    ctx.ctrl.click_by_point(GOAL_ACHIEVE_CONFIRM)
                    return
                elif any(word in combined_text for word in ['failed', '失败']):
                    log.info(f"❌ Goal Failed detected - clicking confirmation")
                    ctx.ctrl.click_by_point(GOAL_FAIL_CONFIRM)
                    return
                elif any(word in combined_text for word in ['next', '下一个']):
                    log.info(f"➡️ Next Goal detected - clicking confirmation")
                    ctx.ctrl.click_by_point(NEXT_GOAL_CONFIRM)
                    return
                else:
                    # Generic goal screen - try standard position
                    log.info(f"🎯 Generic goal screen - using standard position")
                    ctx.ctrl.click(370, 1110, "Generic goal confirmation")
                    return
            
    except Exception as e:
        log.debug(f"Goal detection fallback failed: {str(e)}")
    
    # Original fallback if goal detection fails
    log.debug("🔍 No specific UI detected - using default fallback click")
    ctx.ctrl.click(719, 1, "Default fallback click")


def script_receive_cup(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(CULTIVATE_RECEIVE_CUP_CLOSE)


def script_cultivate_level_result(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(CULTIVATE_LEVEL_RESULT_CONFIRM)


def script_factor_receive(ctx: UmamusumeContext):
    if ctx.cultivate_detail.parse_factor_done:
        ctx.ctrl.click_by_point(CULTIVATE_FACTOR_RECEIVE_CONFIRM)
    else:
        time.sleep(2)
        parse_factor(ctx)


def script_historical_rating_update(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(HISTORICAL_RATING_UPDATE_CONFIRM)


def script_scenario_rating_update(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(SCENARIO_RATING_UPDATE_CONFIRM)
