from bot.base.context import BotContext
from module.umamusume.scenario import base_scenario, ura_scenario, aoharuhai_scenario
from module.umamusume.task import UmamusumeTask, UmamusumeTaskType
from module.umamusume.define import *
from module.umamusume.types import TurnInfo
import bot.base.log as logger

log = logger.get_logger(__name__)
class CultivateContextDetail:
    turn_info: TurnInfo | None
    turn_info_history: list[TurnInfo]
    scenario : base_scenario.BaseScenario
    expect_attribute: list[int] | None
    follow_support_card_name: str
    follow_support_card_level: int
    extra_race_list: list[int]
    learn_skill_list: list[list[str]]
    learn_skill_blacklist: list[str]
    learn_skill_done: bool
    learn_skill_selected: bool
    cultivate_finish: bool
    tactic_list: list[int]
    debut_race_win: bool
    clock_use_limit: int
    clock_used: int
    learn_skill_threshold: int
    learn_skill_only_user_provided: bool
    learn_skill_before_race: bool
    allow_recover_tp: bool
    parse_factor_done: bool
    extra_weight: list
    manual_purchase_completed: bool

    def __init__(self):
        self.expect_attribute = None
        self.turn_info = TurnInfo()
        self.turn_info_history = []
        self.extra_race_list = []
        self.learn_skill_list = []
        self.learn_skill_blacklist = []
        self.learn_skill_done = False
        self.learn_skill_selected = False
        self.cultivate_finish = False
        self.tactic_list = []
        self.debut_race_win = False
        self.clock_use_limit = 0
        self.clock_used = 0
        self.allow_recover_tp = False
        self.parse_factor_done = False
        self.extra_weight = []
        self.manual_purchase_completed = False

    def reset_skill_learn(self):
        self.learn_skill_done = False
        self.learn_skill_selected = False


class UmamusumeContext(BotContext):
    task: UmamusumeTask
    cultivate_detail: CultivateContextDetail

    def __init__(self, task, ctrl):
        super().__init__(task, ctrl)

    def is_task_finish(self) -> bool:
        return False


def build_context(task: UmamusumeTask, ctrl) -> UmamusumeContext:
    ctx = UmamusumeContext(task, ctrl)
    if task.task_type == UmamusumeTaskType.UMAMUSUME_TASK_TYPE_CULTIVATE:
        detail = CultivateContextDetail()
        # Initialize corresponding inherited class based on scenario type
        match task.detail.scenario:
            case ScenarioType.SCENARIO_TYPE_URA:
                detail.scenario = ura_scenario.URAScenario()
            case ScenarioType.SCENARIO_TYPE_AOHARUHAI:
                detail.scenario = aoharuhai_scenario.AoharuHaiScenario()
            case _: # Placeholder, actually impossible to reach here
                log.error("Unknown scenario")
                detail.scenario = None
        detail.expect_attribute = task.detail.expect_attribute
        detail.follow_support_card_name = task.detail.follow_support_card_name
        detail.follow_support_card_level = task.detail.follow_support_card_level
        detail.extra_race_list = task.detail.extra_race_list
        detail.learn_skill_list = task.detail.learn_skill_list
        detail.learn_skill_blacklist = task.detail.learn_skill_blacklist
        detail.tactic_list = task.detail.tactic_list
        detail.clock_use_limit = task.detail.clock_use_limit
        detail.learn_skill_threshold = task.detail.learn_skill_threshold
        detail.learn_skill_only_user_provided = task.detail.learn_skill_only_user_provided
        detail.allow_recover_tp = task.detail.allow_recover_tp
        detail.extra_weight = task.detail.extra_weight
        
        # Load motivation thresholds from preset (with defaults) - ensure they are integers
        detail.motivation_threshold_year1 = int(getattr(task.detail, 'motivation_threshold_year1', 3))
        detail.motivation_threshold_year2 = int(getattr(task.detail, 'motivation_threshold_year2', 4))
        detail.motivation_threshold_year3 = int(getattr(task.detail, 'motivation_threshold_year3', 4))
        detail.prioritize_recreation = getattr(task.detail, 'prioritize_recreation', False)
        
        ctx.cultivate_detail = detail
    return ctx





