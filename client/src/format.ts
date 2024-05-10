/* eslint-disable @typescript-eslint/no-explicit-any */

export function formatActionName(name: string) {
  const shortName = name.replace('action_', '');
  return shortName[0].toUpperCase() + shortName.substring(1).toLowerCase();
}

export function formatAction(data: any) {
  const actionName = formatActionName(data.action);
  const actionParameters = data.parameters;

  return `Action: ${actionName} - ${Object.entries(actionParameters).map(([key, value]) => `${key}: ${value}`).join(', ')}`;
}

export function formatInput(data: any) {
  const action = formatAction(data);
  return `Starting turn: ${action}`;
}

export function formatResult(data: any) {
  return `Turn result: ${data.result}`;
}

export function formatWorld(data: any) {
  return `${data.world.theme} - ${data.step}`;
}

export const formatters: Record<string, any> = {
  action: formatInput,
  result: formatResult,
  world: formatWorld,
};
