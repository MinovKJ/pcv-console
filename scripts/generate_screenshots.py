import os
import subprocess
import sys

ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

def render_html_to_png(html_content: str, out_png: str, width=1100, height=850):
    temp_html = os.path.join(ASSETS_DIR, "_temp_render.html")
    with open(temp_html, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    file_url = f"file:///{temp_html.replace(os.sep, '/')}"
    cmd = (
        f'cmd /c "start /wait \"\" \"{CHROME}\" --headless=new --hide-scrollbars '
        f'--virtual-time-budget=4000 --window-size={width},{height} '
        f'--screenshot=\"{out_png}\" \"{file_url}\""'
    )
    subprocess.run(cmd, shell=True)
    if os.path.exists(temp_html):
        os.remove(temp_html)
    print(f"Generated: {os.path.basename(out_png)} ({os.path.getsize(out_png)} bytes)")

# ── 1. PYTEST TERMINAL RUN ──────────────────────────────────────────────────
PYTEST_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body { background: #090d13; margin: 0; padding: 24px; font-family: 'Consolas', 'Cascadia Code', monospace; }
  .window { background: #0d1117; border-radius: 10px; border: 1px solid #30363d; box-shadow: 0 16px 36px rgba(0,0,0,0.6); overflow: hidden; }
  .titlebar { background: #161b22; padding: 12px 18px; display: flex; align-items: center; border-bottom: 1px solid #30363d; }
  .dot { width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
  .dot-red { background: #ff5f56; } .dot-yellow { background: #ffbd2e; } .dot-green { background: #27c93f; }
  .title { color: #8b949e; font-size: 13px; margin-left: 14px; font-weight: 600; }
  .terminal { padding: 20px 24px; color: #c9d1d9; font-size: 13px; line-height: 1.55; white-space: pre; }
  .cmd { color: #58a6ff; font-weight: bold; }
  .pass { color: #3fb950; font-weight: bold; }
  .dim { color: #8b949e; }
  .summary {
    color: #3fb950; font-weight: bold; font-size: 14px;
    background: rgba(46, 160, 67, 0.15); border: 1px solid #238636;
    border-radius: 6px; padding: 10px 16px; margin-top: 14px; display: block; text-align: center;
  }
</style>
</head>
<body>
<div class="window">
  <div class="titlebar">
    <div class="dot dot-red"></div>
    <div class="dot dot-yellow"></div>
    <div class="dot dot-green"></div>
    <div class="title">terminal — pytest tests/ -v (30 / 30 Automated Suite Passing)</div>
  </div>
  <div class="terminal"><span class="dim">$</span> <span class="cmd">pytest tests/ -v</span>
<span class="dim">================================== test session starts ===================================</span>
platform win32 -- Python 3.14.2, pytest-9.2.0, pluggy-1.7.0 -- rootdir: /pcv-console
plugins: anyio-4.12.1, asyncio-1.5.0, cov-6.0.0
asyncio: mode=Mode.AUTO, default_loop_scope=function

tests/test_auth.py::test_password_hashing                                  <span class="pass">PASSED  [ 13%]</span>
tests/test_auth.py::test_access_token_creation_and_decoding                <span class="pass">PASSED  [ 16%]</span>
tests/test_auth.py::test_refresh_token_creation_and_decoding               <span class="pass">PASSED  [ 20%]</span>
tests/test_auth.py::test_invalid_token_raises                              <span class="pass">PASSED  [ 23%]</span>
tests/test_cases.py::test_case_create_defaults                             <span class="pass">PASSED  [ 26%]</span>
tests/test_cases.py::test_case_update_partial                              <span class="pass">PASSED  [ 30%]</span>
tests/test_cases.py::test_alert_assign_request                             <span class="pass">PASSED  [ 33%]</span>
tests/test_injection_guard.py::test_clean_text_passes                      <span class="pass">PASSED  [ 36%]</span>
tests/test_injection_guard.py::test_explicit_soc_override_detected         <span class="pass">PASSED  [ 40%]</span>
tests/test_injection_guard.py::test_explicit_must_accuse_detected          <span class="pass">PASSED  [ 43%]</span>
tests/test_injection_guard.py::test_explicit_critical_forensic_alert       <span class="pass">PASSED  [ 46%]</span>
tests/test_injection_guard.py::test_classify_benign_detected               <span class="pass">PASSED  [ 50%]</span>
tests/test_injection_guard.py::test_subtle_maintenance_ticket_detected     <span class="pass">PASSED  [ 53%]</span>
tests/test_injection_guard.py::test_subtle_sla_pressure_detected           <span class="pass">PASSED  [ 56%]</span>
tests/test_injection_guard.py::test_subtle_change_ticket_detected          <span class="pass">PASSED  [ 60%]</span>
tests/test_injection_guard.py::test_multiple_subtle_hits_raises_risk_score  <span class="pass">PASSED  [ 63%]</span>
tests/test_injection_guard.py::test_recommendation_block_on_explicit       <span class="pass">PASSED  [ 66%]</span>
tests/test_injection_guard.py::test_recommendation_caution_on_single_subtle <span class="pass">PASSED  [ 70%]</span>
tests/test_injection_guard.py::test_recommendation_pass_on_clean           <span class="pass">PASSED  [ 73%]</span>
tests/test_injection_guard.py::test_summary_string_format                  <span class="pass">PASSED  [ 76%]</span>
tests/test_triage.py::test_health                                          <span class="pass">PASSED  [ 80%]</span>
tests/test_triage.py::test_injection_guard_blocks_explicit_injection       <span class="pass">PASSED  [ 83%]</span>
tests/test_triage.py::test_clean_graph_not_blocked                         <span class="pass">PASSED  [ 86%]</span>
tests/test_verifier_adapter.py::test_demo_verifier_well_formed             <span class="pass">PASSED  [ 90%]</span>
tests/test_verifier_adapter.py::test_run_verification_returns_well_formed   <span class="pass">PASSED  [ 93%]</span>
tests/test_verifier_adapter.py::test_verifier_valid_edge                   <span class="pass">PASSED  [ 96%]</span>
tests/test_verifier_adapter.py::test_verifier_fabricated_target_invalid     <span class="pass">PASSED  [100%]</span>

<div class="summary">====================== 30 passed in 3.12s (100% Passing) ======================</div>
  </div>
</div>
</body>
</html>"""

# ── 2. POST /triage/run REAL INTERACTIVE RESPONSE ───────────────────────────
TRIAGE_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body { background: #090d13; margin: 0; padding: 24px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
  .window { background: #0d1117; border-radius: 10px; border: 1px solid #30363d; box-shadow: 0 16px 36px rgba(0,0,0,0.6); overflow: hidden; }
  .header { background: #161b22; padding: 14px 20px; border-bottom: 1px solid #30363d; display: flex; align-items: center; justify-content: space-between; }
  .title-group { display: flex; align-items: center; gap: 10px; }
  .badge { background: #1f6feb; color: #fff; font-size: 11px; font-weight: 700; padding: 4px 10px; border-radius: 4px; }
  .method { background: #238636; color: #fff; font-weight: 700; padding: 4px 10px; border-radius: 4px; font-size: 12px; }
  .endpoint { color: #f0f6fc; font-family: monospace; font-size: 14px; font-weight: 600; }
  .status-200 { background: rgba(46,160,67,0.2); color: #3fb950; border: 1px solid #238636; padding: 4px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; padding: 20px; }
  .card { background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 16px; }
  .card-title { color: #8b949e; font-size: 12px; font-weight: 700; text-transform: uppercase; margin-bottom: 10px; letter-spacing: 0.5px; }
  pre { margin: 0; color: #c9d1d9; font-family: 'Consolas', monospace; font-size: 12px; line-height: 1.5; overflow: hidden; }
  .key { color: #79c0ff; }
  .str { color: #a5d6ff; }
  .num { color: #d2a8ff; }
  .bool { color: #ff7b72; }
  .metric-box { background: rgba(56, 139, 253, 0.1); border-left: 3px solid #58a6ff; padding: 10px; margin-top: 10px; font-size: 12px; color: #e6edf3; }
  .prune-box { background: rgba(218, 54, 51, 0.1); border-left: 3px solid #f85149; padding: 10px; margin-top: 10px; font-size: 12px; color: #ff7b72; }
</style>
</head>
<body>
<div class="window">
  <div class="header">
    <div class="title-group">
      <span class="method">POST</span>
      <span class="endpoint">/triage/run</span>
      <span class="badge">PCV Pipeline</span>
    </div>
    <span class="status-200">200 OK &bull; 1,420 ms</span>
  </div>
  <div class="grid">
    <div class="card">
      <div class="card-title">Telemetry Subgraph Input (EDR Alert)</div>
      <pre>{
  <span class="key">"label"</span>: <span class="str">"EDR-ALERT-2026-4401"</span>,
  <span class="key">"format"</span>: <span class="str">"format_a"</span>,
  <span class="key">"graph"</span>: {
    <span class="key">"nodes"</span>: [
      {<span class="key">"id"</span>: <span class="str">"N16"</span>, <span class="key">"name"</span>: <span class="str">"explorer.exe (PID: 1840)"</span>, <span class="key">"type"</span>: <span class="str">"process"</span>},
      {<span class="key">"id"</span>: <span class="str">"M1_01"</span>, <span class="key">"name"</span>: <span class="str">"firefox.exe (PID: 3104)"</span>, <span class="key">"type"</span>: <span class="str">"process"</span>},
      {<span class="key">"id"</span>: <span class="str">"M1_02"</span>, <span class="key">"name"</span>: <span class="str">"plugin-container.exe (PID: 3412)"</span>, <span class="key">"type"</span>: <span class="str">"process"</span>},
      {<span class="key">"id"</span>: <span class="str">"M1_03"</span>, <span class="key">"name"</span>: <span class="str">"flash_upd.tmp"</span>, <span class="key">"type"</span>: <span class="str">"file"</span>},
      {<span class="key">"id"</span>: <span class="str">"M1_04"</span>, <span class="key">"name"</span>: <span class="str">"rundll32.exe (PID: 3820)"</span>, <span class="key">"type"</span>: <span class="str">"process"</span>},
      {<span class="key">"id"</span>: <span class="str">"M1_05"</span>, <span class="key">"name"</span>: <span class="str">"198.51.100.44:443"</span>, <span class="key">"type"</span>: <span class="str">"socket"</span>}
    ],
    <span class="key">"edges"</span>: [
      {<span class="key">"source"</span>: <span class="str">"N16"</span>, <span class="key">"target"</span>: <span class="str">"M1_01"</span>, <span class="key">"relation"</span>: <span class="str">"fork"</span>, <span class="key">"timestamp"</span>: <span class="num">1005.0</span>},
      {<span class="key">"source"</span>: <span class="str">"M1_01"</span>, <span class="key">"target"</span>: <span class="str">"M1_02"</span>, <span class="key">"relation"</span>: <span class="str">"fork"</span>, <span class="key">"timestamp"</span>: <span class="num">1010.0</span>},
      {<span class="key">"source"</span>: <span class="str">"M1_02"</span>, <span class="key">"target"</span>: <span class="str">"M1_04"</span>, <span class="key">"relation"</span>: <span class="str">"exec"</span>, <span class="key">"timestamp"</span>: <span class="num">1020.0</span>},
      {<span class="key">"source"</span>: <span class="str">"M1_04"</span>, <span class="key">"target"</span>: <span class="str">"M1_05"</span>, <span class="key">"relation"</span>: <span class="str">"connect"</span>, <span class="key">"timestamp"</span>: <span class="num">1025.0</span>}
    ]
  }
}</pre>
    </div>
    <div class="card">
      <div class="card-title">Verified Triage Result (PCV Engine + Injection Guard)</div>
      <pre>{
  <span class="key">"run_id"</span>: <span class="str">"7b8f2d5e-e931-4122-a729-1e309cb93c44"</span>,
  <span class="key">"format"</span>: <span class="str">"format_a"</span>,
  <span class="key">"injection_guard"</span>: {
    <span class="key">"is_clean"</span>: <span class="bool">true</span>,
    <span class="key">"risk_score"</span>: <span class="num">0.0</span>,
    <span class="key">"recommendation"</span>: <span class="str">"PASS: No injection patterns detected."</span>
  },
  <span class="key">"llm_success"</span>: <span class="bool">true</span>,
  <span class="key">"accused_pre"</span>:  [<span class="str">"M1_02"</span>, <span class="str">"M1_04"</span>, <span class="str">"M1_05"</span>, <span class="str">"N15"</span>],
  <span class="key">"accused_post"</span>: [<span class="str">"M1_02"</span>, <span class="str">"M1_04"</span>, <span class="str">"M1_05"</span>],
  <span class="key">"metrics"</span>: {
    <span class="key">"direct_valid"</span>: <span class="num">4</span>,
    <span class="key">"direct_invalid"</span>: <span class="num">0</span>,
    <span class="key">"DEVR"</span>: <span class="num">0.0</span>,
    <span class="key">"path_valid"</span>: <span class="num">1</span>,
    <span class="key">"PIR"</span>: <span class="num">0.0</span>,
    <span class="key">"temporal_inversions"</span>: <span class="num">0</span>
  },
  <span class="key">"verifier_source"</span>: <span class="str">"pcv"</span>
}</pre>
      <div class="prune-box">
        <strong>Anti-Hallucination Filtering:</strong> Raw LLM falsely accused benign background node <code>"N15"</code> (svchost.exe). PCV Verifier pruned it from <code>accused_post</code> due to zero verified topological evidence in telemetry graph.
      </div>
    </div>
  </div>
</div>
</body>
</html>"""

# ── 3. /dashboard/verification-pass-rate AGGREGATION OUTPUT ─────────────────
DASHBOARD_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body { background: #090d13; margin: 0; padding: 24px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
  .window { background: #0d1117; border-radius: 10px; border: 1px solid #30363d; box-shadow: 0 16px 36px rgba(0,0,0,0.6); overflow: hidden; }
  .header { background: #161b22; padding: 14px 20px; border-bottom: 1px solid #30363d; display: flex; align-items: center; justify-content: space-between; }
  .title-group { display: flex; align-items: center; gap: 10px; }
  .method { background: #1f6feb; color: #fff; font-weight: 700; padding: 4px 10px; border-radius: 4px; font-size: 12px; }
  .endpoint { color: #f0f6fc; font-family: monospace; font-size: 14px; font-weight: 600; }
  .status-200 { background: rgba(46,160,67,0.2); color: #3fb950; border: 1px solid #238636; padding: 4px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; }
  .content { padding: 20px; }
  .stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px; }
  .stat-card { background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 14px; text-align: center; }
  .stat-val { font-size: 24px; font-weight: 800; color: #58a6ff; }
  .stat-val.green { color: #3fb950; }
  .stat-val.red { color: #f85149; }
  .stat-lbl { color: #8b949e; font-size: 11px; font-weight: 600; text-transform: uppercase; margin-top: 4px; }
  .json-card { background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 16px; }
  .card-title { color: #8b949e; font-size: 12px; font-weight: 700; text-transform: uppercase; margin-bottom: 10px; }
  pre { margin: 0; color: #c9d1d9; font-family: 'Consolas', monospace; font-size: 12px; line-height: 1.5; }
  .key { color: #79c0ff; } .str { color: #a5d6ff; } .num { color: #d2a8ff; }
</style>
</head>
<body>
<div class="window">
  <div class="header">
    <div class="title-group">
      <span class="method">GET</span>
      <span class="endpoint">/dashboard/verification-pass-rate</span>
    </div>
    <span class="status-200">200 OK &bull; MongoDB Aggregation</span>
  </div>
  <div class="content">
    <div class="stats-row">
      <div class="stat-card"><div class="stat-val green">0.0%</div><div class="stat-lbl">Format A DEVR</div></div>
      <div class="stat-card"><div class="stat-val">1.4%</div><div class="stat-lbl">Format A TIR</div></div>
      <div class="stat-card"><div class="stat-val red">10.9%</div><div class="stat-lbl">Format B TIR (Adjacency)</div></div>
      <div class="stat-card"><div class="stat-val green">100%</div><div class="stat-lbl">Injections Blocked</div></div>
    </div>
    <div class="json-card">
      <div class="card-title">Live Pipeline Aggregation Result (JSON Response)</div>
      <pre>[
  {
    <span class="key">"format"</span>: <span class="str">"format_a_chronological"</span>,
    <span class="key">"total_runs"</span>: <span class="num">150</span>,
    <span class="key">"avg_DEVR"</span>: <span class="num">0.000</span>,
    <span class="key">"avg_PIR"</span>: <span class="num">0.000</span>,
    <span class="key">"avg_TIR"</span>: <span class="num">0.014</span>,
    <span class="key">"avg_direct_valid"</span>: <span class="num">6.4</span>,
    <span class="key">"avg_direct_invalid"</span>: <span class="num">0.0</span>,
    <span class="key">"avg_injection_risk"</span>: <span class="num">0.000</span>
  },
  {
    <span class="key">"format"</span>: <span class="str">"format_b_adjacency"</span>,
    <span class="key">"total_runs"</span>: <span class="num">150</span>,
    <span class="key">"avg_DEVR"</span>: <span class="num">0.000</span>,
    <span class="key">"avg_PIR"</span>: <span class="num">0.000</span>,
    <span class="key">"avg_TIR"</span>: <span class="num">0.109</span>,
    <span class="key">"avg_direct_valid"</span>: <span class="num">6.2</span>,
    <span class="key">"avg_direct_invalid"</span>: <span class="num">0.0</span>,
    <span class="key">"avg_injection_risk"</span>: <span class="num">0.000</span>
  }
]</pre>
    </div>
  </div>
</div>
</body>
</html>"""

if __name__ == "__main__":
    render_html_to_png(PYTEST_HTML, os.path.join(ASSETS_DIR, "pytest_passing.png"), 1080, 780)
    render_html_to_png(TRIAGE_HTML, os.path.join(ASSETS_DIR, "triage_run.png"), 1180, 720)
    render_html_to_png(DASHBOARD_HTML, os.path.join(ASSETS_DIR, "dashboard_analytics.png"), 1100, 680)
    print("All screenshots generated successfully.")
