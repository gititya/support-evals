"""Editorial article view of the support-evaluation evidence."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any, Mapping


def render_article_html(payload: Mapping[str, Any]) -> str:
    """Render an insight-led article for customer-support leaders."""

    run_date = _esc(payload.get("generated_at", "29 August 2026"))
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="What customer-support QA becomes when the agent is AI.">
  <title>QA in Customer Support, 2026</title>
  <style>
    :root {{ --paper:#f7f4ee; --ink:#25221e; --muted:#6e675f; --line:#d9d1c5; --accent:#8a4d32; --soft:#eee7dc; }}
    * {{ box-sizing:border-box; }}
    html {{ scroll-behavior:smooth; }}
    body {{ margin:0; background:var(--paper); color:var(--ink); font:18px/1.72 Georgia,"Times New Roman",serif; }}
    a {{ color:var(--accent); text-underline-offset:3px; }}
    header, article, footer {{ width:min(100% - 40px, 760px); margin-inline:auto; }}
    header {{ padding:72px 0 36px; }}
    article {{ padding-bottom:64px; }}
    h1,h2,h3 {{ line-height:1.14; letter-spacing:-.02em; }}
    h1 {{ margin:10px 0 22px; font-size:clamp(2.5rem,7vw,4.8rem); font-weight:500; }}
    h2 {{ margin:72px 0 20px; font-size:clamp(1.8rem,4vw,2.6rem); font-weight:500; }}
    h3 {{ margin:34px 0 10px; font-size:1.25rem; }}
    p {{ margin:0 0 1.2em; }}
    .eyebrow,.meta,.label,code {{ font-family:ui-monospace,SFMono-Regular,Menlo,monospace; }}
    .eyebrow,.label {{ color:var(--accent); font-size:.72rem; font-weight:700; letter-spacing:.13em; text-transform:uppercase; }}
    .standfirst {{ color:var(--muted); font-size:1.25rem; line-height:1.55; }}
    .meta {{ color:var(--muted); font-size:.78rem; }}
    .contents {{ margin:32px 0 0; padding:20px 22px; border-block:1px solid var(--line); font-family:system-ui,-apple-system,sans-serif; font-size:.9rem; }}
    .contents ol {{ margin:10px 0 0; padding-left:1.25rem; columns:2; column-gap:28px; }}
    .contents li {{ margin:6px 0; break-inside:avoid; }}
    .lede {{ font-size:1.17rem; }}
    blockquote {{ margin:40px 0; padding:2px 0 2px 24px; border-left:3px solid var(--accent); font-size:1.35rem; line-height:1.48; }}
    .case,.note,.honest {{ margin:32px 0; padding:24px; border:1px solid var(--line); background:#fffaf2; }}
    .case h3,.note h3,.honest h3 {{ margin:5px 0 12px; }}
    .journey {{ display:grid; grid-template-columns:repeat(5,1fr); gap:8px; margin:32px -80px; font-family:system-ui,-apple-system,sans-serif; }}
    .journey div {{ min-height:112px; padding:15px; border-top:3px solid var(--accent); background:var(--soft); }}
    .journey strong {{ display:block; margin-bottom:6px; font-size:.95rem; }}
    .journey span {{ display:block; color:var(--muted); font-size:.78rem; line-height:1.4; }}
    .plain-list {{ padding-left:1.25rem; }}
    .plain-list li {{ margin:0 0 18px; padding-left:5px; }}
    .insights {{ margin:34px 0; border-top:1px solid var(--line); }}
    .insights section {{ padding:24px 0 20px; border-bottom:1px solid var(--line); }}
    .insights h3 {{ margin:4px 0 10px; }}
    .term {{ font-family:system-ui,-apple-system,sans-serif; font-weight:700; }}
    code {{ padding:.12em .32em; border:1px solid var(--line); background:var(--soft); font-size:.82em; }}
    pre {{ overflow:auto; padding:18px; background:#26221d; color:#f7f0e6; font:13px/1.55 ui-monospace,SFMono-Regular,Menlo,monospace; }}
    details {{ margin:26px 0; border-block:1px solid var(--line); padding:16px 0; }}
    summary {{ cursor:pointer; font-family:system-ui,-apple-system,sans-serif; font-weight:700; }}
    .sources {{ color:var(--muted); font-family:system-ui,-apple-system,sans-serif; font-size:.82rem; }}
    footer {{ padding:30px 0 60px; border-top:1px solid var(--line); color:var(--muted); font-family:system-ui,-apple-system,sans-serif; font-size:.82rem; }}
    @media (max-width:900px) {{ .journey {{ margin-inline:0; grid-template-columns:1fr; }} .journey div {{ min-height:auto; }} }}
    @media (max-width:600px) {{ header {{ padding-top:40px; }} .contents ol {{ columns:1; }} body {{ font-size:17px; }} .case,.note,.honest {{ padding:19px; }} }}
    @media print {{ body {{ background:white; }} .contents {{ display:none; }} a {{ color:inherit; }} .journey {{ margin-inline:0; }} }}
  </style>
</head>
<body>
<header>
  <p class="eyebrow">Working article · customer-support evaluation</p>
  <h1>QA in Customer Support, 2026</h1>
  <p class="standfirst">The old tension in support QA was the checklist versus the customer experience. AI has not removed that tension. It has made the cost of weak QA much higher.</p>
  <p class="meta">Based on support-evaluation work reviewed on {run_date} · no production customer claims</p>
  <nav class="contents" aria-label="Article contents">
    <span class="label">In this article</span>
    <ol>
      <li><a href="#old-problem">The old QA problem</a></li>
      <li><a href="#answer">Why grading the answer fails</a></li>
      <li><a href="#journey">What QA should follow</a></li>
      <li><a href="#built">What I built</a></li>
      <li><a href="#learned">What changed my mind</a></li>
      <li><a href="#voice">What voice changes</a></li>
      <li><a href="#method">The method I now use</a></li>
      <li><a href="#limits">The missing feedback loop</a></li>
    </ol>
  </nav>
</header>

<article>
  <section id="old-problem">
    <p class="lede">When I was taking customer calls as a support rep in 2011, I was often anxious about the Quality Auditing team.</p>
    <p>If I did not follow a certain script, process, or even use the expected words, I could lose points. I often found myself near the bottom of the weekly QA scores. It did not bother me much then because I knew a checklist could not fully measure the customer experience I delivered.</p>
    <p>When I started leading teams a couple of years later, the question changed: if a checklist can miss good support, what should QA measure?</p>
    <p>That question matters again in 2026. This time, the support rep may be an AI system that can repeat the same behaviour across thousands of conversations. A weak scorecard does not just misjudge one rep. It can approve a bad support habit and help it spread.</p>
  </section>

  <section id="answer">
    <h2>The first mistake is grading the answer</h2>
    <p>A support answer can sound clear, polite, and useful while the support itself is poor.</p>
    <p>Imagine a customer whose home-security camera stopped working after the Wi-Fi password changed. They have already restarted it. The agent replies with a neat set of restart instructions.</p>
    <p>Nothing in that answer looks offensive or incoherent. A language-quality reviewer may pass it. A customer-support reviewer should not. The agent ignored what the customer had already tried, failed to investigate the network change, and added effort without moving the case forward.</p>

    <div class="case">
      <p class="label">The difference</p>
      <h3>Answer quality asks, “Was this a good reply?”</h3>
      <p>Support quality asks: Did the agent understand the case? Did it use the evidence already available? Did it choose the right next step? Did anything improve for the customer?</p>
    </div>

    <blockquote>A reply is evidence of communication. It is not evidence of resolution.</blockquote>
  </section>

  <section id="journey">
    <h2>QA should follow the customer journey</h2>
    <p>I now treat the complete support journey as the thing being reviewed. The journey starts with the customer's need. It ends with a verified fix, an honest explanation of why the system cannot help, or a handoff that lets another person continue the work.</p>

    <div class="journey" role="img" aria-label="A support journey moves through understanding, investigation, guidance, action, and closure">
      <div><strong>Understand</strong><span>What does the customer need, and which details must stay exact?</span></div>
      <div><strong>Investigate</strong><span>What is known, what is only a guess, and what should be checked next?</span></div>
      <div><strong>Guide</strong><span>Is the advice supported, safe, and suited to this customer's case?</span></div>
      <div><strong>Act</strong><span>Did the promised action happen, and did the product state change?</span></div>
      <div><strong>Close</strong><span>Is the issue resolved, safely blocked, or handed over with enough context?</span></div>
    </div>

    <p>This changes the purpose of QA. The job is no longer to reward the presence of approved words. The job is to check the quality of the decisions that moved the customer from one stage to the next.</p>
  </section>

  <section id="built">
    <h2>What I built</h2>
    <p>Across my support projects, I had built separate ways to test understanding, investigation, safety, actions, handoffs, transcripts, screens, and voice conversations. The code differed, but the support question underneath was often the same: <em>did the system have enough evidence to do what it did?</em></p>
    <p>I extracted those ideas into one reusable QA system. It is not another support bot. It sits beside a support product and reviews saved or simulated journeys.</p>

    <ol class="plain-list">
      <li><strong>A case describes the customer situation.</strong> It records what the customer wants, what the product knows at the start, and what a safe ending looks like.</li>
      <li><strong>A small connector translates the product's history.</strong> Chat messages, actions, handoffs, screen guidance, and voice events become one readable journey.</li>
      <li><strong>The QA system reviews the journey.</strong> It checks whether the system understood, investigated, acted, and closed the case safely.</li>
      <li><strong>Serious failures block the result.</strong> A warm tone cannot cancel an invented fact, an unsafe promise, or an action that never happened.</li>
      <li><strong>The full evidence stays available.</strong> A support leader can read the conclusion. A builder can inspect the exact journey when something fails.</li>
    </ol>

    <div class="note">
      <p class="label">In plain English</p>
      <h3>The “harness” is just the repeatable QA process around the support product</h3>
      <p>It provides the practice case, runs the case through the product, reviews what happened, and saves enough detail to explain the decision. Each product needs a small connector, but the core support principles can be reused.</p>
    </div>

    <details>
      <summary>For a builder: how a local journey is run</summary>
      <pre>python3 -m support_evals run --adapter reference-shop \
  --output /tmp/support-evals-shop.json \
  --html /tmp/support-evals-shop.html</pre>
      <p>The included shop is fictional. The command does not contact customers or change a live support system.</p>
    </details>
  </section>

  <section id="learned">
    <h2>What changed my mind</h2>
    <p>The experiments mattered when they contradicted an easy assumption. These are the conclusions I would carry into a real support operation.</p>

    <div class="insights">
      <section>
        <p class="label">Synthetic customers</p>
        <h3>Practice customers can make a weak system look good</h3>
        <p>When customer messages were clean and written like support categories, the system appeared to understand them. When the wording became more natural—mixed symptoms, incomplete context, emotion, and customer guesses—the weakness became obvious.</p>
        <p>Synthetic cases are still useful. They make tests safe and repeatable. But they are good for checking known behaviour, not for proving that the system understands how real customers speak.</p>
      </section>

      <section>
        <p class="label">Investigation</p>
        <h3>Being right too early is still bad support</h3>
        <p>An agent can guess the eventual cause from the first symptom and later appear correct. That does not make the investigation sound. A different customer with the same symptom may have a different cause and receive the wrong fix.</p>
        <p>I therefore started checking what the agent knew at each point, which explanations it had ruled out, and why the next step made sense. This grades the quality of the investigation, not the luck of the final answer.</p>
      </section>

      <section>
        <p class="label">AI reviewing AI</p>
        <h3>The QA reviewer becomes another source of support risk</h3>
        <p>An AI reviewer can miss an unsafe promise. It can also reject a good answer because it quietly changes the question it is grading. A confident verdict does not make the reviewer correct.</p>
        <p>That changed the role I give AI review. It can help with judgment calls such as whether an explanation is grounded or a handoff is useful. It should not decide facts that the system can check directly, such as whether an action ran or an account state changed.</p>
      </section>

      <section>
        <p class="label">Resolution</p>
        <h3>“You're all set” is not a customer outcome</h3>
        <p>Support systems often grade the conversation because that is the easiest record to read. But a promise inside the conversation is not the same as a completed action.</p>
        <p>If the agent says it changed an address, restored access, or created a ticket, QA should check the product record. The final state—not the sentence—is the proof.</p>
      </section>

      <section>
        <p class="label">Handoff</p>
        <h3>A handoff is part of the resolution, not an escape from it</h3>
        <p>Passing a case to a human does not make the AI successful. The next person needs the customer's goal, the relevant evidence, what has already been tried, what remains unknown, and a clear next action.</p>
        <p>If the customer has to start again, the handoff failed even if the routing decision was correct.</p>
      </section>
    </div>
  </section>

  <section id="voice">
    <h2>Voice changes what QA can see</h2>
    <p>A transcript removes much of the experience of a call. It does not show how long the customer waited, whether the agent spoke over them, whether they could interrupt, or how often they had to repeat themselves.</p>
    <p>It can also hide where the failure began. If speech recognition drops the word “not,” the support system may reason correctly from an incorrect record. A text-only review may blame the agent's reasoning when the real failure happened while listening.</p>
    <p>My voice work therefore treats hearing, timing, interruption, silence, repeated information, support action, and final outcome as separate parts of the same call. A natural-sounding voice cannot compensate for a wrong action. A correct action does not excuse an interaction that traps the caller in silence.</p>
    <p>The current system reviews saved call traces. It does not yet judge real phone audio, voice naturalness, telephone networks, or live caller behaviour. Those are not small missing checks. They are a separate layer of proof.</p>
  </section>

  <section id="method">
    <h2>The method I now use</h2>
    <div class="honest">
      <p class="label">Evidence-gated journey QA</p>
      <h3>A support decision should not pass QA unless the journey contains the evidence needed to defend it.</h3>
      <p>The method asks four questions: What did the system know when it made the decision? Was that enough? Did the promised action happen? Did the customer reach a safe next state?</p>
    </div>
    <p>I would not claim that I invented a new branch of evaluation. The method combines familiar support QA with agent testing, product-state checks, and stricter rules for risk. Its value is the combination: it reviews the work of support, not only the words produced by the AI.</p>
    <p>This also explains how the framework can support normal customer service and technical support. Policies and product actions change. The need to understand, investigate, act on evidence, verify the outcome, and hand over cleanly does not.</p>
  </section>

  <section id="limits">
    <h2>The missing part is a real feedback loop</h2>
    <p>I do not have a live support product or real customers. That limits what I can learn, but it does not prevent me from building a serious framework.</p>
    <p>Without production access, I can test whether the framework is repeatable, whether it catches known support failures, whether different products can connect to it, and whether it preserves an honest record. I cannot know which problems real customers will create most often, which cases my test set has missed, or whether better eval results lead to better customer outcomes.</p>
    <p>Production use would not simply add more cases. It would correct the framework. Human QA disagreements would expose weak rules. Escalations and complaints would reveal missing scenarios. Customer outcomes would show whether the scores track the experience that matters.</p>
    <p>So the honest claim is not “I built a production-proven QA platform.” It is: <strong>I built a reusable method, tested it against the failure patterns I know, and made its current limits visible.</strong></p>
    <blockquote>Support QA in 2026 should move from policing words to proving decisions.</blockquote>
  </section>

  <section class="sources">
    <h2>Evidence and reading</h2>
    <p><a href="support-portfolio-report-2026-08-29.html">Detailed evidence appendix</a> · <a href="support-portfolio-run-2026-08-29.json">Machine-readable evidence</a> · <a href="https://manthanguptaa.in/posts/evaluating_voice_agents/">Manthan Gupta: How to Evaluate Voice Agents</a></p>
    <p>The opening adapts my draft “QA in Customer Support 2026.” The detailed test results stay in the appendix so the article can focus on the support lessons they produced.</p>
  </section>
</article>

<footer>
  <p>Working article for review. No production customer or business-outcome claims. Evidence reviewed {run_date}.</p>
</footer>
</body>
</html>
"""


def write_article_html(path: str | Path, payload: Mapping[str, Any]) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(render_article_html(payload), encoding="utf-8")
    return destination


def _esc(value: Any) -> str:
    return html.escape(str(value), quote=True)
