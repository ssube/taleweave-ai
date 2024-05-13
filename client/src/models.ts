export interface Item {
  type: 'item';
  name: string;
  description: string;
}

export interface Actor {
  type: 'actor';
  name: string;
  backstory: string;
  description: string;
  items: Array<Item>;
}

export interface Room {
  type: 'room';
  name: string;
  description: string;
  portals: Record<string, string>;
  actors: Array<Actor>;
  items: Array<Item>;
}

export interface World {
  type: 'world';
  name: string;
  order: Array<string>;
  rooms: Array<Room>;
  theme: string;
}

// TODO: copy event types from server
export interface GameEvent {
  type: string;
}
