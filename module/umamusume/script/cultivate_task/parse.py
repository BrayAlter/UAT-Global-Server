import re
from difflib import SequenceMatcher

import cv2
import numpy
import time

from bot.base.task import TaskStatus, EndTaskReason
from bot.recog.image_matcher import image_match, compare_color_equal
from bot.recog.ocr import ocr_line, find_similar_text
from module.umamusume.asset.race_data import RACE_LIST
from module.umamusume.context import UmamusumeContext
from module.umamusume.types import SupportCardInfo
from module.umamusume.asset import *
from module.umamusume.define import *
import bot.base.log as logger
from module.umamusume.script.cultivate_task.const import DATE_YEAR, DATE_MONTH

log = logger.get_logger(__name__)


def normalize_skill_name(skill_name: str) -> str:
    """Normalize skill name by removing spaces and converting to lowercase for better matching"""
    return skill_name.replace(" ", "").lower()


def find_similar_skill_name(target_text: str, ref_text_list: list[str], threshold: float = 0.7) -> str:
    """Enhanced skill name matching that handles spacing variations"""
    result = ""
    best_ratio = 0
    
    # Normalize target text
    normalized_target = normalize_skill_name(target_text)
    
    for ref_text in ref_text_list:
        # Try exact match first
        if target_text == ref_text:
            return ref_text
        
        # Try normalized match
        normalized_ref = normalize_skill_name(ref_text)
        if normalized_target == normalized_ref:
            return ref_text
        
        # Try similarity matching
        s = SequenceMatcher(None, target_text, ref_text)
        ratio = s.ratio()
        
        # Also try normalized similarity
        s_normalized = SequenceMatcher(None, normalized_target, normalized_ref)
        ratio_normalized = s_normalized.ratio()
        
        # Use the better ratio
        best_ratio_for_this = max(ratio, ratio_normalized)
        
        if best_ratio_for_this > threshold and best_ratio_for_this > best_ratio:
            result = ref_text
            best_ratio = best_ratio_for_this
    
    return result


def parse_date(img, ctx: UmamusumeContext) -> int:
    # Youth Cup and URA UI positions are different
    if ctx.cultivate_detail.scenario.scenario_type() == ScenarioType.SCENARIO_TYPE_AOHARUHAI:
        sub_img_date = ctx.cultivate_detail.scenario.get_date_img(img)
        sub_img_date = cv2.copyMakeBorder(sub_img_date, 20, 20, 20, 20, cv2.BORDER_CONSTANT, None, (255, 255, 255))
        date_text = ocr_line(sub_img_date)
        
        # Debug: Log the extracted date text
        log.info(f"🔍 Extracted date text: '{date_text}'")
        
        year_text = ""
        for text in DATE_YEAR:
            if date_text.__contains__(text):
                year_text = text

        if year_text == "":
            year_text = find_similar_text(date_text, DATE_YEAR)
            log.info(f"🔍 Similar text found: '{year_text}'")

        if year_text == DATE_YEAR[3]:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            if image_match(img, URA_DATE_1).find_match:
                return 97
            elif image_match(img, URA_DATE_2).find_match:
                return 98
            else:
                return 99

        if year_text == "":
            log.warning(f"❌ No year text found in date: '{date_text}'")
            return -1

        month_text = ""
        for text in DATE_MONTH:
            if date_text.__contains__(text):
                month_text = text
        if month_text == "":
            month_text = find_similar_text(date_text, DATE_MONTH)

        if month_text != DATE_MONTH[0]:
            date_id = DATE_YEAR.index(year_text) * 24 + DATE_MONTH.index(month_text)
        else:
            sub_img_turn_to_race = ctx.cultivate_detail.scenario.get_turn_to_race_img(img)
            sub_img_turn_to_race = cv2.copyMakeBorder(sub_img_turn_to_race, 20, 20, 20, 20, cv2.BORDER_CONSTANT, None,
                                                      (255, 255, 255))
            turn_to_race_text = ocr_line(sub_img_turn_to_race)
            if turn_to_race_text == "Race Day":
                log.debug("Debut race day")
                return 12
            turn_to_race_text = re.sub("\\D", "", turn_to_race_text)
            if turn_to_race_text == '':
                log.warning("Debut race date recognition exception")
                return 12 - (len(ctx.cultivate_detail.turn_info_history) + 1)
            date_id = 12 - int(turn_to_race_text)
            if date_id < 1:
                log.warning("Debut race date recognition exception")
                return 12 - (len(ctx.cultivate_detail.turn_info_history) + 1)
        return date_id
    else:
        # URA scenario date parsing
        sub_img_date = ctx.cultivate_detail.scenario.get_date_img(img)
        sub_img_date = cv2.copyMakeBorder(sub_img_date, 20, 20, 20, 20, cv2.BORDER_CONSTANT, None, (255, 255, 255))
        date_text = ocr_line(sub_img_date)
        
        # Debug: Log the extracted date text for URA
        log.info(f"🔍 URA Extracted date text: '{date_text}'")
        
        # Special handling for "Finale Season" in URA championship
        if "Finale Season" in date_text or "Finale" in date_text:
            log.info("🏆 URA Finale Season detected - checking championship phase")
            
            # Check specific coordinates for URA championship phase text
            championship_phase_img = img[74:100, 250:575]  # x: 250, y: 74, width: 325, height: 26
            championship_phase_img = cv2.copyMakeBorder(championship_phase_img, 20, 20, 20, 20, cv2.BORDER_CONSTANT, None, (255, 255, 255))
            championship_phase_text = ocr_line(championship_phase_img)
            log.info(f"🔍 URA Championship phase text: '{championship_phase_text}'")
            
            # Determine URA championship phase based on OCR text
            if "URA Finale Qualifier" in championship_phase_text or "Qualifier" in championship_phase_text:
                log.info("🏆 URA Finals Qualifier detected")
                return 73  # Qualifier date
            elif "URA Finale Semifinal" in championship_phase_text or "Semifinal" in championship_phase_text:
                log.info("🏆 URA Finals Semifinal detected")
                return 76  # Semi-final date
            elif "URA Finale Finals" in championship_phase_text or "Finals" in championship_phase_text:
                log.info("🏆 URA Finals Final detected")
                return 79  # Final date
            else:
                log.warning(f"❌ Unknown URA championship phase: '{championship_phase_text}'")
                # Fallback to qualifier if unknown
                return 73
        
        year_text = ""
        for text in DATE_YEAR:
            if date_text.__contains__(text):
                year_text = text

        if year_text == "":
            year_text = find_similar_text(date_text, DATE_YEAR)
            log.info(f"🔍 URA Similar text found: '{year_text}'")

        if year_text == DATE_YEAR[3]:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            if image_match(img, URA_DATE_1).find_match:
                return 97
            elif image_match(img, URA_DATE_2).find_match:
                return 98
            else:
                return 99

        if year_text == "":
            log.warning(f"❌ URA No year text found in date: '{date_text}'")
            return -1

        month_text = ""
        for text in DATE_MONTH:
            if date_text.__contains__(text):
                month_text = text
        if month_text == "":
            month_text = find_similar_text(date_text, DATE_MONTH)

        if month_text != DATE_MONTH[0]:
            date_id = DATE_YEAR.index(year_text) * 24 + DATE_MONTH.index(month_text)
        else:
            sub_img_turn_to_race = ctx.cultivate_detail.scenario.get_turn_to_race_img(img)
            sub_img_turn_to_race = cv2.copyMakeBorder(sub_img_turn_to_race, 20, 20, 20, 20, cv2.BORDER_CONSTANT, None,
                                                      (255, 255, 255))
            turn_to_race_text = ocr_line(sub_img_turn_to_race)
            if turn_to_race_text == "Race Day":
                log.debug("URA Debut race day")
                return 12
            turn_to_race_text = re.sub("\\D", "", turn_to_race_text)
            if turn_to_race_text == '':
                log.warning("URA Debut race date recognition exception")
                return 12 - (len(ctx.cultivate_detail.turn_info_history) + 1)
            date_id = 12 - int(turn_to_race_text)
            if date_id < 1:
                log.warning("URA Debut race date recognition exception")
                return 12 - (len(ctx.cultivate_detail.turn_info_history) + 1)
        return date_id


def parse_cultivate_main_menu(ctx: UmamusumeContext, img):
    parse_train_main_menu_operations_availability(ctx, img)
    parse_umamusume_remain_stamina_value(ctx, img)
    parse_umamusume_basic_ability_value(ctx, img)
    parse_motivation(ctx, img)
    parse_debut_race(ctx, img)
    ctx.cultivate_detail.turn_info.parse_main_menu_finish = True


def parse_debut_race(ctx: UmamusumeContext, img):
    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    if image_match(img, REF_DEBUT_RACE_NOT_WIN).find_match:
        ctx.cultivate_detail.debut_race_win = False
    else:
        ctx.cultivate_detail.debut_race_win = True


def parse_motivation(ctx: UmamusumeContext, img):
    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    for i in range(len(MOTIVATION_LIST)):
        result = image_match(img, MOTIVATION_LIST[i])
        if result.find_match:
            ctx.cultivate_detail.turn_info.motivation_level = MotivationLevel(i + 1)
            return


def parse_umamusume_basic_ability_value(ctx: UmamusumeContext, img):
    sub_img_speed = img[855:885, 70:139]
    sub_img_speed = cv2.copyMakeBorder(sub_img_speed, 20, 20, 20, 20, cv2.BORDER_CONSTANT, None, (255, 255, 255))
    speed_text = ocr_line(sub_img_speed)

    sub_img_stamina = img[855:885, 183:251]
    sub_img_stamina = cv2.copyMakeBorder(sub_img_stamina, 20, 20, 20, 20, cv2.BORDER_CONSTANT, None, (255, 255, 255))
    stamina_text = ocr_line(sub_img_stamina)

    sub_img_power = img[855:885, 289:364]
    sub_img_power = cv2.copyMakeBorder(sub_img_power, 20, 20, 20, 20, cv2.BORDER_CONSTANT, None, (255, 255, 255))
    power_text = ocr_line(sub_img_power)

    sub_img_will = img[855:885, 409:476]
    sub_img_will = cv2.copyMakeBorder(sub_img_will, 20, 20, 20, 20, cv2.BORDER_CONSTANT, None, (255, 255, 255))
    will_text = ocr_line(sub_img_will)

    sub_img_intelligence = img[855:885, 521:588]
    sub_img_intelligence = cv2.copyMakeBorder(sub_img_intelligence, 20, 20, 20, 20, cv2.BORDER_CONSTANT, None,
                                              (255, 255, 255))
    intelligence_text = ocr_line(sub_img_intelligence)

    sub_img_skill = img[855:902, 602:690]
    sub_img_skill = cv2.copyMakeBorder(sub_img_skill, 20, 20, 20, 20, cv2.BORDER_CONSTANT, None,
                                       (255, 255, 255))
    skill_point_text = ocr_line(sub_img_skill)

    ctx.cultivate_detail.turn_info.uma_attribute.speed = trans_attribute_value(speed_text, ctx,
                                                                               TrainingType.TRAINING_TYPE_SPEED)
    ctx.cultivate_detail.turn_info.uma_attribute.stamina = trans_attribute_value(stamina_text, ctx,
                                                                                 TrainingType.TRAINING_TYPE_STAMINA)
    ctx.cultivate_detail.turn_info.uma_attribute.power = trans_attribute_value(power_text, ctx,
                                                                               TrainingType.TRAINING_TYPE_POWER)
    ctx.cultivate_detail.turn_info.uma_attribute.will = trans_attribute_value(will_text, ctx,
                                                                              TrainingType.TRAINING_TYPE_WILL)
    ctx.cultivate_detail.turn_info.uma_attribute.intelligence = trans_attribute_value(intelligence_text, ctx,
                                                                                      TrainingType.TRAINING_TYPE_INTELLIGENCE)
    ctx.cultivate_detail.turn_info.uma_attribute.skill_point = trans_attribute_value(skill_point_text, ctx)


def trans_attribute_value(text: str, ctx: UmamusumeContext,
                          train_type: TrainingType = TrainingType.TRAINING_TYPE_UNKNOWN) -> int:
    text = re.sub("\\D", "", text)
    if text == "":
        prev_turn_idx = len(ctx.cultivate_detail.turn_info_history)
        if prev_turn_idx != 0:
            history = ctx.cultivate_detail.turn_info_history[prev_turn_idx - 1]
            log.warning("Image recognition error, using previous turn value")
            if train_type.value == 1:
                return history.uma_attribute.speed
            elif train_type.value == 2:
                return history.uma_attribute.stamina
            elif train_type.value == 3:
                return history.uma_attribute.power
            elif train_type.value == 4:
                return history.uma_attribute.will
            elif train_type.value == 5:
                return history.uma_attribute.intelligence
            else:
                return 0
        else:
            return 100
    else:
        return int(text)


def parse_umamusume_remain_stamina_value(ctx: UmamusumeContext, img):
    sub_img_remain_stamina = img[160:161, 229:505]
    stamina_counter = 0
    for c in sub_img_remain_stamina[0]:
        if not compare_color_equal(c, [117, 117, 117], tolerance=20):
            stamina_counter += 1
    remain_stamina = int(stamina_counter / 276 * 100)
    ctx.cultivate_detail.turn_info.remain_stamina = remain_stamina


def parse_train_main_menu_operations_availability(ctx: UmamusumeContext, img):
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    # Availability
    btn_rest_check_point = img[980, 60]
    btn_train_check_point = img[990, 250]
    btn_skill_check_point = img[980, 550]
    btn_medic_room_check_point = img[1125, 105]
    btn_trip_check_point = img[1115, 305]
    btn_race_check_point = img[1130, 490]

    # During summer camp
    if ctx.cultivate_detail.turn_info and ctx.cultivate_detail.turn_info.date and (36 < ctx.cultivate_detail.turn_info.date <= 40 or 60 < ctx.cultivate_detail.turn_info.date <= 64):
        btn_medic_room_check_point = img[1130, 200]
        btn_rest_check_point = img[990, 190]
        btn_race_check_point = img[1125, 395]

    rest_available = btn_rest_check_point[0] > 200
    train_available = btn_train_check_point[0] > 200
    skill_available = btn_skill_check_point[0] > 200
    if btn_medic_room_check_point[0] > 200 and btn_medic_room_check_point[1] > 200 and btn_medic_room_check_point[
        2] > 200:
        medic_room_available = True
    else:
        medic_room_available = False
    trip_available = btn_trip_check_point[0] > 200
    race_available = btn_race_check_point[0] > 200

    ctx.cultivate_detail.turn_info.race_available = race_available
    ctx.cultivate_detail.turn_info.medic_room_available = medic_room_available


def parse_training_support_card(ctx: UmamusumeContext, img, train_type: TrainingType):
    support_card_info_list = ctx.cultivate_detail.scenario.parse_training_support_card(img)
    ctx.cultivate_detail.turn_info.training_info_list[train_type.value - 1].support_card_info_list = support_card_info_list

def parse_train_type(ctx: UmamusumeContext, img) -> TrainingType:
    train_label = cv2.cvtColor(img[210:275, 0:210], cv2.COLOR_RGB2GRAY)
    train_type = TrainingType.TRAINING_TYPE_UNKNOWN
    if image_match(train_label, REF_TRAINING_TYPE_SPEED).find_match:
        train_type = TrainingType.TRAINING_TYPE_SPEED
    elif image_match(train_label, REF_TRAINING_TYPE_STAMINA).find_match:
        train_type = TrainingType.TRAINING_TYPE_STAMINA
    elif image_match(train_label, REF_TRAINING_TYPE_POWER).find_match:
        train_type = TrainingType.TRAINING_TYPE_POWER
    elif image_match(train_label, REF_TRAINING_TYPE_WILL).find_match:
        train_type = TrainingType.TRAINING_TYPE_WILL
    elif image_match(train_label, REF_TRAINING_TYPE_INTELLIGENCE).find_match:
        train_type = TrainingType.TRAINING_TYPE_INTELLIGENCE
    return train_type


def parse_training_result(ctx: UmamusumeContext, img, train_type: TrainingType):
    train_incr = ctx.cultivate_detail.scenario.parse_training_result(img)
    log.debug(train_incr)
    
    ctx.cultivate_detail.turn_info.training_info_list[train_type.value - 1].speed_incr = train_incr[0]
    ctx.cultivate_detail.turn_info.training_info_list[train_type.value - 1].stamina_incr = train_incr[1]
    ctx.cultivate_detail.turn_info.training_info_list[train_type.value - 1].power_incr = train_incr[2]
    ctx.cultivate_detail.turn_info.training_info_list[train_type.value - 1].will_incr = train_incr[3]
    ctx.cultivate_detail.turn_info.training_info_list[train_type.value - 1].intelligence_incr = train_incr[4]
    ctx.cultivate_detail.turn_info.training_info_list[train_type.value - 1].skill_point_incr = train_incr[5]


def find_support_card(ctx: UmamusumeContext, img):
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    while True:
        match_result = image_match(img, REF_FOLLOW_SUPPORT_CARD_DETECT_LABEL)
        if match_result.find_match:
            pos = match_result.matched_area
            support_card_info = img[pos[0][1] - 125:pos[1][1] + 10, pos[0][0] - 140: pos[1][0] + 380]
            img[match_result.matched_area[0][1]:match_result.matched_area[1][1],
            match_result.matched_area[0][0]:match_result.matched_area[1][0]] = 0
            support_card_level_img = support_card_info[125:145, 68:111]
            support_card_name_img = support_card_info[63:94, 132:439]

            support_card_level_img = cv2.copyMakeBorder(support_card_level_img, 20, 20, 20, 20, cv2.BORDER_CONSTANT,
                                                        None,
                                                        (255, 255, 255))
            support_card_name_img = cv2.copyMakeBorder(support_card_name_img, 20, 20, 20, 20, cv2.BORDER_CONSTANT, None,
                                                       (255, 255, 255))
            support_card_level_text = ocr_line(support_card_level_img)
            if support_card_level_text == "":
                continue
            support_card_level = int(re.sub("\\D", "", support_card_level_text))
            if support_card_level < ctx.cultivate_detail.follow_support_card_level:
                continue
            support_card_text = ocr_line(support_card_name_img)
            s = SequenceMatcher(None, support_card_text, ctx.cultivate_detail.follow_support_card_name)
            if s.ratio() > 0.7:
                ctx.ctrl.click(match_result.center_point[0], match_result.center_point[1] - 75,
                               "选择支援卡：" + ctx.cultivate_detail.follow_support_card_name + "<" + str(
                                   support_card_level) + ">")
                return True
        else:
            break
    return False


# 111 237 480 283
def parse_cultivate_event(ctx: UmamusumeContext, img) -> tuple[str, list[int]]:
    event_name_img = img[237:283, 111:480]
    event_name = ocr_line(event_name_img)
    event_selector_list = []
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Method 1: Original Chinese server template matching
    img_temp = img_gray.copy()
    while True:
        match_result = image_match(img_temp, REF_SELECTOR)
        if match_result.find_match:
            event_selector_list.append(match_result.center_point)
            img_temp[match_result.matched_area[0][1]:match_result.matched_area[1][1],
                     match_result.matched_area[0][0]:match_result.matched_area[1][0]] = 0
        else:
            break
    
    # Method 2: Try individual dialogue templates (dialogue1, dialogue2, dialogue3)
    if len(event_selector_list) == 0:
        log.warning(f"REF_SELECTOR template failed for event '{event_name}', trying individual dialogue templates")
        
        # Try each dialogue template
        from module.umamusume.asset.template import Template, UMAMUSUME_REF_TEMPLATE_PATH
        dialogue_templates = []
        
        try:
            dialogue_templates = [
                Template("dialogue1", UMAMUSUME_REF_TEMPLATE_PATH),
                Template("dialogue2", UMAMUSUME_REF_TEMPLATE_PATH),
                Template("dialogue3", UMAMUSUME_REF_TEMPLATE_PATH)
            ]
        except:
            log.warning("Could not load dialogue templates")
        
        # Try matching each dialogue template
        for template in dialogue_templates:
            try:
                img_temp = img_gray.copy()
                while True:
                    match_result = image_match(img_temp, template)
                    if match_result.find_match:
                        event_selector_list.append(match_result.center_point)
                        img_temp[match_result.matched_area[0][1]:match_result.matched_area[1][1],
                                 match_result.matched_area[0][0]:match_result.matched_area[1][0]] = 0
                    else:
                        break
            except:
                continue
        
        if len(event_selector_list) > 0:
            log.info(f"Found {len(event_selector_list)} dialogue options using individual templates")
        else:
            log.warning("Individual dialogue templates also failed, using fallback position")
            # Last resort fallback
            event_selector_list = [(360, 800)]
    
    event_selector_list.sort(key=lambda x: x[1])
    return event_name, event_selector_list


def convert_race_name_to_ingame_format(race_id: int) -> str:
    """Convert CSV race data to in-game display format using only available data"""
    try:
        import csv
        # Read race data from CSV
        with open('resource/umamusume/data/race.csv', 'r', encoding="utf-8") as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) >= 9 and int(row[1]) == race_id:
                    # CSV format: time_period,race_id,period_name,race_name,grade,venue,surface,distance,direction,condition,going
                    venue = row[5] if len(row) > 5 and row[5] else ""  # Hanshin
                    surface = row[6] if len(row) > 6 and row[6] else ""  # Turf
                    distance = row[7] if len(row) > 7 and row[7] else ""  # 2200
                    direction = row[8] if len(row) > 8 and row[8] else ""  # Right
                    going = row[10] if len(row) > 10 and row[10] else ""  # Medium
                    
                    # Build format using only available data
                    parts = []
                    
                    # Add venue + surface + distance if available
                    if venue and surface and distance:
                        # Add "m" after distance numbers (4 digits only)
                        if distance.isdigit() and len(distance) == 4:
                            parts.append(f"{venue} {surface} {distance}m")
                        else:
                            parts.append(f"{venue} {surface} {distance}")
                    elif venue and surface:
                        parts.append(f"{venue} {surface}")
                    elif venue:
                        parts.append(venue)
                    
                    # Add going in parentheses if available
                    if going:
                        if going.lower() == "medium":
                            parts.append("(Med)")
                        elif going.lower() == "good":
                            parts.append("(Good)")
                        elif going.lower() == "yielding":
                            parts.append("(Yielding)")
                        elif going.lower() == "soft":
                            parts.append("(Soft)")
                        elif going.lower() == "heavy":
                            parts.append("(Heavy)")
                        else:
                            parts.append(f"({going})")
                    
                    # Add direction if available
                    if direction:
                        parts.append(direction)
                    
                    # Join all available parts
                    in_game_format = " ".join(parts)
                    
                    return in_game_format
    except Exception as e:
        log.debug(f"Failed to convert race name for ID {race_id}: {e}")
    
    # Fallback to original name if conversion fails
    return RACE_LIST[race_id][1] if race_id < len(RACE_LIST) else ""


def find_race(ctx: UmamusumeContext, img, race_id: int = 0) -> bool:
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    target_race_template = RACE_LIST[race_id][2]
    img_height, img_width = img.shape
    
    # Debug: Log race template info
    if target_race_template is not None:
        log.info(f"🔍 Looking for race ID {race_id}: {RACE_LIST[race_id][1]}")
        log.info(f"🔍 Template exists: {target_race_template is not None}")
    else:
        log.warning(f"❌ No template found for race ID {race_id}")
        return False
    
    while True:
        match_result = image_match(img, REF_RACE_LIST_DETECT_LABEL)
        if match_result.find_match:
            pos = match_result.matched_area
            pos_center = match_result.center_point
            if 685 < pos_center[1] < 1110:
                # Calculate safe bounds for race name extraction
                y1 = max(0, pos[0][1] - 60)
                y2 = min(img_height, pos[1][1] + 25)
                x1 = max(0, pos[0][0] - 250)
                x2 = min(img_width, pos[1][0] + 400)
                
                # Extract race name region with bounds checking
                race_name_img = img[y1:y2, x1:x2]
                
                # Check if extracted region is large enough for template matching
                if target_race_template is not None and race_name_img.shape[0] > 0 and race_name_img.shape[1] > 0:
                    template_img = target_race_template.template_image
                    if (template_img is not None and 
                        race_name_img.shape[0] >= template_img.shape[0] and 
                        race_name_img.shape[1] >= template_img.shape[1]):
                        
                        # STEP 1: Try template matching first
                        template_match = image_match(race_name_img, target_race_template)
                        template_success = template_match.find_match
                        
                        if template_success:
                            log.info(f"✅ Template match successful for race {race_id}")
                        else:
                            log.debug(f"❌ Template match failed for race {race_id}")
                            
                            # Try with preprocessed template (wiki image optimization)
                            try:
                                preprocessed_template = preprocess_wiki_image_for_ingame_matching(template_img.copy())
                                # Create a temporary template with preprocessed image
                                from bot.base.resource import Template
                                temp_template = Template(f"preprocessed_{race_id}", UMAMUSUME_RACE_TEMPLATE_PATH)
                                temp_template.template_image = preprocessed_template
                                
                                # Try without threshold parameter first
                                preprocessed_match = image_match(race_name_img, temp_template)
                                if preprocessed_match.find_match:
                                    template_success = True
                                    log.info(f"✅ Preprocessed template match successful for race {race_id}")
                                else:
                                    log.debug(f"❌ Preprocessed template match also failed for race {race_id}")
                            except Exception as e:
                                log.debug(f"Preprocessed template matching failed: {e}")
                        
                        # STEP 2: Try OCR to get the actual race name from screen
                        ocr_race_id = None
                        try:
                            race_name_text = ocr_line(race_name_img)
                            log.info(f"🔍 OCR extracted text: '{race_name_text}'")
                            
                            # Try to find which race ID this OCR text corresponds to
                            # Search through all races to find a match
                            for search_race_id in range(len(RACE_LIST)):
                                if search_race_id == race_id:  # Skip our target race
                                    continue
                                    
                                target_race_name = RACE_LIST[search_race_id][1]
                                in_game_race_name = convert_race_name_to_ingame_format(search_race_id)
                                
                                # Check if OCR text matches this race
                                csv_match = target_race_name.lower() in race_name_text.lower() or race_name_text.lower() in target_race_name.lower()
                                ingame_match = in_game_race_name.lower() in race_name_text.lower() or race_name_text.lower() in in_game_race_name.lower()
                                
                                if csv_match or ingame_match:
                                    ocr_race_id = search_race_id
                                    log.info(f"🔍 OCR identified race ID: {ocr_race_id} ({RACE_LIST[ocr_race_id][1]})")
                                    break
                                    
                        except Exception as e:
                            log.debug(f"OCR failed: {e}")
                        
                        # STEP 3: DUAL VERIFICATION - Both template and OCR must agree
                        if template_success and ocr_race_id is not None:
                            if ocr_race_id == race_id:
                                # Both methods agree on the same race ID - this is the correct race!
                                log.info(f"✅ DUAL VERIFICATION SUCCESS: Template and OCR both identify race ID {race_id}")
                                ctx.ctrl.click(match_result.center_point[0], match_result.center_point[1],
                                               "Select race (verified): " + str(RACE_LIST[race_id][1]))
                                return True
                            else:
                                # Template and OCR disagree - this is NOT the correct race
                                log.warning(f"⚠️ DUAL VERIFICATION FAILED: Template suggests race {race_id}, but OCR suggests race {ocr_race_id}")
                                log.info(f"🔄 Continuing to search for the correct race...")
                                # Mark this area as searched and continue
                                img[match_result.matched_area[0][1]:match_result.matched_area[1][1],
                                    match_result.matched_area[0][0]:match_result.matched_area[1][0]] = 0
                                continue
                        elif template_success and ocr_race_id is None:
                            # Template succeeded but OCR failed - use template only as fallback
                            log.warning(f"⚠️ OCR failed, but template succeeded. Using template-only verification for race {race_id}")
                            ctx.ctrl.click(match_result.center_point[0], match_result.center_point[1],
                                           "Select race (template-only): " + str(RACE_LIST[race_id][1]))
                            return True
                        else:
                            # Both methods failed - continue searching
                            log.debug(f"❌ Both template and OCR failed for race {race_id}, continuing search...")
                            # Mark this area as searched and continue
                            img[match_result.matched_area[0][1]:match_result.matched_area[1][1],
                                match_result.matched_area[0][0]:match_result.matched_area[1][0]] = 0
                            continue
                    else:
                        log.debug(f"Template too large for extracted region: template {None if template_img is None else template_img.shape}, region {race_name_img.shape}")
            img[match_result.matched_area[0][1]:match_result.matched_area[1][1],
            match_result.matched_area[0][0]:match_result.matched_area[1][0]] = 0
        else:
            break
    return False


def find_skill(ctx: UmamusumeContext, img, skill: list[str], learn_any_skill: bool) -> bool:
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    find = False
    while True:
        match_result = image_match(img, REF_SKILL_LIST_DETECT_LABEL)
        if match_result.find_match:
            pos = match_result.matched_area
            pos_center = match_result.center_point
            if 460 < pos_center[0] < 560 and 450 < pos_center[1] < 1050:
                skill_info_img = img[pos[0][1] - 65:pos[1][1] + 75, pos[0][0] - 470: pos[1][0] + 150]
                if not image_match(skill_info_img, REF_SKILL_LEARNED).find_match:
                    skill_name_img = skill_info_img[10: 47, 100: 445]
                    text = ocr_line(skill_name_img)
                    result = find_similar_skill_name(text, skill, 0.7)
                    # print(text + "->" + result)
                    if result != "" or learn_any_skill:
                        tmp_img = ctx.ctrl.get_screen()
                        pt_text = re.sub("\\D", "", ocr_line(tmp_img[400: 440, 490: 665]))
                        skill_pt_cost_text = re.sub("\\D", "", ocr_line(skill_info_img[69: 99, 525: 588]))
                        
                        # Handle empty cost (Global Server UI compatibility) - same as get_skill_list()
                        if not skill_pt_cost_text or skill_pt_cost_text == '':
                            # Try alternative cost extraction regions for Global Server
                            alt_cost_regions = [
                                skill_info_img[65: 95, 520: 595],  # Slightly adjusted region
                                skill_info_img[70: 100, 515: 590], # Different adjustment
                                skill_info_img[60: 90, 530: 600],  # Wider region
                            ]
                            
                            for i, alt_region in enumerate(alt_cost_regions):
                                try:
                                    alt_cost_text = ocr_line(alt_region)
                                    alt_cost = re.sub("\\D", "", alt_cost_text)
                                    if alt_cost and alt_cost != '':
                                        skill_pt_cost_text = alt_cost
                                        log.debug(f"find_skill - Found skill cost using alternative region {i+1}: '{alt_cost}' for '{text}'")
                                        break
                                except:
                                    continue
                            
                            # Final fallback if all regions fail
                            if not skill_pt_cost_text or skill_pt_cost_text == '':
                                log.debug(f"find_skill - Could not parse skill cost for '{text}', defaulting to 1")
                                skill_pt_cost_text = '1'  # Default cost to avoid crashes
                        
                        # Debug: Log point and cost extraction
                        log.debug(f"🔍 find_skill - Available points: '{pt_text}', Skill cost: '{skill_pt_cost_text}'")
                        
                        if pt_text != "" and skill_pt_cost_text != "":
                            pt = int(pt_text)
                            skill_pt_cost = int(skill_pt_cost_text)
                            log.debug(f"🔍 find_skill - Points: {pt}, Cost: {skill_pt_cost}, Can buy: {pt >= skill_pt_cost}")
                            
                            if pt >= skill_pt_cost:
                                log.info(f"✅ Buying skill '{text}' - Points: {pt}, Cost: {skill_pt_cost}")
                                ctx.ctrl.click(match_result.center_point[0] + 128, match_result.center_point[1],
                                               "Bonus Skills：" + text)
                                if result in skill:
                                    skill.remove(result)
                                ctx.cultivate_detail.learn_skill_selected = True
                                find = True
                            else:
                                log.debug(f"❌ Not enough points for '{text}' - Need {skill_pt_cost}, have {pt}")
                        else:
                            log.debug(f"❌ Failed to extract points/cost - Points: '{pt_text}', Cost: '{skill_pt_cost_text}'")

            img[match_result.matched_area[0][1]:match_result.matched_area[1][1],
            match_result.matched_area[0][0]:match_result.matched_area[1][0]] = 0

        else:
            break
    return find


def get_skill_list(img, skill: list[str], skill_blacklist: list[str]) -> list:
    origin_img = img
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    res = []
    while True:
        all_skill_scanned = True
        match_result = image_match(img, REF_SKILL_LIST_DETECT_LABEL)
        if match_result.find_match:
            all_skill_scanned = False
            pos = match_result.matched_area
            pos_center = match_result.center_point
            if 460 < pos_center[0] < 560 and 450 < pos_center[1] < 1050:
                skill_info_img = img[pos[0][1] - 65:pos[1][1] + 75, pos[0][0] - 470: pos[1][0] + 150]
                skill_info_cp = origin_img[pos[0][1] - 65:pos[1][1] + 75, pos[0][0] - 470: pos[1][0] + 150]

                skill_name_img = skill_info_img[10: 47, 100: 445]
                skill_cost_img = skill_info_img[69: 99, 525: 588]
                text = ocr_line(skill_name_img)
                cost_text = ocr_line(skill_cost_img)
                cost = re.sub("\\D", "", cost_text)
                
                # Debug: Log OCR text for skill names
                log.debug(f"🔍 OCR skill name: '{text}'")
                
                # Handle empty cost (Global Server UI compatibility)
                if not cost or cost == '':
                    # Try alternative cost extraction regions for Global Server
                    alt_cost_regions = [
                        skill_info_img[65: 95, 520: 595],  # Slightly adjusted region
                        skill_info_img[70: 100, 515: 590], # Different adjustment
                        skill_info_img[60: 90, 530: 600],  # Wider region
                    ]
                    
                    for i, alt_region in enumerate(alt_cost_regions):
                        try:
                            alt_cost_text = ocr_line(alt_region)
                            alt_cost = re.sub("\\D", "", alt_cost_text)
                            if alt_cost and alt_cost != '':
                                cost = alt_cost
                                log.debug(f"Found skill cost using alternative region {i+1}: '{alt_cost}' for '{text}'")
                                break
                        except:
                            continue
                    
                    # Final fallback if all regions fail
                    if not cost or cost == '':
                        log.debug(f"Could not parse skill cost for '{text}', cost_text: '{cost_text}', defaulting to 1")
                        cost = '1'  # Default cost to avoid crashes

                # Check if it's a gold skill
                mask = cv2.inRange(skill_info_cp, numpy.array([40, 180, 240]), numpy.array([100, 210, 255]))
                is_gold = True if mask[120, 600] == 255 else False

                skill_in_priority_list = False
                skill_name_raw = "" # Save original skill name to prevent OCR deviation
                priority = 99
                for i in range(len(skill)):
                    found_similar_blacklist = find_similar_skill_name(text, skill_blacklist, 0.7)
                    found_similar_prioritylist = find_similar_skill_name(text, skill[i], 0.7)
                    
                    # Debug: Log similarity matching results
                    if found_similar_prioritylist != "":
                        log.debug(f"✅ Skill match: '{text}' -> '{found_similar_prioritylist}' (priority {i})")
                    elif found_similar_blacklist != "":
                        log.debug(f"❌ Skill blacklisted: '{text}' -> '{found_similar_blacklist}'")
                    else:
                        log.debug(f"❌ No match for skill: '{text}' (priority {i})")
                    
                    if found_similar_blacklist != "": # Exclude skills that appear in blacklist
                        priority = -1
                        skill_name_raw = found_similar_blacklist
                        skill_in_priority_list = True
                        break
                    elif found_similar_prioritylist != "":
                        priority = i
                        skill_name_raw = found_similar_prioritylist
                        skill_in_priority_list = True
                        break
                if not skill_in_priority_list:
                    priority = len(skill)

                available = not image_match(skill_info_img, REF_SKILL_LEARNED).find_match

                if priority != -1: # Exclude skills that appear in blacklist
                    res.append({"skill_name": text,
                                "skill_name_raw": skill_name_raw,
                                "skill_cost": int(cost),
                                "priority": priority,
                                "gold": is_gold,
                                "subsequent_skill": "",
                                "available": available,
                                "y_pos": int(pos_center[1])})
            img[match_result.matched_area[0][1]:match_result.matched_area[1][1],
                match_result.matched_area[0][0]:match_result.matched_area[1][0]] = 0

        # Parse previously obtained skills
        match_result = image_match(img, REF_SKILL_LEARNED)
        if match_result.find_match:
            all_skill_scanned = False
            pos = match_result.matched_area
            pos_center = match_result.center_point
            if 550 < pos_center[0] < 640 and 450 < pos_center[1] < 1050:
                skill_info_img = img[pos[0][1] - 65:pos[1][1] + 75, pos[0][0] - 520: pos[1][0] + 150]
                skill_info_cp = origin_img[pos[0][1] - 65:pos[1][1] + 75, pos[0][0] - 470: pos[1][0] + 150]

                # Check if it's a gold skill
                mask = cv2.inRange(skill_info_cp, numpy.array([40, 180, 240]), numpy.array([100, 210, 255]))
                is_gold = True if mask[120, 600] == 255 else False
                skill_name_img = skill_info_img[10: 47, 100: 445]
                text = ocr_line(skill_name_img)
                res.append({"skill_name": text,
                            "skill_name_raw": text,
                            "skill_cost": 0,
                            "priority": -1,
                            "gold": is_gold,
                            "subsequent_skill": "",
                            "available": False,
                            "y_pos": int(pos_center[1])})
            img[match_result.matched_area[0][1]:match_result.matched_area[1][1],
                match_result.matched_area[0][0]:match_result.matched_area[1][0]] = 0
        if all_skill_scanned:
            break

    res = sorted(res, key=lambda x: x["y_pos"])
    # No precise calculation, but approximately y-axis less than 540 will cause skill name to display incompletely. No problems tested yet.
    return [{k: v for k, v in r.items() if k != "y_pos"} for r in res if r["y_pos"] >= 540]


def parse_factor(ctx: UmamusumeContext):
    origin_img = ctx.ctrl.get_screen()
    img = cv2.cvtColor(origin_img, cv2.COLOR_BGR2GRAY)
    factor_list = []
    while True:
        match_result = image_match(img, REF_FACTOR_DETECT_LABEL)
        if match_result.find_match:
            factor_info = ['unknown', 0]
            pos = match_result.matched_area
            factor_info_img_gray = img[pos[0][1] - 20:pos[1][1] + 25, pos[0][0] - 630: pos[1][0] - 25]
            factor_info_img = origin_img[pos[0][1] - 20:pos[1][1] + 25, pos[0][0] - 630: pos[1][0] - 25]
            factor_name_sub_img = factor_info_img_gray[15: 60, 45:320]
            factor_name = ocr_line(factor_name_sub_img)
            factor_level = 0
            factor_level_check_point = [factor_info_img[35, 535], factor_info_img[35, 565], factor_info_img[35, 595]]
            for i in range(len(factor_level_check_point)):
                if not compare_color_equal(factor_level_check_point[i], [223, 227, 237]):
                    factor_level += 1
                else:
                    break
            img[match_result.matched_area[0][1]:match_result.matched_area[1][1],
            match_result.matched_area[0][0]:match_result.matched_area[1][0]] = 0
            factor_info[0] = factor_name
            factor_info[1] = factor_level
            factor_list.append(factor_info)
        else:
            break
    ctx.cultivate_detail.parse_factor_done = True
    ctx.task.detail.cultivate_result['factor_list'] = factor_list


def preprocess_wiki_image_for_ingame_matching(template_img):
    """Preprocess wiki images to better match in-game conditions"""
    try:
        import cv2
        import numpy as np
        
        # Convert to grayscale if not already
        if len(template_img.shape) == 3:
            template_img = cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY)
        
        # Apply preprocessing steps to make wiki images match in-game better
        
        # 1. Resize to common in-game resolution
        height, width = template_img.shape
        if width > 400:  # If image is too large
            scale = 400 / width
            new_width = int(width * scale)
            new_height = int(height * scale)
            template_img = cv2.resize(template_img, (new_width, new_height))
        
        # 2. Apply slight blur to match in-game rendering
        template_img = cv2.GaussianBlur(template_img, (1, 1), 0)
        
        # 3. Adjust contrast to match in-game text rendering
        template_img = cv2.convertScaleAbs(template_img, alpha=1.1, beta=5)
        
        # 4. Apply slight noise reduction
        template_img = cv2.medianBlur(template_img, 1)
        
        return template_img
    except Exception as e:
        log.debug(f"Image preprocessing failed: {e}")
        return template_img
