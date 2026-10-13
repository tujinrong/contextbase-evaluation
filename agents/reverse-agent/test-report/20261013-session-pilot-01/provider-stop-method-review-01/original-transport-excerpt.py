completed = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command',
                            '[Console]::OutputEncoding=[Text.UTF8Encoding]::new();' + PROCESS_SCRIPT],
                           input=json.dumps(request), capture_output=True, text=True,
                           encoding='utf-8', timeout=60, check=True)
exclusive_json(target / 'process-actions.json', json.loads(completed.stdout))
after = capture(job, target / 'after')
exclusive_json(target / 'inventory-after.json', after)
exclusive_json(target / 'result.json', {
    'finishedAt': datetime.now(timezone.utc).isoformat(),
    'stopRequested': args.stop_at_deadline, 'beforeFiles': len(before), 'afterFiles': len(after),
    'completeInferenceClaimed': False, 'completedScore': None,
    'captureErrors': sum('captureError' in item for item in before + after),
    'limitations': ['Live files may change during pre-stop copy; stableDuringCopy is explicit',
                     'Missing provider result/answer remains incomplete',
                     'Review/grading agents are controlled separately by the parent agent']})
