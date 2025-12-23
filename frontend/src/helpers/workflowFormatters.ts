/**
 * Helper functions for WorkflowDialog component
 * Formats tool input/output for display
 */

/**
 * Format tool input for display with proper markdown
 */
export function formatInput(input: unknown): string {
  if (!input) return 'No input';

  let parsedInput: unknown = input;

  if (typeof parsedInput === 'string') {
    try {
      parsedInput = JSON.parse(parsedInput);
    } catch {
      return parsedInput as string;
    }
  }

  if (typeof parsedInput === 'object' && parsedInput !== null) {
    const parts: string[] = [];

    Object.entries(parsedInput as Record<string, unknown>).forEach(([key, value]) => {
      const formattedKey = key
        .replace(/_/g, ' ')
        .replace(/\b\w/g, (l: string) => l.toUpperCase());

      if (typeof value === 'string') {
        if (/\b(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER)\b/i.test(value)) {
          parts.push(`**${formattedKey}:**\n\`\`\`sql\n${value}\n\`\`\``);
        } else {
          parts.push(`**${formattedKey}:** ${value}`);
        }
      } else if (typeof value === 'number' || typeof value === 'boolean') {
        parts.push(`**${formattedKey}:** ${value}`);
      } else {
        parts.push(
          `**${formattedKey}:**\n\`\`\`json\n${JSON.stringify(value, null, 2)}\n\`\`\``
        );
      }
    });

    return parts.join('\n\n');
  }

  return JSON.stringify(parsedInput, null, 2);
}

/**
 * Format tool output for display with truncation
 */
export function formatOutput(output: unknown): string {
  const MAX_LENGTH = 2000;

  if (!output) return 'No output';

  if (typeof output === 'string') {
    let parsedOutput: unknown;
    try {
      parsedOutput = JSON.parse(output);
      const outputStr = JSON.stringify(parsedOutput, null, 2);
      return outputStr.length > MAX_LENGTH
        ? outputStr.substring(0, MAX_LENGTH) + '\n\n... (truncated)'
        : outputStr;
    } catch {
      return output.length > MAX_LENGTH
        ? output.substring(0, MAX_LENGTH) + '\n\n... (truncated)'
        : output;
    }
  }

  const outputStr = JSON.stringify(output, null, 2);
  return outputStr.length > MAX_LENGTH
    ? outputStr.substring(0, MAX_LENGTH) + '\n\n... (truncated)'
    : outputStr;
}
