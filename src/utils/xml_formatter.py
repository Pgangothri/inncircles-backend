def xml_wrap(task_id, status, current_step, tools_used, reasoning, result):
    if isinstance(tools_used, list) and all(isinstance(t, dict) for t in tools_used):
        tools_xml = "\n".join(
            f"<tool name='{t.get('name', '')}' status='{t.get('status', '')}' />"
            for t in tools_used
        )
    elif isinstance(tools_used, list) and all(isinstance(t, str) for t in tools_used):
        tools_xml = "\n".join(
            f"<tool name='{t}' status='unknown' />" for t in tools_used
        )
    else:
        tools_xml = ""

    xml = f"""
<agent_response>
  <task_id>{task_id}</task_id>
  <status>{status}</status>
  <current_step>{current_step}</current_step>
  <tools_used>
    {tools_xml}
  </tools_used>
  <reasoning>
    <thought>{reasoning['thought']}</thought>
    <next_action>{reasoning['next_action']}</next_action>
  </reasoning>
  <result>
    <success>{str(result['success']).lower()}</success>
    <data>{result['data']}</data>
    <errors>{result['errors']}</errors>
  </result>
</agent_response>
""".strip()
    return xml
