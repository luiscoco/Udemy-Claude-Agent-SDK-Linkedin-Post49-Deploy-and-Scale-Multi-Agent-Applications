"""Lesson-specific workflow. Read this file before the execution adapter."""
from __future__ import annotations
import asyncio
import json
from pathlib import Path
from runtime import atomic_json, contained_path, in_process_tool

async def run(agent, data):
    workers = data['workers']
    if type(workers) is not int or not 1 <= workers <= 3:
        raise ValueError('Use one to three workers')
    semaphore = asyncio.Semaphore(workers)
    async def worker(index, job):
        async with semaphore:
            return await agent.ask('job_' + str(index), 'Complete the assigned short summary.', job, 'Completed summary for: ' + job)
    results = await asyncio.gather(*(worker(i, job) for i, job in enumerate(data['jobs'])))
    config = {'workers': workers, 'requests': len(results), 'credentials': 'environment only', 'hosted': False}
    atomic_json(agent.output / 'deployment_config.json', config)
    return {'results': results, 'configuration': config}
