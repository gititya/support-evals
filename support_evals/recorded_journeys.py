"""Review captured product responses without generating missing events or outcomes."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from .contracts import CheckResult, EvaluatorResult, ResultStatus


def review_voice(run, source):
    checks = []
    if run.get('passed') is False:
        checks.append(CheckResult('recorded_execution', ResultStatus.FAIL,
            'The original driver recorded this attempted journey as unsuccessful.',
            'An incomplete attempt remains visible; this is not a new judgment of the handoff decision.',
            (source + '/passed',)))
    responses = run.get('responses', [])
    prior_session = None
    for index, response in enumerate(responses):
        pointer = f'{source}/responses/{index}'
        body = response.get('body', {})
        status = body.get('status')
        session = body.get('session_id')
        if response.get('http_status') != 200:
            checks.append(CheckResult(f'response.{index}', ResultStatus.ERROR,
                'The recorded request did not complete successfully.',
                'This part of the support journey cannot be counted as successful.',
                (pointer,), error=str(response.get('http_status'))))
            continue
        if prior_session and session != prior_session:
            checks.append(CheckResult(f'session.{index}', ResultStatus.FAIL,
                'The case changed during the recorded journey.',
                'The customer investigation may have been lost.', (pointer,)))
        prior_session = session
        guidance = body.get('guidance') or {}
        if status == 'guiding' and guidance.get('caption'):
            matches = body.get('message') == guidance['caption']
            checks.append(CheckResult(f'current_instruction.{index}',
                ResultStatus.PASS if matches else ResultStatus.FAIL,
                'The shared message agrees with the current guidance.' if matches else
                'The shared message disagrees with the current guidance.',
                'An app needs consistent words and pointing for the same step.',
                (pointer + '/body/message', pointer + '/body/guidance/caption'),
                expected=guidance['caption'], observed=body.get('message')))
        if status == 'resolved':
            history = body.get('history', [])
            confirmations = [(i, e) for i, e in enumerate(history)
                             if e.get('kind') == 'customer_confirmation']
            last = confirmations[-1] if confirmations else None
            observed_before = bool(last and any(e.get('kind') == 'observed_result'
                                   for e in history[:last[0]]))
            valid = bool(last and last[1].get('answer') == 'yes' and
                         body.get('confirmation') == 'yes' and observed_before)
            checks.append(CheckResult(f'confirmed_outcome.{index}',
                ResultStatus.PASS if valid else ResultStatus.FAIL,
                'Resolution follows observed progress and a recorded yes.' if valid else
                'Resolution lacks observed progress followed by a recorded yes.',
                'Showing instructions alone must not close the case.',
                (pointer + '/body/history', pointer + '/body/confirmation')))
        if body.get('confirmation') in {'no', 'unsure'}:
            checks.append(CheckResult(f'unresolved_outcome.{index}',
                ResultStatus.FAIL if status == 'resolved' else ResultStatus.PASS,
                'The recorded negative or uncertain answer must not count as resolution.',
                'The customer retains a route to more help.', (pointer,)))
        if status == 'handoff':
            delivered = (body.get('delivery') or {}).get('status') == 'delivered'
            checks.append(CheckResult(f'receiver.{index}',
                ResultStatus.ABSTENTION,
                'Delivery is reported, but an independent receiving receipt is not checked here.' if delivered else
                'External receipt is not established by this record.',
                'A local case number alone does not prove a person received the investigation.',
                (pointer + '/body/delivery',)))
    if not responses:
        checks.append(CheckResult('missing_responses', ResultStatus.ABSTENTION,
            'No response sequence was captured.', 'The journey cannot be assessed.', (source,)))
    checks.append(CheckResult('owner_judgment', ResultStatus.ABSTENTION,
        'No separate owner assessment is supplied for this review.',
        'Mechanical checks do not establish that the support was useful.', (source,)))
    return EvaluatorResult('recorded-voice', tuple(checks)).to_dict()


def review_copilot(record, source):
    history = record.get('history', [])
    checks = []
    advice = [i for i, e in enumerate(history) if e.get('type') == 'private_advice']
    reads = [i for i, e in enumerate(history) if e.get('type') == 'read']
    progress = record.get('case_progress', {})
    checks.append(CheckResult('record_available',
        ResultStatus.PASS if history and advice else ResultStatus.ABSTENTION,
        'Ordered rep reports, source reads and private advice are available.' if history and advice else
        'The recorded conversation is incomplete.',
        'The reviewer can inspect what was known when advice was offered.', (source + '/history',),
        observed={'advice_indexes': advice, 'read_indexes': reads, 'final_progress': progress}))
    checks.append(CheckResult('support_judgment', ResultStatus.ABSTENTION,
        'Whether the questions, explanation and proposed transfer were useful requires review.',
        'Source-read order alone cannot prove the advice follows from the evidence.',
        tuple(f'{source}/history/{i}' for i in advice)))
    checks.append(CheckResult('terminal_outcome', ResultStatus.ABSTENTION,
        'This file is not an independently verified closure or receiving-team receipt.',
        'Advice to close or escalate is distinct from the rep doing so.', (source + '/case_progress',)))
    return EvaluatorResult('recorded-copilot', tuple(checks)).to_dict()


def review_file(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    record = json.loads(raw)
    source = {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest()}
    if isinstance(record.get('runs'), list):
        runs = [{'scenario': run.get('journey'), 'source_pointer': f'/runs/{i}',
                 'recorded_driver_pass': run.get('passed'),
                 'assessment': review_voice(run, f'{path}#/runs/{i}')}
                for i, run in enumerate(record['runs'])]
    elif record.get('kind') == 'interactive_fictional_walkthrough':
        runs = [{'scenario': record.get('case_id'), 'source_pointer': '/',
                 'assessment': review_copilot(record, f'{path}#')}]
    else:
        raise ValueError(f'Unsupported captured record: {path}')
    return {'source': source, 'runs': runs}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('records', nargs='+')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    results = []
    for path in args.records:
        try:
            results.append(review_file(path))
        except (ValueError, OSError, TypeError) as exc:
            results.append({'source': {'path': str(Path(path).resolve())}, 'error': str(exc)})
    Path(args.output).write_text(json.dumps({
        'method': 'Retrospective review of recorded development runs; no model calls or invented events.',
        'limits': 'No independent support-quality verdict or customer-success rate. Repeated runs are not unique scenarios.',
        'owner_review': 'pending', 'records': results,
    }, indent=2) + '\n')


if __name__ == '__main__':
    main()
