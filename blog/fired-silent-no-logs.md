---
title: "Fired, silent, no_logs: why two states aren't enough"
date: 2026-09-10
description: A rule that didn't alert means one of two very different things, and collapsing them hides the only finding an engineer can act on.
author: MayaTrail
tags: [detection-engineering, aws, cloudtrail]
draft: true
---

Run an attack emulation, then ask the obvious question: did the detections catch it?

Most tooling answers with a number. Eleven rules armed, eight fired, coverage 73%. It looks like an answer. It isn't, because the three rules that didn't fire are not the same kind of problem — and the number has already thrown away the difference.

## Two failures wearing the same mask

A rule that didn't alert failed in one of two ways.

Either **events for that rule's log source arrived and none of them matched**. The rule ran. It saw traffic. It decided nothing was wrong. Maybe the attack genuinely didn't perform that action, or maybe the rule needs tuning — a field name that drifted, a threshold set too high, a filter that's too generous.

Or **no events from that source reached the log archive at all**. The rule never ran. It was never given the chance. Nothing is wrong with the detection logic, and no amount of tuning will help, because the problem is upstream in the log pipeline.

These need opposite responses. The first is a detection-engineering task. The second is a plumbing task, and often a much more urgent one, because *every* rule depending on that source is equally blind and you haven't noticed.

Report both as "missed" and you've told an engineer to go tune a rule that was never evaluated.

## Three states

So we don't report two states. We report three:

| state | meaning | where the fix is |
|---|---|---|
| `fired` | the rule matched events this run produced | nowhere — it worked |
| `silent` | events arrived for this source, none matched | the rule |
| `no_logs` | no events from this source reached the archive | the pipeline |

The rule that governs this in our codebase is short enough to state plainly: evidence is attached to a rule that fired, and to nothing else. Six empty evidence blocks would bury the one that matters.

## Why this shows up more in the cloud

On a host, a missing log source is usually loud. The agent is down, the box is unreachable, something pages someone.

In AWS the failure is quiet and specific. CloudTrail management events are on by default; **data events are not**. So `s3:ListBuckets` is logged and `s3:GetObject` is not, unless someone turned data events on for that bucket. An attacker enumerating your buckets is visible. The same attacker reading 128 objects out of them is not.

That's not a rule problem. Every S3 exfiltration rule you own could be perfectly written and every one of them would stay quiet, because the events never existed. A two-state report calls that a detection gap. It's a logging gap, and it's the single highest-leverage thing on the list.

The same shape recurs across the control plane: IMDS credential requests aren't logged at all, so the theft is invisible and only the *replay* of the stolen credentials shows up in CloudTrail — under an assumed-role session named after the instance, from an IP outside your VPC. If you're not collecting the right events, the best rule in the world has nothing to read.

## What to do with it

Sort by state, not by count.

Start with `no_logs`. It is the cheapest fix and the widest blast radius: turning on a log source can move a dozen rules from useless to working in one change, and until you do, you cannot say anything at all about the techniques that depend on it.

Then `silent`. Now you're doing real detection engineering — comparing what the rule expected against the events the run actually produced, and adjusting one or the other.

And treat a coverage percentage with suspicion, including ours. A single number can only be honest if every rule underneath it was actually given a chance to run.

---

*MayaTrail runs documented cloud campaigns inside your own AWS account and reports, per technique, which of your detections fired, which stayed silent, and which never saw a log line.*
