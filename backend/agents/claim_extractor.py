# Stub for PoC mode
class ClaimExtractorAgent:
    async def run(self, context):
        return type('Result', (), {'output': {'claims': []}})()