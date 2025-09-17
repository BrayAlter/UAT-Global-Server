from module.umamusume.context import *
from module.umamusume.types import TurnOperation
from module.umamusume.script.cultivate_task.support_card import get_support_card_score
import numpy as np
import cv2
from module.umamusume.asset.template import UI_CULTIVATE_URA_RACE_1, UI_CULTIVATE_URA_RACE_2, UI_CULTIVATE_URA_RACE_3
from bot.recog.image_matcher import image_match
log = logger.get_logger(__name__)

# Simple cache for race data to avoid repeated lookups
_race_cache = {}

def _get_races_for_period_cached(period: int) -> list[int]:
    """Cached version of get_races_for_period to avoid repeated CSV reads"""
    if period not in _race_cache:
        from module.umamusume.asset.race_data import get_races_for_period
        _race_cache[period] = get_races_for_period(period)
    return _race_cache[period]


def get_operation(ctx: UmamusumeContext) -> TurnOperation | None:
    turn_operation = TurnOperation()
    if not ctx.cultivate_detail.debut_race_win:
        turn_operation.turn_operation_type = TurnOperationType.TURN_OPERATION_TYPE_RACE
    # this is stupid change later
    if ctx.cultivate_detail.turn_info.medic_room_available and ctx.cultivate_detail.turn_info.remain_stamina <= 80:
        log.info(f"🏥 Fast path: Low stamina ({ctx.cultivate_detail.turn_info.remain_stamina}) - prioritizing medic")
        turn_operation.turn_operation_type = TurnOperationType.TURN_OPERATION_TYPE_MEDIC
        return turn_operation
    
    
    # Fast path: If we have a clear decision based on stamina/motivation, skip complex calculations
    if ctx.cultivate_detail.turn_info.remain_stamina <= 48:
        log.info(f"🏥 Fast path: Low stamina ({ctx.cultivate_detail.turn_info.remain_stamina}) - prioritizing rest")
        turn_operation.turn_operation_type = TurnOperationType.TURN_OPERATION_TYPE_REST
        return turn_operation
    


    # Cache screen image to avoid multiple conversions
    cached_screen = None
    if ctx.current_screen is not None:
        cached_screen = cv2.cvtColor(ctx.current_screen, cv2.COLOR_BGR2GRAY)

    attribute_result = get_training_basic_attribute_score(ctx, ctx.cultivate_detail.turn_info,
                                                          ctx.cultivate_detail.expect_attribute)
    support_card_result = get_training_support_card_score(ctx)
    support_card_event_result = get_support_card_event_score(ctx)
    training_level_result = get_training_level_score(ctx)

    attribute_result_max = np.max(attribute_result)
    attribute_result_min = np.min(attribute_result)
    if attribute_result_max != attribute_result_min:
        normalized_attribute_result = (attribute_result - attribute_result_min) / (
                attribute_result_max - attribute_result_min)
    else:
        normalized_attribute_result = [1, 1, 1, 1, 1]

    support_card_max = np.max(support_card_result)
    support_card_min = np.min(support_card_result)
    if support_card_max != support_card_min:
        normalized_support_card_result = (support_card_result - support_card_min) / (
                support_card_max - support_card_min)
    else:
        normalized_support_card_result = [1, 1, 1, 1, 1]

    training_level_max = np.max(training_level_result)
    training_level_min = np.min(training_level_result)
    if training_level_min != training_level_max:
        normalized_training_level_result = (training_level_result - training_level_min) / (
                training_level_max - training_level_min)
    else:
        normalized_training_level_result = [1, 1, 1, 1, 1]

    # Year 1 to before Year 2 training camp
    if ctx.cultivate_detail.turn_info.date <= 36:
        attr_weight = 0
        support_card_weight = 1
        training_level_weight = 0
    # During Year 2 training camp
    elif 36 < ctx.cultivate_detail.turn_info.date <= 40:
        attr_weight = 0
        support_card_weight = 1
        training_level_weight = 0
    # After Year 2 training camp to before Year 3
    elif 40 < ctx.cultivate_detail.turn_info.date <= 48:
        attr_weight = 0
        support_card_weight = 1
        training_level_weight = 0
    # Before Year 3 training camp
    elif 48 < ctx.cultivate_detail.turn_info.date <= 60:
        attr_weight = 0
        support_card_weight = 1
        training_level_weight = 0
    # During Year 3 training camp
    elif 60 < ctx.cultivate_detail.turn_info.date <= 64:
        attr_weight = 0
        support_card_weight = 1
        training_level_weight = 0
    # Year 3 to end
    elif 64 < ctx.cultivate_detail.turn_info.date <= 99:
        attr_weight = 0
        support_card_weight = 1
        training_level_weight = 0
    else:
        attr_weight = 0
        support_card_weight = 1
        training_level_weight = 0

    # attribute growth is very faulty as ocr kinda suck and training level weight is always 0 so only support card weight can be relied on
    training_score = []
    for i in range(5):
        training_score.append(normalized_attribute_result[i] * attr_weight + normalized_support_card_result[i] *
                              support_card_weight + normalized_training_level_result[i] * training_level_weight + 
                              support_card_event_result[i])
    # Set training score to 0 for weights of -1    
    extra_weight = [0, 0, 0, 0, 0]
    date = ctx.cultivate_detail.turn_info.date
    if len(ctx.cultivate_detail.extra_weight) == 3:
        if 0 < date <= 24:
            extra_weight = ctx.cultivate_detail.extra_weight[0]
        elif 24 < date <= 48:
            extra_weight = ctx.cultivate_detail.extra_weight[1]
        elif 48 < date:
            extra_weight = ctx.cultivate_detail.extra_weight[2]
    if -1 in extra_weight:
        log.debug("Setting training score to 0 for weights of -1")
        for i in range(5):
            if extra_weight[i] <= -1:
                training_score[i] = 0
    log.debug("Overall training score: " + str(training_score))

    # Can only participate in races after debut race success
    if ctx.cultivate_detail.debut_race_win:
        from module.umamusume.asset.race_data import get_races_for_period
        
        # Check for URA championship races first (automatic detection)
        ura_race_id = None
        if ctx.task.detail.scenario == ScenarioType.SCENARIO_TYPE_URA:
            # URA championship phases based on date
            date = ctx.cultivate_detail.turn_info.date
            if 73 <= date <= 75:  # URA Qualifier
                ura_race_id = 2381
            elif 76 <= date <= 78:  # URA Semi-final
                ura_race_id = 2382
            elif 79 <= date <= 99:  # URA Final
                ura_race_id = 2385  # or 2386, 2387 for different final types
            
            # Check if URA race button is actually available on screen (optimized)
            if ura_race_id and cached_screen is not None:
                ura_race_available = False
                
                if 73 <= date <= 75:  # Qualifier
                    ura_race_available = image_match(cached_screen, UI_CULTIVATE_URA_RACE_1).find_match
                elif 76 <= date <= 78:  # Semi-final
                    ura_race_available = image_match(cached_screen, UI_CULTIVATE_URA_RACE_2).find_match
                elif 79 <= date <= 99:  # Final
                    ura_race_available = image_match(cached_screen, UI_CULTIVATE_URA_RACE_3).find_match
                
                # If race button is not available, don't race
                if not ura_race_available:
                    ura_race_id = None  # Don't race if button not available
            elif ura_race_id and cached_screen is None:
                ura_race_id = None
        
        if ura_race_id:
            log.info(f"🏆 Detected URA championship race: {ura_race_id} at date {date}")
            # Check if we should rest/recreate instead of racing
            medic = False
            if ctx.cultivate_detail.turn_info.medic_room_available and ctx.cultivate_detail.turn_info.remain_stamina <= 85:
                medic = True

            trip = False
            if not ctx.cultivate_detail.turn_info.medic_room_available and (ctx.cultivate_detail.turn_info.date <= 36 and ctx.cultivate_detail.turn_info.motivation_level.value <= 3 and ctx.cultivate_detail.turn_info.remain_stamina < 90 and not support_card_max >= 2
                                                                        or 40 < ctx.cultivate_detail.turn_info.date <= 60 and ctx.cultivate_detail.turn_info.motivation_level.value <= 4 and ctx.cultivate_detail.turn_info.remain_stamina < 90
                                                                        or 64 < ctx.cultivate_detail.turn_info.date <= 99 and ctx.cultivate_detail.turn_info.motivation_level.value <= 4 and ctx.cultivate_detail.turn_info.remain_stamina < 90):
                try:
                    best_idx = training_score.index(np.max(training_score))
                    relevant = ctx.cultivate_detail.turn_info.training_info_list[best_idx].relevant_count
                except Exception:
                    relevant = 0
                if relevant >= 3:
                    log.info("No recreation as good training detected")
                    trip = False
                else:
                    trip = True

            rest = False
            if ctx.cultivate_detail.turn_info.remain_stamina <= 48:
                rest = True
            elif (
                    ctx.cultivate_detail.turn_info.date == 36 or ctx.cultivate_detail.turn_info.date == 60) and ctx.cultivate_detail.turn_info.remain_stamina < 65:
                rest = True

            # If we need rest/recreation, prioritize that over racing
            if rest:
                log.info(f"🏥 Low stamina ({ctx.cultivate_detail.turn_info.remain_stamina}) - prioritizing rest over URA race")
                turn_operation.turn_operation_type = TurnOperationType.TURN_OPERATION_TYPE_REST
                return turn_operation
            elif trip:
                log.info(f"🏖️ Low stamina/motivation - prioritizing trip over URA race")
                turn_operation.turn_operation_type = TurnOperationType.TURN_OPERATION_TYPE_TRIP
                return turn_operation
            elif medic:
                log.info(f"🏥 Low stamina - prioritizing medic over URA race")
                turn_operation.turn_operation_type = TurnOperationType.TURN_OPERATION_TYPE_MEDIC
                return turn_operation
            else:
                # Only race if we have enough stamina
                log.info(f"🏆 Proceeding with URA race - stamina: {ctx.cultivate_detail.turn_info.remain_stamina}")
                turn_operation.turn_operation_type = TurnOperationType.TURN_OPERATION_TYPE_RACE
                turn_operation.race_id = ura_race_id
                return turn_operation
        
        # Get races available for current time period
        available_races = _get_races_for_period_cached(ctx.cultivate_detail.turn_info.date)
        # Find intersection with user-configured extra races
        extra_race_this_turn = [race_id for race_id in ctx.cultivate_detail.extra_race_list 
                               if race_id in available_races]
        if len(extra_race_this_turn) != 0:
            turn_operation.turn_operation_type = TurnOperationType.TURN_OPERATION_TYPE_RACE
            turn_operation.race_id = extra_race_this_turn[0]
            return turn_operation

    medic = False
    if ctx.cultivate_detail.turn_info.medic_room_available and ctx.cultivate_detail.turn_info.remain_stamina <= 85:
        medic = True

    trip = False
    if not ctx.cultivate_detail.turn_info.medic_room_available and (ctx.cultivate_detail.turn_info.date <= 36 and ctx.cultivate_detail.turn_info.motivation_level.value < ctx.cultivate_detail.motivation_threshold_year1 and ctx.cultivate_detail.turn_info.remain_stamina < 90 and not support_card_max >= 3
                                                                    or 40 < ctx.cultivate_detail.turn_info.date <= 60 and ctx.cultivate_detail.turn_info.motivation_level.value < ctx.cultivate_detail.motivation_threshold_year2 and ctx.cultivate_detail.turn_info.remain_stamina < 90
                                                                    or 64 < ctx.cultivate_detail.turn_info.date <= 99 and ctx.cultivate_detail.turn_info.motivation_level.value < ctx.cultivate_detail.motivation_threshold_year3 and ctx.cultivate_detail.turn_info.remain_stamina < 90):
        try:
            best_idx = training_score.index(np.max(training_score))
            relevant = ctx.cultivate_detail.turn_info.training_info_list[best_idx].relevant_count
        except Exception:
            relevant = 0
        if relevant >= 3:
            log.info("No recreation as good training detected")
            trip = False
        else:
            trip = True
           

    rest = False
    if ctx.cultivate_detail.turn_info.remain_stamina <= 48:
        rest = True
    elif (
            ctx.cultivate_detail.turn_info.date == 36 or ctx.cultivate_detail.turn_info.date == 60) and ctx.cultivate_detail.turn_info.remain_stamina < 65:
        rest = True

    expect_operation_type = TurnOperationType.TURN_OPERATION_TYPE_UNKNOWN

    if medic and expect_operation_type is TurnOperationType.TURN_OPERATION_TYPE_UNKNOWN:
        expect_operation_type = TurnOperationType.TURN_OPERATION_TYPE_MEDIC

    if trip and expect_operation_type is TurnOperationType.TURN_OPERATION_TYPE_UNKNOWN:
        expect_operation_type = TurnOperationType.TURN_OPERATION_TYPE_TRIP

    if rest and expect_operation_type is TurnOperationType.TURN_OPERATION_TYPE_UNKNOWN:
        expect_operation_type = TurnOperationType.TURN_OPERATION_TYPE_REST

    if expect_operation_type is TurnOperationType.TURN_OPERATION_TYPE_UNKNOWN:
        date_num = ctx.cultivate_detail.turn_info.date
        if date_num in (59, 60): 
            rainbow = 0
            try:
                best_idx = training_score.index(np.max(training_score))
                id_counts = {}
                for sc in ctx.cultivate_detail.turn_info.training_info_list[best_idx].support_card_info_list:
                    k = id(sc)
                    id_counts[k] = id_counts.get(k, 0) + 1
                rainbow = sum(1 for v in id_counts.values() if v >= 2)
            except Exception:
                rainbow = 0
            if rainbow < 2:
                log.info("Low rainbow count conserving energy for summer")
                if ctx.cultivate_detail.turn_info.remain_stamina < 60:
                    expect_operation_type = TurnOperationType.TURN_OPERATION_TYPE_REST
                else:
                    expect_operation_type = TurnOperationType.TURN_OPERATION_TYPE_TRAINING
                    turn_operation.training_type = TrainingType.TRAINING_TYPE_INTELLIGENCE

    if expect_operation_type is TurnOperationType.TURN_OPERATION_TYPE_UNKNOWN:
        expect_operation_type = TurnOperationType.TURN_OPERATION_TYPE_TRAINING
        try:
            relevant_counts = [ctx.cultivate_detail.turn_info.training_info_list[i].relevant_count for i in range(5)]
        except Exception:
            relevant_counts = [0, 0, 0, 0, 0]
        # log.info(f"relevant_counts = {relevant_counts}")
        if all(rc == 0 for rc in relevant_counts):
            log.info("no good training option. umamusume is a wit game")
            turn_operation.training_type = TrainingType.TRAINING_TYPE_INTELLIGENCE
        else:
            turn_operation.training_type = TrainingType(training_score.index(np.max(training_score)) + 1)

    if turn_operation.turn_operation_type != TurnOperationType.TURN_OPERATION_TYPE_UNKNOWN:
        turn_operation.turn_operation_type_replace = expect_operation_type
    else:
        turn_operation.turn_operation_type = expect_operation_type
    return turn_operation


def get_training_level_score(ctx: UmamusumeContext):
    expect_attribute = ctx.cultivate_detail.expect_attribute
    total_score = 2
    result = []
    for i in range(len(expect_attribute)):
        result.append(expect_attribute[i] / sum(expect_attribute) * total_score)
    log.debug("Score for each training facility: " + str(result))
    return result


def get_training_support_card_score(ctx: UmamusumeContext) -> list[float]:
    turn_info = ctx.cultivate_detail.turn_info
    result = []
    for i in range(len(turn_info.training_info_list)):
        score = 0
        for j in range(len(turn_info.training_info_list[i].support_card_info_list)):
            score += get_support_card_score(ctx, turn_info.training_info_list[i].support_card_info_list[j])
        result.append(score)
    log.debug("Support card score for each training: " + str(result))
    return result

def get_support_card_event_score(ctx: UmamusumeContext) -> list[float]:
    # Only valid for URA
    if ctx.task.detail.scenario != ScenarioType.SCENARIO_TYPE_URA:
        return [0, 0, 0, 0, 0]
    turn_info = ctx.cultivate_detail.turn_info
    result = []
    for i in range (len(turn_info.training_info_list)):
        has_event = False
        for j in range(len(turn_info.training_info_list[i].support_card_info_list)):
            if turn_info.training_info_list[i].support_card_info_list[j].has_event:
                has_event = True
                break
        if has_event:
            result.append(1*ctx.task.detail.scenario_config.ura_config.getSkillEventWeight(ctx.cultivate_detail.turn_info.date))
        else:
            result.append(0)
    log.debug("Event score for each training: " + str(result))
    return result


def get_training_basic_attribute_score(ctx: UmamusumeContext, turn_info: TurnInfo, expect_attribute: list[int]) -> list[float]:
    date = turn_info.date
    cultivate_expect_attribute = expect_attribute.copy()
    extra_weight = [0, 0, 0, 0, 0]
    if len(ctx.cultivate_detail.extra_weight) == 3:
        if 0 < date <= 24:
            extra_weight = ctx.cultivate_detail.extra_weight[0]
        elif 24 < date <= 48:
            extra_weight = ctx.cultivate_detail.extra_weight[1]
        elif 48 < date:
            extra_weight = ctx.cultivate_detail.extra_weight[2]
    log.debug("Extra weight for this turn: " + str(extra_weight))
    turn_expect_attribute = [0, 0, 0, 0, 0]
    ura_extra_attr = 50
    if date > 72:
        ura_extra_attr = 0
        date = 72
    for i in range(len(cultivate_expect_attribute)):
        turn_expect_attribute_item = (int((cultivate_expect_attribute[i] - ura_extra_attr) * (date / 72))
                                      ) + 120 * (1 - date / 72)
        turn_expect_attribute_item = (1 + extra_weight[i]) * turn_expect_attribute_item
        if turn_expect_attribute_item > cultivate_expect_attribute[i]:
            turn_expect_attribute_item = cultivate_expect_attribute[i]
        turn_expect_attribute[i] = turn_expect_attribute_item if turn_expect_attribute_item > 0 else 1
    turn_uma_attr = [turn_info.uma_attribute.speed, turn_info.uma_attribute.stamina, turn_info.uma_attribute.power,
              turn_info.uma_attribute.will, turn_info.uma_attribute.intelligence]
    result = []
    expect_attribute_all_complete = all(x >= y for x, y in zip(turn_uma_attr, cultivate_expect_attribute))
    if expect_attribute_all_complete:
        log.debug("Training target attributes achieved")
        for i in range(len(turn_info.training_info_list)):
            incr = [turn_info.training_info_list[i].speed_incr, turn_info.training_info_list[i].stamina_incr,
                    turn_info.training_info_list[i].power_incr, turn_info.training_info_list[i].will_incr,
                    turn_info.training_info_list[i].intelligence_incr]
            rating_incr = 0
            for j in range(len(incr)):
                if incr[j] != 0:
                    rating_incr += incr[j]
            result.append(rating_incr)
    else:
        for i in range(len(turn_info.training_info_list)):
            incr = [turn_info.training_info_list[i].speed_incr, turn_info.training_info_list[i].stamina_incr,
                    turn_info.training_info_list[i].power_incr, turn_info.training_info_list[i].will_incr,
                    turn_info.training_info_list[i].intelligence_incr]
            rating_incr = 0
            for j in range(len(incr)):
                if incr[j] != 0 and turn_uma_attr[j] <= cultivate_expect_attribute[j]:
                    attr_difference = turn_expect_attribute[j] - turn_uma_attr[j]
                    # rating_incr += get_basic_status_score(incr[j] + turn_uma_attr[j]) - get_basic_status_score(turn_uma_attr[j])
                    if j == 3:
                        rating_incr += incr[j]
                    else:
                        if attr_difference >= incr[j]:
                            rating_incr += incr[j]
                        else:
                            if attr_difference < 0:
                                attr_difference = 0
                            rating_incr += attr_difference
                            overflow_incr = incr[j]-attr_difference
                            if cultivate_expect_attribute[j] - turn_expect_attribute[j] > overflow_incr:
                                rating_incr += 0.25 * overflow_incr
                            else:
                                rating_incr += 0.25 * (cultivate_expect_attribute[j] - turn_expect_attribute[j])
            # rating_incr += turn_info.training_info_list[i].skill_point_incr * 1.45
            result.append(rating_incr * (1 + extra_weight[i]))
        log.debug("Raw attribute growth score for each training: " + str(result))
        log.debug("Expected attributes for this turn: " + str(turn_expect_attribute))
        target_percent = [0, 0, 0, 0, 0]
        for i in range(len(turn_uma_attr)):
            target_percent[i] = turn_uma_attr[i] / turn_expect_attribute[i]
        avg = sum(target_percent) / len(target_percent)
        for i in range(len(result)):
            result[i] = result[i] * (1 - (target_percent[i] - avg))
    log.debug("Attribute growth score for each training: " + str(result))
    return result


status_score = [0.66, 1.15, 1.71, 2.25, 2.7, 2.96, 3.2, 3.45, 4.01, 4.26, 5.36, 6.70]


def get_basic_status_score(status: int) -> float:
    result = 0
    for i in range(13):
        if status > 0:
            status -= 100
            result += status_score[i] * 100
        else:
            if i - 1 > 11:
                log.debug("Recognition error")
                return 0
            result += status * status_score[i - 1]
            break
    return result


if __name__ == '__main__':
    print(str(get_basic_status_score(1169)))