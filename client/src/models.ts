export type Attributes = Record<string, boolean | number | string>;

export interface CalendarEvent {
  name: string;
  turn: number;
}

export interface Planner {
  calendar: Array<CalendarEvent>;
  notes: Array<string>;
}

export interface Item {
  type: 'item';
  name: string;
  description: string;
  attributes: Attributes;
}

export interface Character {
  type: 'character';
  name: string;
  backstory: string;
  description: string;
  items: Array<Item>;
  attributes: Attributes;
  planner: Planner;
}

export interface Portal {
  type: 'portal';
  name: string;
  description: string;
  destination: string;
}

export interface Room {
  type: 'room';
  name: string;
  description: string;
  characters: Array<Character>;
  items: Array<Item>;
  portals: Array<Portal>;
  attributes: Attributes;
}

export interface World {
  type: 'world';
  name: string;
  order: Array<string>;
  rooms: Array<Room>;
  theme: string;
  turn: number;
}

//

export interface StringParameter {
  type: 'string';
  default?: string;
  enum?: Array<string>;
}

export interface NumberParameter {
  type: 'number';
  default?: string;
  enum?: Array<string>;
}

export type Parameter = NumberParameter | StringParameter;

export interface Action {
  type: 'function';
  function: {
    name: string;
    description: string;
    parameters: {
      type: 'object';
      properties: Record<string, Parameter>;
    };
  };
}

// TODO: copy event types from server
export interface GameEvent {
  type: string;
}

export interface PromptEvent {
  type: 'prompt';
  prompt: string;
  actions: Array<Action>;
  character: Character;
  room: Room;
}
