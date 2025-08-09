import time
from datetime import datetime
import pytz

import cv2

from bot.base.task import TaskStatus, EndTaskReason
from module.umamusume.task import EndTaskReason as UEndTaskReason
from bot.recog.image_matcher import image_match
from bot.recog.ocr import ocr_line, find_similar_text
from module.umamusume.asset.point import *
from module.umamusume.asset.ui import INFO
from module.umamusume.context import UmamusumeContext
import bot.base.log as logger

log = logger.get_logger(__name__)

def get_date_name(date_id: int) -> str:
    """Convert numeric date ID to readable date name"""
    if date_id <= 0:
        return "Unknown Date"
    
    # Date mapping constants
    DATE_YEAR = ['Junior', 'Classic', 'Senior', 'Finals']
    DATE_MONTH = ['Pre-Debut', 'Early Jan', 'Late Jan', 'Early Feb', 'Late Feb', 'Early Mar', 'Late Mar', 'Early Apr', 'Late Apr',
                  'Early May', 'Late May', 'Early Jun', 'Late Jun', 'Early Jul', 'Late Jul',
                  'Early Aug', 'Late Aug', 'Early Sep', 'Late Sep', 'Early Oct', 'Late Oct', 'Early Nov', 'Late Nov', 'Early Dec',
                  'Late Dec']
    
    # Calculate year and month
    year_index = (date_id - 1) // 24
    month_index = (date_id - 1) % 24
    
    if year_index >= len(DATE_YEAR) or month_index >= len(DATE_MONTH):
        return f"Unknown Date ({date_id})"
    
    year_name = DATE_YEAR[year_index]
    month_name = DATE_MONTH[month_index]
    
    return f"{year_name} Year {month_name}"

TITLE = [
    "Race Details",                    # TITLE[0]
    "Rest & Outing Confirmation",     # TITLE[1]
    "Rest & Recreation", ##handles the rest & recreation popup in summer # TITLE[2]
    "Network Error",                  # TITLE[3]
    "Try Again", ##handles the try again button when race failed (used clock items) # TITLE[4]
    "Earned Title",                  # TITLE[5]
    "Training Complete",              # TITLE[6]
    "Quick Mode Settings", ##handles the quick mode settings popup dialog # TITLE[7]
    "Recreation", ##handles the recreation popup dialog # TITLE[8]
    "Confirmation", ##handles the initial confirmation when learning skill starts # TITLE[9]
    "Skills Learned", ##handles the final completion dialog after learning skills is done # TITLE[10]
    "Complete Career", ##handles the complete career popup dialog # TITLE[11]
    "Umamusume Details", ##handles the umamusume details after career finish popup dialog # TITLE[12]
    "Fan Count Below Target Race Requirement", # TITLE[13]
    "Outing",                        # TITLE[14]
    "Skip Confirmation", ##handles the skip confirmation content when first start career # TITLE[15]
    "Rest", ##handles the rest popup confirmationdialog # TITLE[16]
    "Race Recommendations", ##handles the race recommendation popup dialog # TITLE[17]
    "Tactics", ##fallback to strategy # TITLE[18]
    "Strategy", ##handles the strategy change popup in race # TITLE[19]
    "Goal Not Reached", ##handles the goal not reached popup dialog (Oguri Cap G1 Goals) # TITLE[20]
    "Insufficient Fans", ###maybe the right insufficient fans dialog???????????????### # TITLE[21]
    "Warning", ##handles the warning 3 consecutive racing popup dialog # TITLE[22]
    "Infirmary", ##handles the infirmary popup confirmation dialog # TITLE[23]
    "Gift Box",                      # TITLE[24]
    "Collection Successful", ###maybe event collection successful??????????????### # TITLE[25]
    "Character Story Unlocked",      # TITLE[26]
    "Skill Acquisition Confirmation", # TITLE[27]
    "Successfully Acquired Skill",   # TITLE[28]
    "Target Achievement Count Insufficient", # TITLE[29] - FIXED: was "Confirm"
    "Event Story Unlocked",          # TITLE[30]
    "Confirm", ##Recover TP Confirm button if you enable auto recover tp in UAT website # TITLE[31] - FIXED: was "Target Achievement Count Insufficient"
    "Recover TP", ##Recover TP Confirm popup dialog to buy the recover tp item # TITLE[32]
    "Factor Confirmation", ##handles the factor confirmation popup dialog (Fujikiseki Show) # TITLE[33]
    # Limited Time: Fujikiseki Show
    "New Difficulty Unlocked", # TITLE[34]
    # Aoharu Cup
    "Auto Formation", # TITLE[35]
    "Battle Confirmation", # TITLE[36]
]


def script_info(ctx: UmamusumeContext):
    img = ctx.current_screen
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    result = image_match(img, UI_INFO)
    if result.find_match:
        pos = result.matched_area
        title_img = img[pos[0][1] - 5:pos[1][1] + 5, pos[0][0] + 150: pos[1][0] + 405]
        title_text = ocr_line(title_img)
        log.debug(title_text)
        
        # Debug: Log the original OCR text and similarity matching
        original_text = title_text
        title_text = find_similar_text(title_text, TITLE, 0.8)
        
        if title_text == "":
            log.warning(f"Unknown option box - OCR: '{original_text}'")
            # Try with lower threshold for better matching
            title_text = find_similar_text(original_text, TITLE, 0.6)
            if title_text == "":
                log.warning(f"Still no match with lower threshold - OCR: '{original_text}'")
                return
            else:
                log.info(f"✅ Found match with lower threshold: '{original_text}' -> '{title_text}'")
        else:
            log.info(f"✅ Found match: '{original_text}' -> '{title_text}'")
        
        # Debug: Show which TITLE index this matches to
        try:
            title_index = TITLE.index(title_text)
            log.info(f"🔍 DEBUG: title_text='{title_text}' matches TITLE[{title_index}]='{TITLE[title_index]}'")
        except ValueError:
            log.warning(f"⚠️ DEBUG: title_text='{title_text}' not found in TITLE array")
        
        # Force correct handler for "Confirm" - bypass TITLE array indexing issues
        if title_text == "Confirm":
            log.info("🔋 FORCED: Handling 'Confirm' (TP recovery) screen")
            if not ctx.cultivate_detail.allow_recover_tp:
                ctx.task.end_task(TaskStatus.TASK_STATUS_FAILED, UEndTaskReason.TP_NOT_ENOUGH)
            else:
                ctx.ctrl.click_by_point(TO_RECOVER_TP)
            return  # Exit early to prevent wrong handler execution
        
        # Force correct handler for "Recover TP" - bypass TITLE array indexing issues
        if title_text == "Recover TP":
            log.info("🔋 FORCED: Handling 'Recover TP' screen")
            screen = ctx.ctrl.get_screen(to_gray=True)
            
            # Debug: Check image matching results
            match1 = image_match(screen, REF_RECOVER_TP_1)
            match2 = image_match(screen, REF_RECOVER_TP_2)
            match3 = image_match(screen, REF_RECOVER_TP_3)
            
            log.info(f"🔍 DEBUG: REF_RECOVER_TP_1 match: {match1.find_match}")
            log.info(f"🔍 DEBUG: REF_RECOVER_TP_2 match: {match2.find_match}")
            log.info(f"🔍 DEBUG: REF_RECOVER_TP_3 match: {match3.find_match}")
            
            # Try to find REF_RECOVER_TP_1 (Use button)
            if match1.find_match:
                log.info("✅ Found REF_RECOVER_TP_1 - clicking USE_TP_DRINK")
                ctx.ctrl.click_by_point(USE_TP_DRINK)
            # Try to find REF_RECOVER_TP_2 (Confirm button)
            elif match2.find_match:
                log.info("✅ Found REF_RECOVER_TP_2 - clicking USE_TP_DRINK_CONFIRM")
                ctx.ctrl.click_by_point(USE_TP_DRINK_CONFIRM)
            # Try to find REF_RECOVER_TP_3 (Result close button)
            elif match3.find_match:
                log.info("✅ Found REF_RECOVER_TP_3 - clicking USE_TP_DRINK_RESULT_CLOSE")
                ctx.ctrl.click_by_point(USE_TP_DRINK_RESULT_CLOSE)
            else:
                log.warning("⚠️ No TP recovery image templates found - trying fallback")
                # Try to find any "Confirm" or "Use" button by OCR
                try:
                    # Look for "Confirm" button around the typical position
                    ctx.ctrl.click(600, 400, "Fallback TP recovery click - Confirm area")
                except:
                    # Final fallback - click center of screen
                    ctx.ctrl.click(350, 600, "Final fallback TP recovery click")
            return  # Exit early to prevent wrong handler execution

        if title_text == TITLE[0]: #race details
            ctx.ctrl.click_by_point(CULTIVATE_GOAL_RACE_INTER_3)
            time.sleep(1)
        if title_text == TITLE[1]:  # "Rest & Outing Confirmation"
            log.info("🏖️ Handling Rest & Outing Confirmation")
            ctx.ctrl.click_by_point(INFO_SUMMER_REST_CONFIRM)
        if title_text == TITLE[2]:  # "Rest & Recreation"
            log.info("🏖️ Handling Rest & Recreation")
            ctx.ctrl.click_by_point(INFO_SUMMER_REST_CONFIRM)
        if title_text == TITLE[3]:
            ctx.ctrl.click_by_point(NETWORK_ERROR_CONFIRM)
        if title_text == TITLE[4]:  # Try Again
            # Check if this is actually a race fail screen using image detection
            img = ctx.current_screen
            img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            from module.umamusume.asset.template import UI_RACE_FAIL
            result = image_match(img_gray, UI_RACE_FAIL)
            
            if result.find_match:
                # Only use clock if we haven't reached the limit
                if ctx.cultivate_detail.clock_used < ctx.cultivate_detail.clock_use_limit:
                    ctx.ctrl.click_by_point(RACE_FAIL_CONTINUE_USE_CLOCK)
                    ctx.cultivate_detail.clock_used += 1
                    log.info("🔋 Clock limit %s, used %s", str(ctx.cultivate_detail.clock_use_limit), str(ctx.cultivate_detail.clock_used))
                else:
                    ctx.ctrl.click_by_point(RACE_FAIL_CONTINUE_CANCEL)
                    log.info("🔋 Reached Clock limit, cancel race")
            else:
                # Not a race fail screen, just confirm
                ctx.ctrl.click_by_point(RACE_FAIL_CONTINUE_CANCEL)
                log.info("🔋 Not a race fail screen - canceling")
            log.debug("Clock limit %s, used %s", str(ctx.cultivate_detail.clock_use_limit),
                        str(ctx.cultivate_detail.clock_used))
        if title_text == TITLE[5]: #Earned Title
            ctx.ctrl.click_by_point(GET_TITLE_CONFIRM)
        if title_text == TITLE[6]: #Training Complete
            ctx.ctrl.click_by_point(CULTIVATE_FINISH_RETURN_CONFIRM)
        if title_text == TITLE[7]: #Quick Mode Settings
            ctx.ctrl.click_by_point(SCENARIO_SHORTEN_SET_2)
            time.sleep(0.5)
            ctx.ctrl.click_by_point(SCENARIO_SHORTEN_CONFIRM)
        if title_text == TITLE[8]: #Recreation
            # Check for different types of recreation by detecting templates
            img = ctx.current_screen
            img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            from module.umamusume.asset.template import UI_FRIEND_RECREATION, UI_FRIEND_RECREATION_COMPLETE
            
            # Check for friend recreation complete first (most specific)
            result_complete = image_match(img_gray, UI_FRIEND_RECREATION_COMPLETE)
            log.info(f"🔍 Recreation - Friend recreation complete template match: {result_complete.find_match}")
            
            if result_complete.find_match:
                # This is friend recreation complete - use CULTIVATE_TRIP_WITH_FRIEND_COMPLETE
                log.info("🏖️ Friend recreation complete detected - using CULTIVATE_TRIP_WITH_FRIEND_COMPLETE")
                ctx.ctrl.click_by_point(CULTIVATE_TRIP_WITH_FRIEND_COMPLETE)
            else:
                # Check for regular friend recreation
                result = image_match(img_gray, UI_FRIEND_RECREATION)
                log.info(f"🔍 Recreation - Friend recreation template match: {result.find_match}")
                
                if result.find_match:
                    # This is friend recreation - use CULTIVATE_TRIP_WITH_FRIEND
                    log.info("🏖️ Friend recreation detected - using CULTIVATE_TRIP_WITH_FRIEND")
                    ctx.ctrl.click_by_point(CULTIVATE_TRIP_WITH_FRIEND)
                else:
                    # This is regular recreation - use CULTIVATE_OPERATION_COMMON_CONFIRM
                    log.info("🏖️ Regular recreation detected - using CULTIVATE_OPERATION_COMMON_CONFIRM")
                    ctx.ctrl.click_by_point(CULTIVATE_OPERATION_COMMON_CONFIRM)
        if title_text == TITLE[9]: #Confirmation
            ctx.ctrl.click_by_point(CULTIVATE_LEARN_SKILL_CONFIRM_AGAIN)
        if title_text == TITLE[10]: #Skills Learned
            ctx.ctrl.click_by_point(CULTIVATE_LEARN_SKILL_DONE_CONFIRM)
            ctx.cultivate_detail.learn_skill_selected = False
        if title_text == TITLE[11]: #Complete Career
            ctx.ctrl.click_by_point(CULTIVATE_FINISH_CONFIRM_AGAIN)
        if title_text == TITLE[12]: #Umamusume Details
            ctx.ctrl.click_by_point(CULTIVATE_RESULT_CONFIRM)
        if title_text == TITLE[13]: #Fan Count Below Target Race Requirement
            ctx.ctrl.click_by_point(CULTIVATE_FAN_NOT_ENOUGH_RETURN)
        if title_text == TITLE[14]:
            ctx.ctrl.click_by_point(CULTIVATE_TRIP_WITH_FRIEND)
        if title_text == TITLE[15]:  # Skip Confirmation
            # Check if this might be a skill confirmation by looking for the template
            img = ctx.current_screen
            img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            from module.umamusume.asset.ui import CONFIRMATION_LEARNSKILL_BUTTON
            result = image_match(img_gray, CONFIRMATION_LEARNSKILL_BUTTON)
            log.info(f"🔍 Skip Confirmation - Template matching result: {result.find_match}")
            if result.find_match:
                # Use template matching coordinates for skill confirmation
                center_x = (result.matched_area[0][0] + result.matched_area[1][0]) // 2
                center_y = (result.matched_area[0][1] + result.matched_area[1][1]) // 2
                ctx.ctrl.click(center_x, center_y, "Skill confirmation using template matching (Skip Confirmation)")
                log.info(f"✅ Found skill confirmation button at ({center_x}, {center_y}) via Skip Confirmation")
            else:
                # Use CULTIVATE_LEARN_SKILL_CONFIRM_AGAIN coordinates for skill confirmations
                ctx.ctrl.click_by_point(CULTIVATE_LEARN_SKILL_CONFIRM_AGAIN)
                log.info("⚠️ Using skill confirmation coordinates for Skip Confirmation - template not found")
        if title_text == TITLE[16]: #Rest
            ctx.ctrl.click_by_point(CULTIVATE_OPERATION_COMMON_CONFIRM)
        if title_text == TITLE[17]: #Race Recommendations
            ctx.ctrl.click_by_point(RACE_RECOMMEND_CONFIRM)
        if title_text == TITLE[18] or title_text == TITLE[19]:  # "Tactics" or "Strategy"
            date = ctx.cultivate_detail.turn_info.date
            if date != -1:
                if date <= 72:
                    ctx.ctrl.click_by_point(TACTIC_LIST[ctx.cultivate_detail.tactic_list[int((date - 1)/ 24)] - 1])
                else:
                    ctx.ctrl.click_by_point(TACTIC_LIST[ctx.cultivate_detail.tactic_list[2] - 1])
            time.sleep(0.5)
            ctx.ctrl.click_by_point(BEFORE_RACE_CHANGE_TACTIC_CONFIRM)
        if title_text == TITLE[20]:  # "Goal Not Reached" - Navigate to races to fulfill goal
            # For Oguri Cap G1 race goals, go to race selection instead of failing
            log.info("🏆 Goal Not Reached detected - navigating to races to fulfill G1 requirements")
            
            # Close popup to return to main menu where date is visible
            ctx.ctrl.click_by_point(WIN_TIMES_NOT_ENOUGH_RETURN)
            time.sleep(2)  # Wait longer for main menu to fully load
            
            # Refresh screen to get the actual main menu
            ctx.current_screen = ctx.ctrl.get_screen()
            
            # Read actual current date from main menu
            from module.umamusume.script.cultivate_task.parse import parse_date
            current_date = parse_date(ctx.current_screen, ctx)
            if current_date == -1:
                log.warning("Failed to parse date from main menu")
                return
            
            # Use current period for race planning (no +1 needed)
            next_period = current_date
            
            # Update context with accurate date
            ctx.cultivate_detail.turn_info.date = current_date
            
            current_date_name = get_date_name(current_date)
            next_period_name = get_date_name(next_period)
            log.info(f"📅 Current game date: {current_date} ({current_date_name}), planning races for: {next_period} ({next_period_name})")
            log.info(f"🔄 Updated game date to: {current_date} ({current_date_name})")
            
            # Check for races in the next period
            from module.umamusume.asset.race_data import get_races_for_period
            next_period_races = get_races_for_period(next_period)
            
            if next_period_races:
                log.info(f"🏁 Found {len(next_period_races)} races in next period {next_period} ({next_period_name}): {next_period_races}")
                
                # Check if any of these races are in user's selected race list
                user_selected_races = ctx.cultivate_detail.extra_race_list
                matching_races = [race_id for race_id in next_period_races if race_id in user_selected_races]
                
                if matching_races:
                    log.info(f"✅ Found {len(matching_races)} user-selected races in next period {next_period} ({next_period_name}): {matching_races}")
                    # Set the first matching race as target
                    target_race_id = matching_races[0]
                    log.info(f"🎯 Setting target race ID: {target_race_id}")
                else:
                    log.info(f"⚠️ No user-selected races found in next period {next_period} ({next_period_name})")
                    target_race_id = 0  # Will search for any available race
            else:
                log.info(f"⚠️ No races available in next period {next_period} ({next_period_name})")
                target_race_id = 0  # Will search for any available race
            
            # Set a race operation so the race list logic knows what to do
            from module.umamusume.types import TurnOperation, TurnOperationType
            ctx.cultivate_detail.turn_info.turn_operation = TurnOperation()
            ctx.cultivate_detail.turn_info.turn_operation.turn_operation_type = TurnOperationType.TURN_OPERATION_TYPE_RACE
            ctx.cultivate_detail.turn_info.turn_operation.race_id = target_race_id
            log.info("🏁 Set race operation for G1 goal farming")
            ctx.ctrl.click_by_point(CULTIVATE_RACE)  # Navigate to race menu
            log.info("📋 Navigated to race selection to work towards G1 goals")
            
            # If no user-selected races found, search for suitable race template
            if not matching_races:
                log.info("🔍 No user-selected races found - searching for suitable race template")
                time.sleep(2)  # Wait for race menu to load
                
                # Get current screen and search for suitable race template
                img = ctx.ctrl.get_screen(to_gray=True)
                from module.umamusume.asset import REF_SUITABLE_RACE
                suitable_race_match = image_match(img, REF_SUITABLE_RACE)
                
                if suitable_race_match.find_match:
                    log.info("✅ Found suitable race template - clicking on it")
                    center_x = suitable_race_match.center_point[0]
                    center_y = suitable_race_match.center_point[1]
                    ctx.ctrl.click(center_x, center_y, "Click suitable race")
                    log.info(f"🎯 Clicked suitable race at position ({center_x}, {center_y})")
                else:
                    log.info("⚠️ Suitable race template not found - returning to main menu for normal logic")
                    # Return to main menu since no races are available
                    ctx.ctrl.click_by_point(RETURN_TO_CULTIVATE_MAIN_MENU)
                    # Clear the race operation so AI can decide what to do next
                    ctx.cultivate_detail.turn_info.turn_operation = None
                    log.info("🔄 Returned to main menu - AI will decide next action (training, rest, trip, etc.)")
        if title_text == TITLE[21]:  # insufficient fans (was TITLE[19])
            log.info("🏆 insufficient fans detected - navigating to races to fulfill fan goals")
            
            # Close popup to return to main menu where date is visible
            ctx.ctrl.click_by_point(CULTIVATE_FAN_NOT_ENOUGH_RETURN)
            time.sleep(2)  # Wait longer for main menu to fully load
            
            # Refresh screen to get the actual main menu
            ctx.current_screen = ctx.ctrl.get_screen()
            
            # Read actual current date from main menu
            from module.umamusume.script.cultivate_task.parse import parse_date
            current_date = parse_date(ctx.current_screen, ctx)
            if current_date == -1:
                log.warning("Failed to parse date from main menu")
                return
            
            # Use current period for race planning (no +1 needed)
            next_period = current_date
            
            # Update context with accurate date
            ctx.cultivate_detail.turn_info.date = current_date
            
            current_date_name = get_date_name(current_date)
            next_period_name = get_date_name(next_period)
            log.info(f"📅 Current game date: {current_date} ({current_date_name}), planning races for: {next_period} ({next_period_name})")
            log.info(f"🔄 Updated game date to: {current_date} ({current_date_name})")
            
            # Check for races in the next period
            from module.umamusume.asset.race_data import get_races_for_period
            next_period_races = get_races_for_period(next_period)
            
            if next_period_races:
                log.info(f"🏁 Found {len(next_period_races)} races in next period {next_period} ({next_period_name}): {next_period_races}")
                
                # Check if any of these races are in user's selected race list
                user_selected_races = ctx.cultivate_detail.extra_race_list
                matching_races = [race_id for race_id in next_period_races if race_id in user_selected_races]
                
                if matching_races:
                    log.info(f"✅ Found {len(matching_races)} user-selected races in next period {next_period} ({next_period_name}): {matching_races}")
                    # Set the first matching race as target
                    target_race_id = matching_races[0]
                    log.info(f"🎯 Setting target race ID: {target_race_id}")
                else:
                    log.info(f"⚠️ No user-selected races found in next period {next_period} ({next_period_name})")
                    target_race_id = 0  # Will search for any available race
            else:
                log.info(f"⚠️ No races available in next period {next_period} ({next_period_name})")
                target_race_id = 0  # Will search for any available race
            
            # Set a race operation so the race list logic knows what to do
            from module.umamusume.types import TurnOperation, TurnOperationType
            ctx.cultivate_detail.turn_info.turn_operation = TurnOperation()
            ctx.cultivate_detail.turn_info.turn_operation.turn_operation_type = TurnOperationType.TURN_OPERATION_TYPE_RACE
            ctx.cultivate_detail.turn_info.turn_operation.race_id = target_race_id
            log.info("🏁 Set race operation for fan farming")
            ctx.ctrl.click_by_point(CULTIVATE_RACE)
            log.info("📋 Navigated to race selection to work towards fan goals")
            
            # If no user-selected races found, search for suitable race template
            if not matching_races:
                log.info("🔍 No user-selected races found - searching for suitable race template")
                time.sleep(2)  # Wait for race menu to load
                
                # Get current screen and search for suitable race template
                img = ctx.ctrl.get_screen(to_gray=True)
                from module.umamusume.asset import REF_SUITABLE_RACE
                suitable_race_match = image_match(img, REF_SUITABLE_RACE)
                
                if suitable_race_match.find_match:
                    log.info("✅ Found suitable race template - clicking on it")
                    center_x = suitable_race_match.center_point[0]
                    center_y = suitable_race_match.center_point[1]
                    ctx.ctrl.click(center_x, center_y, "Click suitable race")
                    log.info(f"🎯 Clicked suitable race at position ({center_x}, {center_y})")
                else:
                    log.info("⚠️ Suitable race template not found - returning to main menu for normal logic")
                    # Return to main menu since no races are available
                    ctx.ctrl.click_by_point(RETURN_TO_CULTIVATE_MAIN_MENU)
                    # Clear the race operation so AI can decide what to do next
                    ctx.cultivate_detail.turn_info.turn_operation = None
                    log.info("🔄 Returned to main menu - AI will decide next action (training, rest, trip, etc.)")
        if title_text == TITLE[22]:  # Consecutive Racing (was TITLE[20])
            ctx.ctrl.click_by_point(CULTIVATE_TOO_MUCH_RACE_WARNING_CONFIRM)
        if title_text == TITLE[23]:  # Infirmary Confirmation (was TITLE[21])
            ctx.ctrl.click_by_point(CULTIVATE_OPERATION_COMMON_CONFIRM)
        if title_text == TITLE[24]:  # Gift Box (was TITLE[22])
            ctx.ctrl.click_by_point(RECEIVE_GIFT)
        if title_text == TITLE[25]:  # Collection Successful (was TITLE[23])
            ctx.ctrl.click_by_point(RECEIVE_GIFT_SUCCESS_CLOSE)
        if title_text == TITLE[26]:  # Character Story Unlocked (was TITLE[24])
            ctx.ctrl.click_by_point(UNLOCK_STORY_TO_HOME_PAGE)
        if title_text == TITLE[27]:  # Skill Acquisition Confirmation
            # Try to find the confirmation button using template matching first
            img = ctx.current_screen
            img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            from module.umamusume.asset.ui import CONFIRMATION_LEARNSKILL_BUTTON
            result = image_match(img_gray, CONFIRMATION_LEARNSKILL_BUTTON)
            log.info(f"🔍 Primary template matching result: {result.find_match}")
            if result.find_match:
                # Use template matching coordinates
                center_x = (result.matched_area[0][0] + result.matched_area[1][0]) // 2
                center_y = (result.matched_area[0][1] + result.matched_area[1][1]) // 2
                ctx.ctrl.click(center_x, center_y, "Skill confirmation using template matching")
                log.info(f"✅ Found skill confirmation button at ({center_x}, {center_y})")
            else:
                # Fallback to hardcoded coordinates
                ctx.ctrl.click_by_point(CULTIVATE_LEARN_SKILL_CONFIRM_AGAIN)
                log.info("⚠️ Using fallback coordinates for skill confirmation - template not found")
        if title_text == TITLE[28]:  # Successfully Acquired Skill  
            ctx.ctrl.click_by_point(CULTIVATE_LEARN_SKILL_DONE_CONFIRM)
            ctx.cultivate_detail.learn_skill_selected = False
        if title_text == TITLE[29]:  # Target Achievement Count Insufficient
            log.info("🎯 Handling 'Target Achievement Count Insufficient' screen")
            ctx.ctrl.click_by_point(WIN_TIMES_NOT_ENOUGH_RETURN)
        if title_text == TITLE[30]:  # Event Story Unlocked
            ctx.ctrl.click_by_point(ACTIVITY_STORY_UNLOCK_CONFIRM)

        if title_text == TITLE[31]:  # Confirm (TP recovery)
            log.info("🔋 Handling 'Confirm' (TP recovery) screen")
            if not ctx.cultivate_detail.allow_recover_tp:
                ctx.task.end_task(TaskStatus.TASK_STATUS_FAILED, UEndTaskReason.TP_NOT_ENOUGH)
            else:
                ctx.ctrl.click_by_point(TO_RECOVER_TP)
        if title_text == TITLE[32]:  # Recover TP
            log.info("🔋 Handling 'Recover TP' screen")
            if image_match(ctx.ctrl.get_screen(to_gray=True), REF_RECOVER_TP_1).find_match:
                log.info("✅ Found REF_RECOVER_TP_1 - clicking USE_TP_DRINK")
                ctx.ctrl.click_by_point(USE_TP_DRINK)
            elif image_match(ctx.ctrl.get_screen(to_gray=True), REF_RECOVER_TP_2).find_match:
                log.info("✅ Found REF_RECOVER_TP_2 - clicking USE_TP_DRINK_CONFIRM")
                ctx.ctrl.click_by_point(USE_TP_DRINK_CONFIRM)
            elif image_match(ctx.ctrl.get_screen(to_gray=True), REF_RECOVER_TP_3).find_match:
                log.info("✅ Found REF_RECOVER_TP_3 - clicking USE_TP_DRINK_RESULT_CLOSE")
                ctx.ctrl.click_by_point(USE_TP_DRINK_RESULT_CLOSE)
            else:
                log.warning("⚠️ No TP recovery image templates found - trying fallback")
                # Fallback: try to click the first "Use" button
                ctx.ctrl.click(600, 400, "Fallback TP recovery click")
        if title_text == TITLE[33]:  # Factor Confirmation
            # Limited time: Fuji Kiseki Show
            # Currently seems only used here "Select cultivation difficulty, if there are others in the future, need to adjust code structure"
            beijing_tz = pytz.timezone('Asia/Shanghai')
            cutoff_time = beijing_tz.localize(datetime(2025, 7, 13, 11, 59))
            current_time_beijing = datetime.now(beijing_tz)

            if current_time_beijing <= cutoff_time:
                if ctx.task.detail.fujikiseki_show_mode == False:
                    ctx.ctrl.click(360, 300, "Select normal mode")
                else :
                    ctx.ctrl.click(360, 500, "Select Fuji Kiseki Show mode")
                    match = False
                    for i in range(5):
                        screen = ctx.ctrl.get_screen(to_gray=True)
                        if ((not image_match(screen, FUJIKISEKI_SHOW_DIFFICULTY_LOCKED).find_match) 
                            and image_match(screen, FUJIKISEKI_SHOW_DIFFICULTY[ctx.task.detail.fujikiseki_show_difficulty-1]).find_match):
                            log.info(f"Selected difficulty {ctx.task.detail.fujikiseki_show_difficulty}")
                            match = True
                            break
                        ctx.ctrl.click(675, 800, "Switch to next difficulty")
                        time.sleep(1)
                    if not match:
                        log.error(f"Selected difficulty {ctx.task.detail.fujikiseki_show_difficulty} is not unlocked yet, please play lower difficulty modes first!")
                        ctx.task.end_task(TaskStatus.TASK_STATUS_FAILED, UEndTaskReason.DIFFICULTY_LOCKED)
                        return
                        
                ctx.ctrl.click(520, 1180, "")
            else:
                # Fallback for non-Fujikiseki Factor Confirmation
                ctx.ctrl.click_by_point(CULTIVATE_RESULT_DIVISOR_CONFIRM)
            
        if title_text == TITLE[34]:  # New Difficulty Unlocked
            # Limited time: Fuji Kiseki Show
            ctx.ctrl.click(360, 850, "Confirm unlock new difficulty")
        time.sleep(1)

