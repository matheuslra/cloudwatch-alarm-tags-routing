"""The expected route for each kind of alarm event, and the rules read from infra/routing.yaml."""
import copy
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


class TemplateLoader(yaml.SafeLoader):
    pass


# !Ref Environment becomes its default. No other tag appears inside an event pattern.
TemplateLoader.add_multi_constructor("!", lambda loader, suffix, node: "prod" if suffix == "Ref" else None)


def rules():
    resources = yaml.load((ROOT / "infra" / "routing.yaml").read_text(), Loader=TemplateLoader)["Resources"]
    return {name: r["Properties"]["EventPattern"] for name, r in resources.items() if r["Type"] == "AWS::Events::Rule"}


def event(tags=None, status="SUCCESS", state="ALARM"):
    sample = copy.deepcopy(json.loads((ROOT / "samples" / "alarm-event.json").read_text()))
    sample["detail"]["state"]["value"] = state
    if tags is not None:
        sample["detail"]["alarmTags"] = tags
        sample["detail"]["alarmTagsStatus"] = status
    return sample


CASES = [
    ("payments in prod", event({"Team": "payments", "Environment": "prod"}), {"PaymentsRule"}),
    ("search in prod", event({"Team": "search", "Environment": "prod"}), {"SearchRule"}),
    ("payments in dev pages nobody", event({"Team": "payments", "Environment": "dev"}), set()),
    ("a typo in Team", event({"Team": "paymnets", "Environment": "prod"}), {"UnknownTeamRule"}),
    ("no Team tag", event({"Environment": "prod"}), {"NoTeamTagRule"}),
    ("propagation off", event(), {"NoTeamTagRule"}),
    ("tags unreadable", event({}, status="FAILURE"), {"NoTeamTagRule"}),
    ("back to OK pages nobody", event({"Team": "payments", "Environment": "prod"}, state="OK"), set()),
]
