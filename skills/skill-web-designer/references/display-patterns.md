# Display Patterns

The viewer renders semantic flows authored by the agent. It must not invent fixed workflow names from file types.

## Good Flow Titles

Use target-skill actions:
- `Route PMS Scenario`
- `Collect Project Truth`
- `Choose Skill Templates`
- `Run Expansion Tool`
- `Apply Workspace Hook`

## Bad Flow Titles

Avoid generic resource groups unless the target skill explicitly uses those terms:
- `Skill Entry`
- `Prompt Flow`
- `Script and Tool Flow`
- `Template Flow`
- `Supporting Docs and Config`

## Visual Mapping

- `read`: source/reference node
- `decide`: branching or gate node
- `edit`: prompt/config editing node
- `run`: script/tool execution node
- `verify`: check/result validation node
- `report`: final output node

The script may still compute `mode` from file structure as metadata, but `mode` must not control flow names.
