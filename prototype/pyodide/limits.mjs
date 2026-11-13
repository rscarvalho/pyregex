export const LIMITS = Object.freeze({ cases: 32, pattern: 1024, input: 8192,
  total: 32768, output: 1048576, evaluationMs: 2000, startupMs: 30000 });

export function validateCases(cases) {
  if (!Array.isArray(cases) || !cases.length || cases.length > LIMITS.cases) {
    throw new Error('Expected 1..32 fixture-style cases');
  }
  let total = 0;
  for (const row of cases) {
    if (!row || typeof row !== 'object' ||
        Object.keys(row).some(key => !['id', 'operation', 'flags', 'pattern', 'input', 'expected', 'error'].includes(key)) ||
        typeof row.id !== 'string' || row.id.length > 128 ||
        !['match', 'search', 'findall'].includes(row.operation) ||
        !Array.isArray(row.flags) || row.flags.length > 6 ||
        row.flags.some(flag => !['IGNORECASE', 'LOCALE', 'MULTILINE', 'DOTALL', 'UNICODE', 'VERBOSE'].includes(flag)) ||
        typeof row.pattern !== 'string' || row.pattern.length > LIMITS.pattern ||
        typeof row.input !== 'string' || row.input.length > LIMITS.input) {
      throw new Error('Invalid or oversized fixture-style case');
    }
    total += row.id.length + row.pattern.length + row.input.length;
  }
  if (total > LIMITS.total) throw new Error('Batch input limit exceeded');
  // Strip fixture expectations/other non-execution data before cloning to worker.
  return cases.map(({ id, operation, flags, pattern, input }) =>
    ({ id, operation, flags: [...flags], pattern, input }));
}
